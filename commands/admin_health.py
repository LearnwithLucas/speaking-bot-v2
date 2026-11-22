from __future__ import annotations

import datetime as dt
import logging
import time
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord

from commands.admin_check import setup as setup_admin_check
from jobs.cafe_hour import summarize_sessions
from commands.admin_refresh import ADMIN_LOGS_CHANNEL_ID, ADMIN_TESTING_CHANNEL_ID

log = logging.getLogger(__name__)


def _amsterdam_now() -> dt.datetime:
    try:
        return dt.datetime.now(tz=ZoneInfo("Europe/Amsterdam"))
    except ZoneInfoNotFoundError:
        return dt.datetime.now()


def _period_start_epoch(days: int) -> int:
    now = _amsterdam_now()
    start = now - dt.timedelta(days=days)
    return int(start.timestamp())


def _format_duration(seconds: int) -> str:
    minutes = max(0, int((seconds / 60.0) + 0.5))
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    remainder = minutes % 60
    if remainder == 0:
        return f"{hours}h"
    return f"{hours}h {remainder}m"


def _format_period(summary: dict[str, Any]) -> str:
    return (
        f"Voice users: **{summary['active_users']}**\n"
        f"Voice sessions: **{summary['sessions']}**\n"
        f"Voice time: **{_format_duration(summary['seconds'])}**\n"
        f"Partner profiles updated: **{summary['partner_profiles_updated']}**\n"
        f"New voice pairs: **{summary['new_voice_pairs']}**\n"
        f"Achievements awarded: **{summary['achievements_awarded']}**\n"
        f"Weekly recaps sent: **{summary['weekly_recaps_sent']}**\n"
        f"Win-back DMs sent: **{summary['inactivity_nudges_sent']}**"
    )


def _format_commands(summary: dict[str, Any]) -> str:
    rows = summary.get("commands", [])
    if not rows:
        return "No command usage recorded yet. This starts counting after this update."
    return "\n".join(
        f"`/{name}`: **{uses}** uses by **{unique}** member(s)"
        for name, uses, unique in rows
    )


async def _format_activation(bot: Any) -> str:
    """Share of new members with unmuted voice time in their first 7 days, per server."""
    now = int(time.time())
    servers = [("English", getattr(bot, "guild_id", None)), ("Dutch", getattr(bot, "dutch_guild_id", None))]
    lines = []
    for name, guild_id in servers:
        if not guild_id:
            continue
        try:
            in_voice, cohort = await bot.repo.new_member_voice_rate(guild_id, now)
        except Exception:
            log.exception("adminhealth: activation stat failed guild=%s", guild_id)
            continue
        if cohort == 0:
            lines.append(f"{name}: no members in the window yet")
        else:
            lines.append(f"{name}: **{in_voice / cohort:.0%}** ({in_voice} of {cohort})")
    lines.append("Members who joined 8 to 37 days ago. Unmuted voice only.")
    return "\n".join(lines)


async def _send_admin_log(bot: discord.Client, message: str) -> None:
    channel = bot.get_channel(ADMIN_LOGS_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(ADMIN_LOGS_CHANNEL_ID)
        except Exception:
            log.exception("adminhealth: could not fetch admin logs channel")
            return
    if not hasattr(channel, "send"):
        return
    try:
        await channel.send(message)
    except Exception:
        log.exception("adminhealth: failed to send admin log")


async def setup(bot: Any) -> None:
    @bot.tree.command(
        name="adminhealth",
        description="Show an admin-only community health summary.",
    )
    async def cmd_adminhealth(interaction: discord.Interaction) -> None:
        if int(getattr(interaction, "channel_id", 0) or 0) != ADMIN_TESTING_CHANNEL_ID:
            await interaction.response.send_message(
                "Use this in <#1205828956360548383> so admin actions stay in one place.",
                ephemeral=True,
            )
            return

        if interaction.guild_id is None:
            await interaction.response.send_message("Use this inside the server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            await bot.repo.command_usage_record(
                interaction.guild_id,
                interaction.user.id,
                "adminhealth",
                int(time.time()),
            )
        except Exception:
            log.exception("adminhealth: failed to record command usage")

        since_24h = _period_start_epoch(1)
        since_7d = _period_start_epoch(7)
        summary_24h = await bot.repo.community_health_summary(interaction.guild_id, since_24h)
        summary_7d = await bot.repo.community_health_summary(interaction.guild_id, since_7d)

        embed = discord.Embed(
            title="Community health",
            description=(
                "Admin-only summary. The counts are for the whole community. Nobody is ranked.\n"
                f"Currently in voice: **{summary_7d['active_now']}**"
            ),
        )
        embed.add_field(name="Last 24 hours", value=_format_period(summary_24h), inline=False)
        embed.add_field(name="Last 7 days", value=_format_period(summary_7d), inline=False)
        embed.add_field(
            name="New members in voice within 7 days",
            value=await _format_activation(bot),
            inline=False,
        )
        try:
            hosts = await bot.repo.host_invite_counts(bot.guild_id)
            embed.add_field(
                name="Conversation Hosts (English, all time)",
                value=f"Invites sent: **{hosts['sent']}**\nSaid yes: **{hosts['yes']}**\nApproved hosts: **{hosts['approved']}**",
                inline=False,
            )
        except Exception:
            log.exception("adminhealth: host counts failed")
        try:
            shout = await bot.repo.milestone_shoutout_counts(bot.guild_id, _period_start_epoch(7))
            embed.add_field(
                name="Milestone shout-outs (English)",
                value=f"Posted this week: **{shout['posted']}**\nMembers opted out: **{shout['opted_out']}**",
                inline=False,
            )
        except Exception:
            log.exception("adminhealth: shout-out counts failed")
        weekly_tip = getattr(bot, "weekly_tip", None)
        if weekly_tip is not None:
            from jobs.weekly_tip import TIPS

            last = await weekly_tip.last_posted()
            nxt = TIPS[await weekly_tip.next_index()][0]
            embed.add_field(
                name="Weekly tip",
                value=(
                    f"Last posted: **{TIPS[last[2]][0]}** on <t:{last[1]}:D>" if last else "Last posted: none yet"
                ) + f"\nNext: **{nxt}** (Mondays 12:00)",
                inline=False,
            )
        if getattr(getattr(bot, "server_tag", None), "enabled", False):
            try:
                from jobs.milestones import MILESTONE_START_KV

                raw_start = await bot.repo.kv_get(bot.guild_id, MILESTONE_START_KV)
                tag = await bot.repo.tag_stats(bot.guild_id, _period_start_epoch(7), int(raw_start or 0))
                share = (
                    f"{tag['speakers_1h_wearing'] / tag['speakers_1h']:.0%} ({tag['speakers_1h_wearing']} of {tag['speakers_1h']})"
                    if tag["speakers_1h"]
                    else "no 1h+ speakers yet"
                )
                embed.add_field(
                    name="Server Tag (CAFE)",
                    value=(
                        f"Wearing it now: **{tag['wearing']}**\n"
                        f"New wearers this week: **{tag['new_week']}**\n"
                        f"1h+ speakers wearing it: **{share}**"
                    ),
                    inline=False,
                )
            except Exception:
                log.exception("adminhealth: server tag stats failed")
        if getattr(getattr(bot, "cafe_hour", None), "enabled", False):
            try:
                sessions = await bot.repo.cafe_hour_sessions_since(bot.guild_id, int(time.time()) - 14 * 86400)
                embed.add_field(name="Café Hour (last 14 days)", value=summarize_sessions(sessions), inline=False)
            except Exception:
                log.exception("adminhealth: café hour summary failed")
        embed.add_field(name="Command usage, last 7 days", value=_format_commands(summary_7d), inline=False)
        embed.set_footer(text="Look at trends. Quiet learners count too.")

        await interaction.followup.send(embed=embed, ephemeral=True)

        await _send_admin_log(
            bot,
            f"Admin health summary viewed by {interaction.user.mention} in <#1205828956360548383>.",
        )

    @bot.tree.command(
        name="milestoneroles_backfill",
        description="Admin: give milestone roles to members who already passed a threshold.",
    )
    async def cmd_milestoneroles_backfill(interaction: discord.Interaction) -> None:
        if int(getattr(interaction, "channel_id", 0) or 0) != ADMIN_TESTING_CHANNEL_ID:
            await interaction.response.send_message(
                "Use this in <#1205828956360548383> so admin actions stay in one place.",
                ephemeral=True,
            )
            return
        milestones = getattr(getattr(bot, "tracker", None), "milestones", None)
        if milestones is None:
            await interaction.response.send_message("Milestones aren't running yet. Try again in a moment.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        checked, changed = await milestones.backfill_roles()
        await interaction.followup.send(
            f"Checked **{checked}** members with voice time since the milestone start. Roles changed for **{changed}**. No DMs sent.",
            ephemeral=True,
        )
        await _send_admin_log(bot, f"Milestone role backfill by {interaction.user.mention}: {checked} checked, {changed} changed.")

    @bot.tree.command(
        name="milestoneroles_cleanup",
        description="Admin: members with 2+ milestone roles keep only the highest.",
    )
    async def cmd_milestoneroles_cleanup(interaction: discord.Interaction) -> None:
        if int(getattr(interaction, "channel_id", 0) or 0) != ADMIN_TESTING_CHANNEL_ID:
            await interaction.response.send_message(
                "Use this in <#1205828956360548383> so admin actions stay in one place.",
                ephemeral=True,
            )
            return
        milestones = getattr(getattr(bot, "tracker", None), "milestones", None)
        if milestones is None:
            await interaction.response.send_message("Milestones aren't running yet. Try again in a moment.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        checked, fixed, removed = await milestones.cleanup_roles()
        await interaction.followup.send(
            f"Checked **{checked}** members. Fixed **{fixed}**. Removed **{removed}** extra milestone roles. No DMs or posts sent.",
            ephemeral=True,
        )
        await _send_admin_log(
            bot, f"Milestone role cleanup by {interaction.user.mention}: {checked} checked, {fixed} fixed, {removed} removed."
        )

    async def _admin_only(interaction: discord.Interaction) -> bool:
        if int(getattr(interaction, "channel_id", 0) or 0) != ADMIN_TESTING_CHANNEL_ID:
            await interaction.response.send_message(
                "Use this in <#1205828956360548383> so admin actions stay in one place.",
                ephemeral=True,
            )
            return False
        if not getattr(getattr(bot, "cafe_hour", None), "enabled", False):
            await interaction.response.send_message(
                "Café Hour is off. Set CAFE_HOUR_ENABLED=true and the other CAFE_HOUR_ values on Render.",
                ephemeral=True,
            )
            return False
        return True

    @bot.tree.command(name="cafehour_status", description="Admin: next Café Hour, today's topic and recent sessions.")
    async def cmd_cafehour_status(interaction: discord.Interaction) -> None:
        if not await _admin_only(interaction):
            return
        info = await bot.cafe_hour.status()
        start = info["next"]
        lines = [
            f"Next session: <t:{int(start.timestamp())}:F> (<t:{int(start.timestamp())}:R>)"
            + (" **(skipped)**" if info["skipped"] else ""),
            f"Topic: **{info['topic'] or 'picked 15 minutes before the start'}**",
            "",
            "Last sessions:",
        ]
        if info["recent"]:
            lines += [
                f"{s['day']}: **{s['unique_speakers']}** speakers, {s['voice_minutes']} min"
                + (f", {s['interested']} interested" if s["interested"] is not None else "")
                for s in info["recent"]
            ]
        else:
            lines.append("None yet.")
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @bot.tree.command(name="cafehour_skip", description="Admin: skip the next Café Hour (deletes its event, no ping).")
    async def cmd_cafehour_skip(interaction: discord.Interaction) -> None:
        if not await _admin_only(interaction):
            return
        start = await bot.cafe_hour.skip_next()
        await interaction.response.send_message(
            f"Skipped the session on <t:{int(start.timestamp())}:F>. The next one gets its event after that.",
            ephemeral=True,
        )
        await _send_admin_log(bot, f"Café Hour on <t:{int(start.timestamp())}:F> skipped by {interaction.user.mention}.")

    @bot.tree.command(name="cafehour_now", description="Admin: preview the Café Hour reminder and topic here (no ping).")
    async def cmd_cafehour_now(interaction: discord.Interaction) -> None:
        if not await _admin_only(interaction):
            return
        reminder, topic, followup = await bot.cafe_hour.preview()
        await interaction.response.send_message(
            "**Test run.** This is what members would see. Nothing was posted elsewhere.",
            ephemeral=False,
        )
        none = discord.AllowedMentions.none()
        await interaction.followup.send(f"**Reminder (#looking-for-a-partner, 15 min before):**\n{reminder}", allowed_mentions=none)
        await interaction.followup.send(f"**Topic (Open Conversation chat, at the start):**\n{topic}", allowed_mentions=none)
        await interaction.followup.send(f"**Follow-up (after 30 min):**\n{followup}", allowed_mentions=none)

    async def _admin_channel(interaction: discord.Interaction) -> bool:
        if int(getattr(interaction, "channel_id", 0) or 0) != ADMIN_TESTING_CHANNEL_ID:
            await interaction.response.send_message(
                "Use this in <#1205828956360548383> so admin actions stay in one place.",
                ephemeral=True,
            )
            return False
        return True

    @bot.tree.command(name="update_dm_preview", description="Admin: show who would get the update DM and the message. Sends nothing.")
    async def cmd_update_dm_preview(interaction: discord.Interaction) -> None:
        if not await _admin_channel(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        members = await bot.update_dm.recipients()
        await interaction.followup.send(
            f"**{len(members)}** members would get it (voice time in the last 60 days, still in the server, "
            f"not new this week, not opted out, not sent before). Nothing was sent.\n\n"
            f"Message (with your name):\n>>> {bot.update_dm.text_for(interaction.user)}",
            ephemeral=True,
        )

    @bot.tree.command(name="update_dm_send", description="Admin: send the one-off update DM slowly in the background.")
    async def cmd_update_dm_send(interaction: discord.Interaction) -> None:
        if not await _admin_channel(interaction):
            return
        if bot.update_dm.running:
            await interaction.response.send_message("It's already sending. The summary will appear in admin-logs.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        members = await bot.update_dm.recipients()
        if not members:
            await interaction.followup.send("Nobody left to send it to. It never goes to the same member twice.", ephemeral=True)
            return

        async def report(text: str) -> None:
            await _send_admin_log(bot, text)

        bot.update_dm.start(members, report)
        minutes = max(1, round(len(members) * 4 / 60))
        await interaction.followup.send(
            f"Sending to **{len(members)}** members, one every 3 to 5 seconds (about {minutes} min). "
            "The summary will appear in admin-logs.",
            ephemeral=True,
        )
        await _send_admin_log(bot, f"Update DM started by {interaction.user.mention} for {len(members)} members.")

    @bot.tree.command(name="weeklytip_now", description="Admin: post the next weekly tip in announcements now.")
    async def cmd_weeklytip_now(interaction: discord.Interaction) -> None:
        if not await _admin_channel(interaction):
            return
        from jobs.weekly_tip import TIPS

        index = await bot.weekly_tip.post_next()
        if index is None:
            await interaction.response.send_message("Couldn't post: announcements channel not found.", ephemeral=True)
            return
        await interaction.response.send_message(f"Posted tip {index + 1}: **{TIPS[index][0]}**.", ephemeral=True)

    @bot.tree.command(name="weeklytip_skip", description="Admin: skip the next tip in the rotation without posting it.")
    async def cmd_weeklytip_skip(interaction: discord.Interaction) -> None:
        if not await _admin_channel(interaction):
            return
        from jobs.weekly_tip import TIPS

        index = await bot.weekly_tip.skip_next()
        nxt = TIPS[await bot.weekly_tip.next_index()][0]
        await interaction.response.send_message(
            f"Skipped tip {index + 1}: **{TIPS[index][0]}**. Next Monday posts **{nxt}**.", ephemeral=True
        )

    await setup_admin_check(bot)
