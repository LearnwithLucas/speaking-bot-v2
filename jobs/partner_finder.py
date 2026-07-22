from __future__ import annotations

# jobs/partner_finder.py
import asyncio
import datetime as dt
import logging
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord

from db.repo import Repo
from jobs.partner_planner import PartnerPlanStartView

log = logging.getLogger("jobs.partner_finder")

# ---- Channel IDs ----
EN_LOOKING_CHANNEL_ID = 1435902125652578434   # 🙋┃looking-for-a-partner
NL_LOOKING_CHANNEL_ID = 1484566832982654996   # 🙋┃op-zoek-naar-een-partner
OPEN_CONVERSATION_CHANNEL_ID = 1456551629301219420  # 🌍 | Open Conversation

KV_EN_HUB_MSG_ID = "partner_hub_message_id"
KV_NL_HUB_MSG_ID = "partner_hub_nl_message_id"
I_WANT_TO_SPEAK_ROLE_ID = 1529421061727322172
KV_EN_HUB_WEEKLY_REPOST_DATE = "partner_hub_weekly_repost_date_v1"
KV_EN_WEEKLY_SPEAKERS_MSG_ID = "partner_weekly_speakers_message_id"
KV_NL_WEEKLY_SPEAKERS_MSG_ID = "partner_weekly_speakers_nl_message_id"
KV_EN_WEEKLY_WELL_DONE_DATE = "partner_weekly_well_done_date"
KV_NL_WEEKLY_WELL_DONE_DATE = "partner_weekly_well_done_nl_date"

DURATION_OPTIONS: tuple[tuple[int, str, str], ...] = (
    (15 * 60, "15 min", "15 min"),
    (30 * 60, "30 min", "30 min"),
    (45 * 60, "45 min", "45 min"),
    (60 * 60, "1 hour", "1 uur"),
    (2 * 60 * 60, "2 hours", "2 uur"),
    (3 * 60 * 60, "3 hours", "3 uur"),
)
DEFAULT_DURATION_SECONDS = 30 * 60
MAX_WEEKLY_SPEAKERS = 20
WEEKLY_SPEAKERS_REFRESH_SECONDS = 15 * 60
WEEKLY_WELL_DONE_POST_HOUR = 18
MONDAY_HUB_REPOST_HOUR = 9
WEEKLY_SPEAKERS_FOOTER_EN = "active this week:en:v2"
WEEKLY_SPEAKERS_FOOTER_NL = "actief deze week:nl:v2"


def _duration_label(seconds: int, *, is_nl: bool = False) -> str:
    for option_seconds, en_label, nl_label in DURATION_OPTIONS:
        if option_seconds == seconds:
            return nl_label if is_nl else en_label
    minutes = max(1, int(seconds / 60))
    if minutes < 60:
        return f"{minutes} min"
    hours = round(minutes / 60, 1)
    if is_nl:
        return f"{hours:g} uur"
    return f"{hours:g} hour" if hours == 1 else f"{hours:g} hours"


def _open_conversation_link(guild_id: int) -> str:
    return f"https://discord.com/channels/{guild_id}/{OPEN_CONVERSATION_CHANNEL_ID}"


def _amsterdam_week_start_epoch() -> int:
    try:
        tz = ZoneInfo("Europe/Amsterdam")
        now = dt.datetime.now(tz=tz)
    except ZoneInfoNotFoundError:
        now = dt.datetime.now()
    week_start = (now - dt.timedelta(days=now.weekday())).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return int(week_start.timestamp())


def _amsterdam_now() -> dt.datetime:
    try:
        tz = ZoneInfo("Europe/Amsterdam")
        return dt.datetime.now(tz=tz)
    except ZoneInfoNotFoundError:
        return dt.datetime.now()


def _conversation_starters(*, is_nl: bool) -> str:
    if is_nl:
        return (
            "\n\n**Makkelijke starters:**\n"
            "- What did you do today?\n"
            "- Tell me about a food you like.\n"
            "- What is one thing you want to practice in English?\n\n"
            "Je hoeft niet perfect te praten. Kies gewoon een vraag."
        )
    return (
        "\n\n**Easy starters:**\n"
        "- What did you do today?\n"
        "- Tell me about a food you like.\n"
        "- What is one thing you want to practice in English?\n\n"
        "No need to make it perfect. Pick one and start there."
    )


def _hub_content(*, is_nl: bool, weekly_ping: bool = False) -> str | None:
    if is_nl:
        return None
    role_mention = f"<@&{I_WANT_TO_SPEAK_ROLE_ID}>"
    if weekly_ping:
        return (
            f"{role_mention} New week, new speaking practice.\n"
            "Click **I want to speak** if you want to stay on the active speaker ping list."
        )
    return (
        "Want to be pinged when people are looking for a chat? Click **I want to speak**.\n"
        f"Members can mention {role_mention} when they are ready to talk."
    )


# =====================
# HUB EMBEDS
# =====================

def build_en_embed(available_count: int = 0) -> discord.Embed:
    if available_count == 0:
        status = "Nobody is available right now. Press a time button to be the first."
    elif available_count == 1:
        status = "1 person is free to practice right now."
    else:
        status = f"{available_count} people are free to practice right now."

    embed = discord.Embed(
        title="🤝 Find a speaking partner",
        description=(
            "Choose how long you are available to practice.\n"
            "If someone else is free at the same time, you both get a DM with the Open Conversation channel.\n"
            "You can also plan a rough time for later.\n"
            "Use **I want to speak** to join or leave the active speaker ping role.\n"
            "You can refresh or change your time whenever you want.\n\n"
            f"**Right now:** {status}"
        ),
    )
    embed.set_footer(text="hub:en:partner:v3")
    return embed


def build_nl_embed(available_count: int = 0) -> discord.Embed:
    if available_count == 0:
        status = "Er is nu niemand beschikbaar. Druk op een tijdknop om de eerste te zijn."
    elif available_count == 1:
        status = "1 persoon is nu vrij om te oefenen."
    else:
        status = f"{available_count} mensen zijn nu vrij om te oefenen."

    embed = discord.Embed(
        title="🤝 Vind een spreekpartner",
        description=(
            "Kies hoe lang je beschikbaar bent om te oefenen.\n"
            "Als iemand anders ook vrij is, krijgen jullie allebei een DM met het Open Conversation kanaal.\n"
            "Je kunt ook een rustig moment voor later plannen.\n"
            "Je kunt je tijd altijd vernieuwen of aanpassen.\n\n"
            f"**Op dit moment:** {status}"
        ),
    )
    embed.set_footer(text="hub:nl:partner:v3")
    return embed


def build_weekly_speakers_embed(
    speaker_names: list[str],
    *,
    hidden_count: int = 0,
    is_nl: bool = False,
) -> discord.Embed:
    if is_nl:
        embed = discord.Embed(
            title="Actief deze week",
            color=discord.Color.green(),
        )
        if speaker_names:
            embed.description = (
                "Deze mensen zijn sinds maandag in voice geweest. "
                "Zeg gerust hoi als je een rustige spreekpartner zoekt."
            )
            _add_speaker_columns(embed, speaker_names)
        else:
            embed.description = (
                "Nog niemand is deze week in voice geweest. "
                "Zodra iemand oefent, verschijnt die persoon hier."
            )
        if hidden_count:
            embed.add_field(name="Meer", value=f"en {hidden_count} meer", inline=False)
        embed.set_footer(text=WEEKLY_SPEAKERS_FOOTER_NL)
        return embed

    embed = discord.Embed(
        title="Active this week",
        color=discord.Color.green(),
    )
    if speaker_names:
        embed.description = (
            "These people have joined voice since Monday. "
            "Say hi if you want a low-pressure speaking partner."
        )
        _add_speaker_columns(embed, speaker_names)
    else:
        embed.description = (
            "Nobody has joined voice yet this week. "
            "When someone practices, they will appear here."
        )
    if hidden_count:
        embed.add_field(name="More", value=f"and {hidden_count} more", inline=False)
    embed.set_footer(text=WEEKLY_SPEAKERS_FOOTER_EN)
    return embed


def _add_speaker_columns(embed: discord.Embed, speaker_names: list[str]) -> None:
    column_count = 3 if len(speaker_names) >= 9 else 2
    column_size = max(1, (len(speaker_names) + column_count - 1) // column_count)
    for index in range(0, len(speaker_names), column_size):
        column = speaker_names[index:index + column_size]
        embed.add_field(
            name="\u200b",
            value="\n".join(f"- {name}" for name in column),
            inline=True,
        )


# =====================
# PERSISTENT HUB VIEWS
# =====================

class PartnerHubView(discord.ui.View):
    """English persistent view in #looking-for-a-partner."""

    def __init__(self, *, finder: "PartnerFinder | None" = None) -> None:
        super().__init__(timeout=None)
        self._finder = finder

    async def _mark(self, interaction: discord.Interaction, *, duration_seconds: int) -> None:
        if self._finder is None:
            await interaction.response.send_message(
                "Not ready yet. Try again in a moment.", ephemeral=True
            )
            return
        await self._finder.mark_available(
            user=interaction.user,
            guild=interaction.guild,
            interaction=interaction,
            duration_seconds=duration_seconds,
            is_nl=False,
        )

    async def _plan_later(self, interaction: discord.Interaction, *, is_nl: bool) -> None:
        if self._finder is None:
            await interaction.response.send_message(
                "Not ready yet. Try again in a moment.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "When would you like to practice?",
            view=PartnerPlanStartView(bot=self._finder.bot, is_nl=is_nl),
            ephemeral=True,
        )

    async def _toggle_speaking_role(self, interaction: discord.Interaction) -> None:
        if self._finder is None:
            await interaction.response.send_message(
                "Not ready yet. Try again in a moment.", ephemeral=True
            )
            return
        await self._finder.toggle_speaking_role(interaction)

    @discord.ui.button(label="15 min", style=discord.ButtonStyle.secondary, custom_id="partner:free:en:15m:v3", row=0)
    async def free_15(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=15 * 60)

    @discord.ui.button(label="30 min", style=discord.ButtonStyle.success, custom_id="partner:free:en:30m:v3", row=0)
    async def free_30(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=30 * 60)

    @discord.ui.button(label="45 min", style=discord.ButtonStyle.secondary, custom_id="partner:free:en:45m:v3", row=0)
    async def free_45(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=45 * 60)

    @discord.ui.button(label="1 hour", style=discord.ButtonStyle.secondary, custom_id="partner:free:en:1h:v3", row=1)
    async def free_1h(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=60 * 60)

    @discord.ui.button(label="2 hours", style=discord.ButtonStyle.secondary, custom_id="partner:free:en:2h:v3", row=1)
    async def free_2h(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=2 * 60 * 60)

    @discord.ui.button(label="3 hours", style=discord.ButtonStyle.secondary, custom_id="partner:free:en:3h:v3", row=1)
    async def free_3h(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=3 * 60 * 60)

    @discord.ui.button(label="Plan for later", style=discord.ButtonStyle.primary, custom_id="partner:plan:en:v1", row=2)
    async def plan_later(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._plan_later(interaction, is_nl=False)

    @discord.ui.button(label="I want to speak", style=discord.ButtonStyle.primary, custom_id="partner:speak_role:en:v1", row=2)
    async def want_to_speak(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._toggle_speaking_role(interaction)


class PartnerHubViewNL(discord.ui.View):
    """Dutch persistent view in #op-zoek-naar-een-partner."""

    def __init__(self, *, finder: "PartnerFinder | None" = None) -> None:
        super().__init__(timeout=None)
        self._finder = finder

    async def _mark(self, interaction: discord.Interaction, *, duration_seconds: int) -> None:
        if self._finder is None:
            await interaction.response.send_message(
                "Nog niet klaar. Probeer het zo opnieuw.", ephemeral=True
            )
            return
        await self._finder.mark_available(
            user=interaction.user,
            guild=interaction.guild,
            interaction=interaction,
            duration_seconds=duration_seconds,
            is_nl=True,
        )

    async def _plan_later(self, interaction: discord.Interaction, *, is_nl: bool) -> None:
        if self._finder is None:
            await interaction.response.send_message(
                "Nog niet klaar. Probeer het zo opnieuw.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "Wanneer wil je ongeveer oefenen?",
            view=PartnerPlanStartView(bot=self._finder.bot, is_nl=is_nl),
            ephemeral=True,
        )

    @discord.ui.button(label="15 min", style=discord.ButtonStyle.secondary, custom_id="partner:free:nl:15m:v3", row=0)
    async def free_15_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=15 * 60)

    @discord.ui.button(label="30 min", style=discord.ButtonStyle.success, custom_id="partner:free:nl:30m:v3", row=0)
    async def free_30_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=30 * 60)

    @discord.ui.button(label="45 min", style=discord.ButtonStyle.secondary, custom_id="partner:free:nl:45m:v3", row=0)
    async def free_45_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=45 * 60)

    @discord.ui.button(label="1 uur", style=discord.ButtonStyle.secondary, custom_id="partner:free:nl:1h:v3", row=1)
    async def free_1h_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=60 * 60)

    @discord.ui.button(label="2 uur", style=discord.ButtonStyle.secondary, custom_id="partner:free:nl:2h:v3", row=1)
    async def free_2h_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=2 * 60 * 60)

    @discord.ui.button(label="3 uur", style=discord.ButtonStyle.secondary, custom_id="partner:free:nl:3h:v3", row=1)
    async def free_3h_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=3 * 60 * 60)

    @discord.ui.button(label="Plan voor later", style=discord.ButtonStyle.primary, custom_id="partner:plan:nl:v1", row=2)
    async def plan_later_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._plan_later(interaction, is_nl=True)


# =====================
# CORE SERVICE
# =====================

class PartnerFinder:
    def __init__(
        self,
        *,
        bot: discord.Client,
        repo: Repo,
        guild_id: int,
        dutch_guild_id: int | None = None,
    ) -> None:
        self.bot = bot
        self.repo = repo
        self.guild_id = guild_id
        self.dutch_guild_id = dutch_guild_id

        # Separate availability dicts per server
        # user_id -> expires_at (epoch)
        self._available_en: dict[int, float] = {}
        self._available_nl: dict[int, float] = {}
        self._weekly_speakers_task: asyncio.Task | None = None
        self._weekly_speakers_locks: dict[bool, asyncio.Lock] = {
            False: asyncio.Lock(),
            True: asyncio.Lock(),
        }
        self._start_weekly_speakers_refresh()

    def _start_weekly_speakers_refresh(self) -> None:
        try:
            self._weekly_speakers_task = asyncio.create_task(self._weekly_speakers_refresh_loop())
        except RuntimeError:
            self._weekly_speakers_task = None

    async def _weekly_speakers_refresh_loop(self) -> None:
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self._maybe_repost_monday_hub()
                await self._maybe_post_weekly_well_done(is_nl=False)
                await self._publish_weekly_speakers_message(is_nl=False)
                if self.dutch_guild_id:
                    await self._maybe_post_weekly_well_done(is_nl=True)
                    await self._publish_weekly_speakers_message(is_nl=True)
            except Exception:
                log.exception("PartnerFinder: weekly speakers refresh failed")
            await asyncio.sleep(WEEKLY_SPEAKERS_REFRESH_SECONDS)

    def _pool(self, is_nl: bool) -> dict[int, float]:
        return self._available_nl if is_nl else self._available_en

    def _clean_expired(self, is_nl: bool) -> None:
        pool = self._pool(is_nl)
        now = time.time()
        for uid in [uid for uid, exp in pool.items() if now >= exp]:
            del pool[uid]

    def _available_users(self, is_nl: bool) -> list[int]:
        self._clean_expired(is_nl)
        return list(self._pool(is_nl).keys())

    async def mark_available(
        self,
        *,
        user: discord.User | discord.Member,
        guild: discord.Guild | None,
        interaction: discord.Interaction,
        duration_seconds: int = DEFAULT_DURATION_SECONDS,
        is_nl: bool = False,
    ) -> None:
        pool = self._pool(is_nl)
        self._clean_expired(is_nl)
        uid = user.id
        now = time.time()
        duration_label = _duration_label(duration_seconds, is_nl=is_nl)

        already_available = uid in pool
        expires_at = now + duration_seconds
        pool[uid] = expires_at

        others = [u for u in self._available_users(is_nl) if u != uid]

        if is_nl:
            if already_available:
                msg = (
                    f"Je bent nog steeds beschikbaar. Je tijd is bijgewerkt naar **{duration_label}**.\n"
                    + ("Er is ook iemand anders vrij. Bekijk je DMs." if others else "Er is nog niemand anders vrij. Je krijgt een DM zodra iemand zich aanmeldt.")
                )
            elif others:
                count = len(others)
                msg = (
                    f"Je bent **{duration_label}** vrij om te oefenen. {count} {'persoon is' if count == 1 else 'mensen zijn'} ook vrij.\n"
                    "Bekijk je DMs."
                )
            else:
                msg = (
                    f"Je bent de komende **{duration_label}** beschikbaar.\n"
                    "Je krijgt een DM zodra iemand anders ook vrij is."
                )
        else:
            if already_available:
                msg = (
                    f"You're still marked as free. Your time is now **{duration_label}**.\n"
                    + ("Someone else is also free right now. Check your DMs." if others else "Nobody else is free yet. You will get a DM when someone joins.")
                )
            elif others:
                count = len(others)
                msg = (
                    f"You're free to practice for **{duration_label}**. {count} {'person is' if count == 1 else 'people are'} also free right now.\n"
                    "Check your DMs."
                )
            else:
                msg = (
                    f"You're marked as free for the next **{duration_label}**.\n"
                    "You will get a DM as soon as someone else is free too."
                )

        await interaction.response.send_message(msg, ephemeral=True)
        await self._update_hub_embed(is_nl=is_nl)

        if others and guild:
            await self._notify_matches(
                new_user=user,
                match_ids=others,
                guild=guild,
                is_nl=is_nl,
            )

        asyncio.create_task(self._expire_after(uid, duration_seconds, expires_at=expires_at, is_nl=is_nl))

    async def toggle_speaking_role(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This only works inside the server.", ephemeral=True
            )
            return
        if interaction.guild.id != self.guild_id:
            await interaction.response.send_message(
                "This role is only configured for the English community.",
                ephemeral=True,
            )
            return
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "I could not read your server membership. Try again in a moment.",
                ephemeral=True,
            )
            return

        role = interaction.guild.get_role(I_WANT_TO_SPEAK_ROLE_ID)
        if role is None:
            await interaction.response.send_message(
                "I could not find the **I want to speak** role. Please tell Lucas to check the role ID.",
                ephemeral=True,
            )
            return

        try:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(
                    role,
                    reason="SpeakingBot: user opted out of I want to speak role",
                )
                await interaction.response.send_message(
                    "Removed **I want to speak**. You will not be pinged for casual chat requests.",
                    ephemeral=True,
                )
            else:
                await interaction.user.add_roles(
                    role,
                    reason="SpeakingBot: user opted into I want to speak role",
                )
                await interaction.response.send_message(
                    "Added **I want to speak**. People can tag this role when they want a chat.",
                    ephemeral=True,
                )
        except discord.Forbidden:
            log.warning("PartnerFinder: missing permission to manage role %s", I_WANT_TO_SPEAK_ROLE_ID)
            await interaction.response.send_message(
                "I do not have permission to manage that role yet. Please check Manage Roles and role hierarchy.",
                ephemeral=True,
            )
        except Exception:
            log.exception("PartnerFinder: failed to toggle speaking role for user=%s", interaction.user.id)
            await interaction.response.send_message(
                "Something went wrong while updating your role. Try again in a moment.",
                ephemeral=True,
            )

    async def _expire_after(self, user_id: int, seconds: float, *, expires_at: float, is_nl: bool) -> None:
        await asyncio.sleep(seconds)
        pool = self._pool(is_nl)
        current_expires_at = pool.get(user_id)
        if current_expires_at is None:
            return
        if current_expires_at > expires_at + 0.5:
            return
        pool.pop(user_id, None)
        await self._update_hub_embed(is_nl=is_nl)
        log.info("PartnerFinder: availability expired user=%s is_nl=%s", user_id, is_nl)

    async def _notify_matches(
        self,
        *,
        new_user: discord.User | discord.Member,
        match_ids: list[int],
        guild: discord.Guild,
        is_nl: bool,
    ) -> None:
        open_conversation = _open_conversation_link(guild.id)
        starters = _conversation_starters(is_nl=is_nl)

        names = []
        for mid in match_ids[:3]:
            try:
                m = guild.get_member(mid) or await guild.fetch_member(mid)
                names.append(m.display_name)
            except Exception:
                pass
        names_str = ", ".join(names) if names else ("iemand" if is_nl else "someone")
        verb = "is" if len(names) == 1 else "are"
        verb_nl = "is" if len(names) == 1 else "zijn"

        try:
            if is_nl:
                await new_user.send(
                    f"🤝 **Spreekpartner gevonden!**\n\n"
                    f"**{names_str}** {verb_nl} ook vrij op dit moment.\n\n"
                    f"Ga naar Open Conversation: {open_conversation}\n"
                    f"Begin rustig. Je kunt gewoon hoi zeggen.{starters}"
                )
            else:
                await new_user.send(
                    f"🤝 **Partner match!**\n\n"
                    f"**{names_str}** {verb} also free right now.\n\n"
                    f"Go to Open Conversation: {open_conversation}\n"
                    f"Start gently. You can just say hi.{starters}"
                )
        except discord.Forbidden:
            log.info("PartnerFinder: DM blocked user=%s", new_user.id)
        except Exception:
            log.exception("PartnerFinder: failed to DM new user=%s", new_user.id)

        for match_id in match_ids:
            try:
                match_member = guild.get_member(match_id) or await guild.fetch_member(match_id)
                if is_nl:
                    await match_member.send(
                        f"🤝 **Spreekpartner gevonden!**\n\n"
                        f"**{new_user.display_name}** is nu vrij om te oefenen.\n\n"
                        f"Ga naar Open Conversation: {open_conversation}\n"
                        f"Begin rustig. Je kunt gewoon hoi zeggen.{starters}"
                    )
                else:
                    await match_member.send(
                        f"🤝 **Partner match!**\n\n"
                        f"**{new_user.display_name}** is free to practice right now.\n\n"
                        f"Go to Open Conversation: {open_conversation}\n"
                        f"Start gently. You can just say hi.{starters}"
                    )
            except discord.Forbidden:
                log.info("PartnerFinder: DM blocked match=%s", match_id)
            except Exception:
                log.exception("PartnerFinder: failed to DM match=%s", match_id)

    # ---- Hub embeds ----

    async def _fetch_partner_channel(self, *, is_nl: bool) -> discord.TextChannel | None:
        channel_id = NL_LOOKING_CHANNEL_ID if is_nl else EN_LOOKING_CHANNEL_ID
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception:
                log.warning("PartnerFinder: could not fetch channel %s", channel_id)
                return None

        if not isinstance(channel, discord.TextChannel):
            return None
        return channel

    async def _weekly_speaker_ids(self, guild_id: int) -> list[int]:
        now_epoch = int(time.time())
        since_epoch = _amsterdam_week_start_epoch()
        cur = await self.repo.conn.execute(
            """
            SELECT user_id
            FROM voice_sessions
            WHERE guild_id = ?
              AND started_at <= ?
              AND COALESCE(ended_at, ?) >= ?
            GROUP BY user_id
            ORDER BY MAX(COALESCE(ended_at, ?)) DESC
            LIMIT ?
            """,
            (
                guild_id,
                now_epoch,
                now_epoch,
                since_epoch,
                now_epoch,
                MAX_WEEKLY_SPEAKERS + 1,
            ),
        )
        rows = await cur.fetchall()
        return [int(row[0]) for row in rows]

    async def _weekly_speaker_names(
        self,
        *,
        guild_id: int,
        is_nl: bool,
    ) -> tuple[list[str], int]:
        guild = self.bot.get_guild(guild_id)
        user_ids = await self._weekly_speaker_ids(guild_id)
        names: list[str] = []

        for user_id in user_ids:
            member = None
            try:
                if guild is not None:
                    member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            except Exception:
                log.info("PartnerFinder: could not fetch weekly speaker user=%s is_nl=%s", user_id, is_nl)

            if member is None or member.bot:
                continue
            names.append(discord.utils.escape_markdown(member.display_name))
            if len(names) >= MAX_WEEKLY_SPEAKERS:
                break

        hidden_count = max(0, len(user_ids) - len(names))
        return names, hidden_count

    async def _weekly_speaker_mentions(
        self,
        *,
        guild_id: int,
        is_nl: bool,
    ) -> tuple[list[str], int]:
        guild = self.bot.get_guild(guild_id)
        user_ids = await self._weekly_speaker_ids(guild_id)
        mentions: list[str] = []

        for user_id in user_ids:
            member = None
            try:
                if guild is not None:
                    member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            except Exception:
                log.info("PartnerFinder: could not fetch weekly well-done user=%s is_nl=%s", user_id, is_nl)

            if member is None or member.bot:
                continue
            mentions.append(member.mention)
            if len(mentions) >= MAX_WEEKLY_SPEAKERS:
                break

        hidden_count = max(0, len(user_ids) - len(mentions))
        return mentions, hidden_count

    async def _build_weekly_speakers_embed(self, *, guild_id: int, is_nl: bool) -> discord.Embed:
        names, hidden_count = await self._weekly_speaker_names(guild_id=guild_id, is_nl=is_nl)
        return build_weekly_speakers_embed(names, hidden_count=hidden_count, is_nl=is_nl)

    async def _publish_weekly_speakers_message(self, *, is_nl: bool) -> None:
        guild_id = self.dutch_guild_id if is_nl else self.guild_id
        kv_key = KV_NL_WEEKLY_SPEAKERS_MSG_ID if is_nl else KV_EN_WEEKLY_SPEAKERS_MSG_ID

        if guild_id is None:
            return

        channel = await self._fetch_partner_channel(is_nl=is_nl)
        if channel is None:
            return

        lock = self._weekly_speakers_locks[is_nl]
        async with lock:
            embed = await self._build_weekly_speakers_embed(guild_id=guild_id, is_nl=is_nl)
            existing_id_raw = await self.repo.kv_get(guild_id, kv_key)
            if existing_id_raw:
                try:
                    msg = await channel.fetch_message(int(existing_id_raw))
                    await msg.edit(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                    await self._delete_duplicate_weekly_speakers_messages(
                        channel,
                        keep_message_id=msg.id,
                        is_nl=is_nl,
                    )
                    return
                except Exception:
                    log.warning("PartnerFinder: could not edit weekly speakers message, recreating is_nl=%s", is_nl)

            try:
                sent = await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                await self.repo.kv_set(guild_id, kv_key, str(sent.id))
                await self._delete_duplicate_weekly_speakers_messages(
                    channel,
                    keep_message_id=sent.id,
                    is_nl=is_nl,
                )
                log.info("PartnerFinder: posted weekly speakers message %s is_nl=%s", sent.id, is_nl)
            except Exception:
                log.exception("PartnerFinder: failed to post weekly speakers message is_nl=%s", is_nl)

    async def _maybe_post_weekly_well_done(self, *, is_nl: bool) -> None:
        guild_id = self.dutch_guild_id if is_nl else self.guild_id
        kv_key = KV_NL_WEEKLY_WELL_DONE_DATE if is_nl else KV_EN_WEEKLY_WELL_DONE_DATE

        if guild_id is None:
            return

        now = _amsterdam_now()
        if now.weekday() != 6 or now.hour < WEEKLY_WELL_DONE_POST_HOUR:
            return

        day_key = now.date().isoformat()
        if await self.repo.kv_get(guild_id, kv_key) == day_key:
            return

        mentions, hidden_count = await self._weekly_speaker_mentions(guild_id=guild_id, is_nl=is_nl)
        await self.repo.kv_set(guild_id, kv_key, day_key)
        if not mentions:
            return

        channel = await self._fetch_partner_channel(is_nl=is_nl)
        if channel is None:
            return

        if is_nl:
            content = (
                "Zondag compliment voor iedereen die deze week in voice heeft geoefend, "
                "voordat de lijst maandag opnieuw begint:\n"
                f"{' '.join(mentions)}\n\n"
                "Goed gedaan. Geen scorebord, gewoon mooi dat jullie zijn komen oefenen."
            )
            if hidden_count:
                content += f"\nEn nog {hidden_count} anderen hebben ook geoefend."
        else:
            content = (
                "Sunday well done to everyone who practiced in voice this week, "
                "before the list starts fresh on Monday:\n"
                f"{' '.join(mentions)}\n\n"
                "Well done. No leaderboard, just glad you showed up to practice."
            )
            if hidden_count:
                content += f"\nAnd {hidden_count} more people practiced too."

        try:
            await channel.send(
                content,
                allowed_mentions=discord.AllowedMentions(users=True),
            )
            log.info("PartnerFinder: posted Sunday well-done message is_nl=%s", is_nl)
        except Exception:
            log.exception("PartnerFinder: failed to post Sunday well-done message is_nl=%s", is_nl)

    async def _delete_duplicate_weekly_speakers_messages(
        self,
        channel: discord.TextChannel,
        *,
        keep_message_id: int,
        is_nl: bool,
    ) -> None:
        expected_footers = {
            WEEKLY_SPEAKERS_FOOTER_NL if is_nl else WEEKLY_SPEAKERS_FOOTER_EN,
            "actief deze week:nl:v1" if is_nl else "active this week:en:v1",
        }

        try:
            bot_user = self.bot.user
            if bot_user is None:
                return

            async for message in channel.history(limit=25):
                if message.id == keep_message_id:
                    continue
                if message.author.id != bot_user.id:
                    continue
                if not message.embeds:
                    continue
                footer = message.embeds[0].footer.text
                if footer not in expected_footers:
                    continue
                try:
                    await message.delete()
                    log.info("PartnerFinder: deleted duplicate weekly speakers message %s", message.id)
                except discord.Forbidden:
                    log.info("PartnerFinder: missing permission to delete duplicate weekly speakers message %s", message.id)
                except Exception:
                    log.exception("PartnerFinder: failed to delete duplicate weekly speakers message %s", message.id)
        except Exception:
            log.exception("PartnerFinder: failed to scan for duplicate weekly speakers messages")

    async def _delete_old_hub_message(
        self,
        channel: discord.TextChannel,
        *,
        message_id: int,
    ) -> None:
        try:
            msg = await channel.fetch_message(message_id)
        except Exception:
            return

        try:
            await msg.unpin(reason="SpeakingBot: replaced weekly partner hub")
        except discord.NotFound:
            pass
        except discord.Forbidden:
            log.info("PartnerFinder: missing permission to unpin old hub message %s", message_id)
        except Exception:
            pass

        try:
            await msg.delete()
            log.info("PartnerFinder: deleted old hub message %s", message_id)
        except discord.Forbidden:
            log.info("PartnerFinder: missing permission to delete old hub message %s", message_id)
            try:
                await msg.edit(view=None)
            except Exception:
                log.exception("PartnerFinder: could not clear old hub view %s", message_id)
        except Exception:
            log.exception("PartnerFinder: failed to delete old hub message %s", message_id)

    async def _maybe_repost_monday_hub(self) -> None:
        now = _amsterdam_now()
        if now.weekday() != 0 or now.hour < MONDAY_HUB_REPOST_HOUR:
            return

        date_key = now.date().isoformat()
        if await self.repo.kv_get(self.guild_id, KV_EN_HUB_WEEKLY_REPOST_DATE) == date_key:
            return

        posted = await self.publish_hub(
            is_nl=False,
            force_new=True,
            weekly_ping=True,
        )
        if posted:
            await self.repo.kv_set(self.guild_id, KV_EN_HUB_WEEKLY_REPOST_DATE, date_key)

    async def _update_hub_embed(self, *, is_nl: bool) -> None:
        self._clean_expired(is_nl)
        count = len(self._pool(is_nl))
        kv_key = KV_NL_HUB_MSG_ID if is_nl else KV_EN_HUB_MSG_ID
        guild_id = self.dutch_guild_id if is_nl else self.guild_id

        if guild_id is None:
            return

        channel = await self._fetch_partner_channel(is_nl=is_nl)
        if channel is None:
            return

        existing_id_raw = await self.repo.kv_get(guild_id, kv_key)
        if not existing_id_raw:
            return

        embed = build_nl_embed(count) if is_nl else build_en_embed(count)
        view = PartnerHubViewNL(finder=self) if is_nl else PartnerHubView(finder=self)
        content = _hub_content(is_nl=is_nl)

        try:
            msg = await channel.fetch_message(int(existing_id_raw))
            await msg.edit(
                content=content,
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            await self._publish_weekly_speakers_message(is_nl=is_nl)
        except Exception:
            log.warning("PartnerFinder: could not update hub embed is_nl=%s", is_nl)

    async def publish_hub(
        self,
        *,
        is_nl: bool = False,
        force_new: bool = False,
        weekly_ping: bool = False,
    ) -> bool:
        kv_key = KV_NL_HUB_MSG_ID if is_nl else KV_EN_HUB_MSG_ID
        guild_id = self.dutch_guild_id if is_nl else self.guild_id

        if guild_id is None:
            return False

        channel = await self._fetch_partner_channel(is_nl=is_nl)
        if channel is None:
            return False

        self._clean_expired(is_nl)
        count = len(self._pool(is_nl))
        embed = build_nl_embed(count) if is_nl else build_en_embed(count)
        view = PartnerHubViewNL(finder=self) if is_nl else PartnerHubView(finder=self)
        content = _hub_content(is_nl=is_nl, weekly_ping=weekly_ping)
        allowed_mentions = (
            discord.AllowedMentions(roles=True)
            if weekly_ping and not is_nl
            else discord.AllowedMentions.none()
        )

        existing_id_raw = await self.repo.kv_get(guild_id, kv_key)
        if existing_id_raw and not force_new:
            try:
                msg = await channel.fetch_message(int(existing_id_raw))
                await msg.edit(
                    content=content,
                    embed=embed,
                    view=view,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                await self._publish_weekly_speakers_message(is_nl=is_nl)
                log.info("PartnerFinder: updated hub message %s is_nl=%s", existing_id_raw, is_nl)
                return True
            except Exception:
                log.warning("PartnerFinder: could not edit hub message, recreating is_nl=%s", is_nl)

        try:
            sent = await channel.send(
                content=content,
                embed=embed,
                view=view,
                allowed_mentions=allowed_mentions,
            )
            await self.repo.kv_set(guild_id, kv_key, str(sent.id))
            await self._publish_weekly_speakers_message(is_nl=is_nl)
            log.info("PartnerFinder: posted hub message %s is_nl=%s", sent.id, is_nl)
            try:
                await sent.pin()
            except discord.Forbidden:
                log.warning("PartnerFinder: missing pin permission channel=%s", channel.id)
            except Exception:
                log.warning("PartnerFinder: could not pin hub message")
            if force_new and existing_id_raw:
                try:
                    await self._delete_old_hub_message(channel, message_id=int(existing_id_raw))
                except ValueError:
                    pass
            return True
        except Exception:
            log.exception("PartnerFinder: failed to post hub message is_nl=%s", is_nl)
            return False
