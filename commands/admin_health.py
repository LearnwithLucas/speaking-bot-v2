from __future__ import annotations

import datetime as dt
import logging
import time
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord

from commands.admin_check import setup as setup_admin_check
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
        f"Inactivity nudges sent: **{summary['inactivity_nudges_sent']}**"
    )


def _format_commands(summary: dict[str, Any]) -> str:
    rows = summary.get("commands", [])
    if not rows:
        return "No command usage recorded yet. This starts counting after this update."
    return "\n".join(
        f"`/{name}`: **{uses}** uses by **{unique}** member(s)"
        for name, uses, unique in rows
    )


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
            title="Community Health",
            description=(
                "Admin-only summary. Counts are community-level, not a member ranking.\n"
                f"Currently in voice: **{summary_7d['active_now']}**"
            ),
        )
        embed.add_field(name="Last 24 Hours", value=_format_period(summary_24h), inline=False)
        embed.add_field(name="Last 7 Days", value=_format_period(summary_7d), inline=False)
        embed.add_field(name="Command Usage - 7 Days", value=_format_commands(summary_7d), inline=False)
        embed.set_footer(text="Use trends, not individual pressure. Quiet learners count too.")

        await interaction.followup.send(embed=embed, ephemeral=True)

        await _send_admin_log(
            bot,
            f"Admin health summary viewed by {interaction.user.mention} in <#1205828956360548383>.",
        )

    await setup_admin_check(bot)
