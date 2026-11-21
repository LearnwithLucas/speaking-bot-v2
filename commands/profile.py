from __future__ import annotations

# commands/profile.py
#
# /profile: one member's own speaking progress. Private by default (only the
# member sees it), with a Share button that posts the card in
# #your-successes-and-stories. It shows one member, never a ranking.

import datetime as dt
import logging
import time
from typing import Any
from zoneinfo import ZoneInfo

import discord

from config import (
    CAFE_HOUR_DURATION_MIN,
    CAFE_HOUR_VOICE_CHANNEL_ID,
    MILESTONE_ANNOUNCE_CHANNEL_ID,
    MILESTONE_ROLES,
)
from jobs.milestones import MILESTONE_START_KV

log = logging.getLogger("commands.profile")

TZ = ZoneInfo("Europe/Amsterdam")
SHARE_CHANNEL_ID_FALLBACK = 1490320758507962490  # #your-successes-and-stories
CAFE_HOUR_MIN_SECONDS = 3 * 60

ACHIEVEMENT_NAMES = {
    "first_voice_attempt": ("First time in voice", "Eerste keer in voice"),
    "joined_again": ("Came back for more", "Kwam terug voor meer"),
    "came_back_after_break": ("Back after a break", "Terug na een pauze"),
    "spoke_with_someone_new": ("Spoke with someone new", "Met iemand nieuws gesproken"),
    "milestone_1h": ("1 hour of speaking", "1 uur gesproken"),
    "milestone_3h": ("3 hours of speaking", "3 uur gesproken"),
    "milestone_10h": ("10 hours of speaking", "10 uur gesproken"),
}

LABELS = {
    "title": ("{name}'s speaking profile", "Spreekprofiel van {name}"),
    "total": ("Speaking time", "Spreektijd"),
    "since": ("since {date}", "sinds {date}"),
    "week": ("This week", "Deze week"),
    "milestone": ("Milestone", "Mijlpaal"),
    "people": ("People spoken with", "Mensen gesproken"),
    "streak": ("Weekly streak", "Weken op rij"),
    "cafe": ("Café Hours joined", "Café Hours"),
    "achievements": ("Achievements", "Prestaties"),
    "none_yet": ("None yet. Join a voice channel to earn your first.", "Nog geen. Ga in een spraakkanaal voor je eerste."),
    "footer": ("Only your own progress. No rankings.", "Alleen je eigen voortgang. Geen ranglijst."),
    "share": ("Share", "Delen"),
    "shared": ("Shared in #your-successes-and-stories.", "Gedeeld."),
}


def _t(key: str, is_nl: bool, **kw: Any) -> str:
    return LABELS[key][1 if is_nl else 0].format(**kw)


def fmt_duration(seconds: int) -> str:
    minutes = max(0, int(seconds)) // 60
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


def milestone_line(seconds: int, role_names: dict[int, str] | None = None) -> str:
    """'3h Speaker, 4h 10m of 10h' style: current tier and progress to the next.
    Uses the real Discord role names when known."""
    role_names = role_names or {}
    tiers = [(t, role_names.get(rid) or name) for t, name, rid in MILESTONE_ROLES]
    current = None
    nxt = None
    for threshold, name in tiers:
        if seconds >= threshold:
            current = (threshold, name)
        elif nxt is None:
            nxt = (threshold, name)
    cur_txt = current[1] if current else "No milestone yet"
    if nxt is None:
        return f"{cur_txt} (top milestone reached)"
    return f"{cur_txt}, {fmt_duration(seconds)} of {fmt_duration(nxt[0])}"


def weekly_streak(session_starts: list[int], now: dt.datetime) -> int:
    """Weeks in a row (Mon to Sun, Amsterdam) with at least one session, ending this week or last week."""
    weeks = {dt.datetime.fromtimestamp(s, tz=TZ).date().isocalendar()[:2] for s in session_starts}
    if not weeks:
        return 0

    def prev(week: tuple[int, int]) -> tuple[int, int]:
        monday = dt.date.fromisocalendar(week[0], week[1], 1) - dt.timedelta(days=7)
        return monday.isocalendar()[:2]

    current = now.astimezone(TZ).date().isocalendar()[:2]
    # A streak is still alive if this week has no session yet but last week did.
    cursor = current if current in weeks else prev(current)
    streak = 0
    while cursor in weeks:
        streak += 1
        cursor = prev(cursor)
    return streak


def week_start(now: dt.datetime) -> dt.datetime:
    local = now.astimezone(TZ)
    monday = local.date() - dt.timedelta(days=local.weekday())
    return dt.datetime.combine(monday, dt.time(0, 0), tzinfo=TZ)


async def build_profile_embed(bot: Any, member: discord.Member) -> discord.Embed:
    repo = bot.repo
    guild_id = member.guild.id
    is_nl = guild_id == getattr(bot, "dutch_guild_id", None)
    is_en = guild_id == getattr(bot, "guild_id", None)
    now = dt.datetime.now(tz=TZ)

    raw_start = await repo.kv_get(guild_id, MILESTONE_START_KV)
    start = int(raw_start) if raw_start else int(now.timestamp())
    total = await repo.user_voice_seconds_since(guild_id, member.id, start)
    this_week = await repo.user_voice_seconds_since(guild_id, member.id, max(start, int(week_start(now).timestamp())))
    people = await repo.profile_people_met(guild_id, member.id)
    streak = weekly_streak(await repo.profile_session_starts(guild_id, member.id), now)
    earned = await repo.profile_achievements(guild_id, member.id)

    start_date = dt.datetime.fromtimestamp(start, tz=TZ).strftime("%-d %b")
    embed = discord.Embed(title=_t("title", is_nl, name=member.display_name), color=0xF28C28)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name=_t("total", is_nl), value=f"**{fmt_duration(total)}** ({_t('since', is_nl, date=start_date)})", inline=True)
    embed.add_field(name=_t("week", is_nl), value=f"**{fmt_duration(this_week)}**", inline=True)
    if is_en:
        role_names = {}
        for _thr, _name, rid in MILESTONE_ROLES:
            role = member.guild.get_role(rid) if rid else None
            if role is not None:
                role_names[rid] = role.name
        embed.add_field(name=_t("milestone", is_nl), value=milestone_line(total, role_names), inline=False)
    embed.add_field(name=_t("people", is_nl), value=f"**{people}**", inline=True)
    week_word = ("week" if streak == 1 else "weeks") if not is_nl else ("week" if streak == 1 else "weken")
    embed.add_field(name=_t("streak", is_nl), value=f"**{streak}** {week_word}", inline=True)
    if is_en and getattr(getattr(bot, "cafe_hour", None), "enabled", False):
        joined = await repo.profile_cafe_hours_joined(
            guild_id, member.id, CAFE_HOUR_VOICE_CHANNEL_ID, CAFE_HOUR_DURATION_MIN * 60, CAFE_HOUR_MIN_SECONDS
        )
        embed.add_field(name=_t("cafe", is_nl), value=f"**{joined}**", inline=True)

    names = [ACHIEVEMENT_NAMES.get(a, (a.replace("_", " "), a.replace("_", " ")))[1 if is_nl else 0] for a, _t2 in earned]
    embed.add_field(
        name=f"{_t('achievements', is_nl)} ({len(names)})",
        value="\n".join(f"🏅 {n}" for n in names) if names else _t("none_yet", is_nl),
        inline=False,
    )
    embed.set_footer(text=_t("footer", is_nl))
    return embed


class ShareProfileView(discord.ui.View):
    """Under the private card. Only the member who ran /profile sees it."""

    def __init__(self, *, owner_id: int, is_nl: bool) -> None:
        super().__init__(timeout=10 * 60)
        self.owner_id = owner_id
        self.is_nl = is_nl
        self.share.label = _t("share", is_nl)

    @discord.ui.button(label="Share", style=discord.ButtonStyle.primary, emoji="📣")
    async def share(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self.owner_id or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This is someone else's profile.", ephemeral=True)
            return
        channel_id = MILESTONE_ANNOUNCE_CHANNEL_ID or SHARE_CHANNEL_ID_FALLBACK
        channel = interaction.client.get_channel(channel_id) if not self.is_nl else None
        if self.is_nl or not isinstance(channel, discord.TextChannel):
            # The NL server has no shares channel yet: share in the channel where /profile was used.
            channel = interaction.channel
        try:
            embed = await build_profile_embed(interaction.client, interaction.user)
            await channel.send(
                f"{interaction.user.mention} shared their speaking profile." if not self.is_nl
                else f"{interaction.user.mention} deelt hun spreekprofiel.",
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except Exception as e:
            log.warning("Profile: share failed user=%s (%s)", interaction.user.id, e)
            await interaction.response.send_message("Sharing didn't work right now. Try again later.", ephemeral=True)
            return
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(_t("shared", self.is_nl), ephemeral=True)
        log.info("Profile: shared user=%s", interaction.user.id)


async def setup(bot: Any) -> None:
    @bot.tree.command(name="profile", description="See your own speaking progress (only you can see it).")
    async def cmd_profile(interaction: discord.Interaction) -> None:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Use /profile inside the server.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await bot.repo.command_usage_record(interaction.guild.id, interaction.user.id, "profile", int(time.time()))
        except Exception:
            pass
        is_nl = interaction.guild.id == getattr(bot, "dutch_guild_id", None)
        embed = await build_profile_embed(bot, interaction.user)
        await interaction.followup.send(
            embed=embed,
            view=ShareProfileView(owner_id=interaction.user.id, is_nl=is_nl),
            ephemeral=True,
        )
