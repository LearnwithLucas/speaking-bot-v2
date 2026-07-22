from __future__ import annotations

import logging
import os
import time
from pathlib import PurePosixPath
from typing import Any

import discord

from commands.admin_refresh import ADMIN_LOGS_CHANNEL_ID, ADMIN_TESTING_CHANNEL_ID
from commands.ask_jerry import ASK_JERRY_CHANNEL_ID, NL_ASK_JERRY_CHANNEL_ID
from commands.chat_jerry import (
    CHAT_WITH_JERRY_CHANNEL_ID,
    EN_DAILY_CHAT_CHANNEL_ID,
    NL_DAILY_CHAT_CHANNEL_ID,
)
from commands.dictionary import EN_VOCAB_CHANNEL_ID
from commands.testimonials import EN_SUCCESS_CHANNEL_ID, NL_SUCCESS_CHANNEL_ID
from jobs import private_lessons as lesson_config
from jobs.nudges import NL_ANNOUNCEMENTS_CHANNEL_ID
from jobs.partner_finder import EN_LOOKING_CHANNEL_ID, NL_LOOKING_CHANNEL_ID
from jobs.partner_finder import I_WANT_TO_SPEAK_ROLE_ID
from jobs.word_of_the_day import EN_WOTD_CHANNEL_ID, NL_WOTD_CHANNEL_ID

log = logging.getLogger(__name__)


TEXT_CHANNELS: tuple[tuple[str, int, bool], ...] = (
    ("admin-testing", ADMIN_TESTING_CHANNEL_ID, False),
    ("admin-logs", ADMIN_LOGS_CHANNEL_ID, False),
    ("English private lessons", lesson_config.EN_PRIVATE_CHANNEL_ID, True),
    ("Dutch private lessons", lesson_config.NL_PRIVATE_CHANNEL_ID, True),
    ("English supported speaking", lesson_config.EN_SUPPORTED_CHANNEL_ID, True),
    ("Dutch supported speaking", lesson_config.NL_SUPPORTED_CHANNEL_ID, True),
    ("English vocabulary", EN_VOCAB_CHANNEL_ID, True),
    ("English Ask Jerry", ASK_JERRY_CHANNEL_ID, True),
    ("Dutch Ask Jerry", NL_ASK_JERRY_CHANNEL_ID, True),
    ("Chat with Jerry", CHAT_WITH_JERRY_CHANNEL_ID, True),
    ("English daily chat question", EN_DAILY_CHAT_CHANNEL_ID, False),
    ("Dutch daily chat question", NL_DAILY_CHAT_CHANNEL_ID, False),
    ("English partner finder", EN_LOOKING_CHANNEL_ID, True),
    ("Dutch partner finder", NL_LOOKING_CHANNEL_ID, True),
    ("English testimonials", EN_SUCCESS_CHANNEL_ID, True),
    ("Dutch testimonials", NL_SUCCESS_CHANNEL_ID, True),
    ("English word of the day", EN_WOTD_CHANNEL_ID, False),
    ("Dutch word of the day", NL_WOTD_CHANNEL_ID, False),
    ("Dutch announcements", NL_ANNOUNCEMENTS_CHANNEL_ID, False),
)


def _is_render() -> bool:
    return bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID") or os.getenv("RENDER_EXTERNAL_HOSTNAME"))


def _db_status(bot: Any) -> tuple[str, str]:
    repo = getattr(bot, "repo", None)
    db_path = str(getattr(repo, "db_path", "unknown"))
    if _is_render() and not db_path.startswith("/data/"):
        return "WARN", f"DB path `{db_path}` is not under `/data`. Use `DB_PATH=/data/botlab_speaking.sqlite` on Render."
    if db_path == "botlab_speaking.sqlite":
        return "WARN", "DB path is the default local filename. On Render, set `DB_PATH=/data/botlab_speaking.sqlite`."
    if PurePosixPath(db_path).is_absolute() and db_path.startswith("/data/"):
        return "OK", f"DB path `{db_path}` looks persistent for Render."
    return "OK", f"DB path is `{db_path}`."


def _intent_lines(bot: discord.Client) -> list[str]:
    intents = getattr(bot, "intents", None)
    if intents is None:
        return ["WARN intents unavailable"]
    return [
        f"{'OK' if intents.message_content else 'WARN'} message content requested",
        f"{'OK' if intents.members else 'WARN'} members intent requested",
        f"{'OK' if intents.voice_states else 'WARN'} voice state intent requested",
    ]


def _speaking_role_status(bot: Any) -> str:
    guild_id = getattr(bot, "guild_id", None)
    guild = bot.get_guild(guild_id) if guild_id is not None else None
    if guild is None:
        return f"WARN English guild unavailable, cannot inspect role `{I_WANT_TO_SPEAK_ROLE_ID}`"

    role = guild.get_role(I_WANT_TO_SPEAK_ROLE_ID)
    if role is None:
        return f"FAIL role `{I_WANT_TO_SPEAK_ROLE_ID}` not found"

    me = guild.me
    if me is None:
        return "WARN cannot inspect bot member role permissions"
    if not me.guild_permissions.manage_roles:
        return "FAIL bot is missing Manage Roles permission"
    if role >= me.top_role:
        return "FAIL bot top role must be above the I want to speak role"
    if not role.mentionable and not me.guild_permissions.mention_everyone:
        return (
            f"WARN role found and manageable: `{role.name}`, "
            "but role mentions may not notify unless the role is mentionable."
        )
    return f"OK role found and manageable: `{role.name}`"


def _missing_permissions(channel: discord.TextChannel | discord.Thread, bot: discord.Client, *, needs_manage: bool) -> list[str]:
    guild = getattr(channel, "guild", None)
    me = guild.me if guild is not None else None
    if me is None:
        return ["cannot inspect permissions"]

    perms = channel.permissions_for(me)
    required = [
        ("View Channel", perms.view_channel),
        ("Send Messages", perms.send_messages),
        ("Read Message History", perms.read_message_history),
        ("Embed Links", perms.embed_links),
    ]
    if needs_manage:
        required.append(("Manage Messages", perms.manage_messages))

    return [name for name, ok in required if not ok]


async def _channel_line(bot: discord.Client, label: str, channel_id: int, needs_manage: bool) -> str:
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            return f"FAIL {label}: cannot fetch <#{channel_id}>"

    if not isinstance(channel, (discord.TextChannel, discord.Thread)):
        return f"WARN {label}: not a text channel"

    missing = _missing_permissions(channel, bot, needs_manage=needs_manage)
    if missing:
        return f"WARN {label}: missing {', '.join(missing)}"
    return f"OK {label}"


def _chunk_lines(lines: list[str], *, limit: int = 950) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in lines:
        extra = len(line) + 1
        if current and current_len + extra > limit:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += extra
    if current:
        chunks.append("\n".join(current))
    return chunks


async def _send_admin_log(bot: discord.Client, message: str) -> None:
    channel = bot.get_channel(ADMIN_LOGS_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(ADMIN_LOGS_CHANNEL_ID)
        except Exception:
            log.exception("admincheck: could not fetch admin logs channel")
            return
    if not hasattr(channel, "send"):
        return
    try:
        await channel.send(message)
    except Exception:
        log.exception("admincheck: failed to send admin log")


async def setup(bot: Any) -> None:
    @bot.tree.command(
        name="admincheck",
        description="Check speaking bot setup, Render DB path, intents and channel permissions.",
    )
    async def cmd_admincheck(interaction: discord.Interaction) -> None:
        if int(getattr(interaction, "channel_id", 0) or 0) != ADMIN_TESTING_CHANNEL_ID:
            await interaction.response.send_message(
                "Use this in <#1205828956360548383> so admin actions stay in one place.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            if interaction.guild_id is not None:
                await bot.repo.command_usage_record(
                    interaction.guild_id,
                    interaction.user.id,
                    "admincheck",
                    int(time.time()),
                )
        except Exception:
            log.exception("admincheck: failed to record command usage")

        db_level, db_message = _db_status(bot)
        lines = [await _channel_line(bot, label, channel_id, needs_manage) for label, channel_id, needs_manage in TEXT_CHANNELS]
        issue_count = sum(1 for line in lines if not line.startswith("OK "))

        embed = discord.Embed(
            title="Speaking Bot Setup Check",
            description=(
                "Admin-only deployment and permission check.\n"
                f"Channel issues found: **{issue_count}**"
            ),
        )
        embed.add_field(name="Database", value=f"{db_level} {db_message}", inline=False)
        embed.add_field(name="Requested Intents", value="\n".join(_intent_lines(bot)), inline=False)
        embed.add_field(name="I Want To Speak Role", value=_speaking_role_status(bot), inline=False)
        embed.add_field(
            name="Guilds",
            value=(
                f"OK English guild configured: `{getattr(bot, 'guild_id', 'unknown')}`\n"
                f"{'OK' if getattr(bot, 'dutch_guild_id', None) else 'WARN'} Dutch guild configured: `{getattr(bot, 'dutch_guild_id', None)}`"
            ),
            inline=False,
        )

        for index, chunk in enumerate(_chunk_lines(lines), start=1):
            name = "Channels" if index == 1 else f"Channels {index}"
            embed.add_field(name=name, value=chunk, inline=False)

        embed.set_footer(text="Portal privileged intents still need to be enabled in Discord Developer Portal.")
        await interaction.followup.send(embed=embed, ephemeral=True)
        await _send_admin_log(
            bot,
            f"Admin setup check viewed by {interaction.user.mention} in <#1205828956360548383>. Issues: {issue_count}.",
        )
