from __future__ import annotations

import logging
from typing import Any, Awaitable

import discord

from commands.ask_jerry_summer import apply_ask_jerry_summer_copy
from commands.chat_jerry import CHAT_WITH_JERRY_CHANNEL_ID, KV_CHAT_JERRY_HUB_MSG, ChatJerryPublisher
from commands.dictionary import VocabPublisher
from commands.suggestions import (
    KV_SUGGESTION_BOX_MSG,
    SUGGESTION_BOX_CHANNEL_ID,
    SuggestionBoxPublisher,
)
from jobs import private_lessons as lesson_config
from jobs.private_lessons_summer import PrivateLessonsPublisher

log = logging.getLogger(__name__)

ADMIN_TESTING_CHANNEL_ID = 1205828956360548383
ADMIN_LOGS_CHANNEL_ID = 1340397297053339719

# Keep Ask Jerry's long FAQ copy aligned without rewriting the full FAQ module.
apply_ask_jerry_summer_copy()


async def _send_admin_log(bot: discord.Client, message: str) -> None:
    channel = bot.get_channel(ADMIN_LOGS_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(ADMIN_LOGS_CHANNEL_ID)
        except Exception:
            log.exception("adminrefresh: could not fetch admin logs channel")
            return

    if not hasattr(channel, "send"):
        log.warning("adminrefresh: admin logs target is not messageable")
        return

    try:
        await channel.send(message)
    except Exception:
        log.exception("adminrefresh: failed to send admin log")


async def _verify_managed_message(
    *,
    bot: Any,
    channel_id: int,
    kv_key: str,
) -> None:
    channel = bot.get_channel(channel_id)
    if channel is None:
        channel = await bot.fetch_channel(channel_id)

    if not isinstance(channel, discord.TextChannel):
        raise RuntimeError(f"Channel {channel_id} is not a text channel")

    message_id = await bot.repo.kv_get(channel.guild.id, kv_key)
    if not message_id:
        raise RuntimeError(f"No managed message id stored for channel {channel_id}")

    await channel.fetch_message(int(message_id))


async def _publish_and_verify_message(
    *,
    bot: Any,
    work: Awaitable[None],
    channel_id: int,
    kv_key: str,
) -> None:
    await work
    await _verify_managed_message(bot=bot, channel_id=channel_id, kv_key=kv_key)


async def _run_step(
    *,
    label: str,
    work: Awaitable[None],
    refreshed: list[str],
    failed: list[str],
) -> None:
    try:
        await work
        refreshed.append(label)
    except Exception:
        log.exception("adminrefresh: %s failed", label)
        failed.append(label)


async def setup(bot: Any) -> None:
    @bot.tree.command(
        name="adminrefresh",
        description="Refresh managed speaking bot posts from admin-testing",
    )
    async def cmd_adminrefresh(interaction: discord.Interaction) -> None:
        if int(getattr(interaction, "channel_id", 0) or 0) != ADMIN_TESTING_CHANNEL_ID:
            await interaction.response.send_message(
                "Use this in <#1205828956360548383> so admin actions stay in one place.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        await _send_admin_log(
            bot,
            f"Speaking bot admin refresh started by {interaction.user.mention} in <#1205828956360548383>.",
        )

        refreshed: list[str] = []
        failed: list[str] = []
        skipped: list[str] = []

        lessons = PrivateLessonsPublisher(bot=bot, repo=bot.repo)
        await _run_step(
            label="English private lessons",
            work=_publish_and_verify_message(
                bot=bot,
                work=lessons.publish_english(),
                channel_id=lesson_config.EN_PRIVATE_CHANNEL_ID,
                kv_key=lesson_config.KV_EN_PRIVATE_MSG,
            ),
            refreshed=refreshed,
            failed=failed,
        )
        await _run_step(
            label="Dutch private lessons",
            work=_publish_and_verify_message(
                bot=bot,
                work=lessons.publish_dutch(),
                channel_id=lesson_config.NL_PRIVATE_CHANNEL_ID,
                kv_key=lesson_config.KV_NL_PRIVATE_MSG,
            ),
            refreshed=refreshed,
            failed=failed,
        )
        await _run_step(
            label="English supported speaking",
            work=_publish_and_verify_message(
                bot=bot,
                work=lessons.publish_en_supported(),
                channel_id=lesson_config.EN_SUPPORTED_CHANNEL_ID,
                kv_key=lesson_config.KV_EN_SUPPORTED_MSG,
            ),
            refreshed=refreshed,
            failed=failed,
        )
        await _run_step(
            label="Dutch supported speaking",
            work=_publish_and_verify_message(
                bot=bot,
                work=lessons.publish_nl_supported(),
                channel_id=lesson_config.NL_SUPPORTED_CHANNEL_ID,
                kv_key=lesson_config.KV_NL_SUPPORTED_MSG,
            ),
            refreshed=refreshed,
            failed=failed,
        )

        vocab = VocabPublisher(bot=bot, repo=bot.repo)
        await _run_step(
            label="English vocabulary hub",
            work=vocab.publish_english(),
            refreshed=refreshed,
            failed=failed,
        )
        skipped.append("Dutch vocabulary hub (not configured)")

        ask_jerry = getattr(bot, "_ask_jerry_publisher", None)
        if ask_jerry is not None:
            await _run_step(
                label="English Ask Jerry hub",
                work=ask_jerry.publish(bot.guild_id),
                refreshed=refreshed,
                failed=failed,
            )
            if bot.dutch_guild_id:
                await _run_step(
                    label="Dutch Ask Jerry hub",
                    work=ask_jerry.publish_dutch(bot.dutch_guild_id),
                    refreshed=refreshed,
                    failed=failed,
                )
        else:
            skipped.append("Ask Jerry hub")

        chat_jerry = getattr(bot, "_chat_jerry_publisher", None)
        if chat_jerry is None:
            chat_jerry = ChatJerryPublisher(bot=bot, repo=bot.repo)
        await _run_step(
            label="Chat with Jerry hub",
            work=_publish_and_verify_message(
                bot=bot,
                work=chat_jerry.publish(bot.guild_id),
                channel_id=CHAT_WITH_JERRY_CHANNEL_ID,
                kv_key=KV_CHAT_JERRY_HUB_MSG,
            ),
            refreshed=refreshed,
            failed=failed,
        )

        suggestion_box = getattr(bot, "_suggestion_publisher", None)
        if suggestion_box is None:
            suggestion_box = SuggestionBoxPublisher(bot=bot, repo=bot.repo)
        await _run_step(
            label="Suggestion box",
            work=_publish_and_verify_message(
                bot=bot,
                work=suggestion_box.publish(bot.guild_id),
                channel_id=SUGGESTION_BOX_CHANNEL_ID,
                kv_key=KV_SUGGESTION_BOX_MSG,
            ),
            refreshed=refreshed,
            failed=failed,
        )

        testimonial = getattr(bot, "_testimonial_publisher", None)
        if testimonial is not None:
            await _run_step(
                label="English testimonials hub",
                work=testimonial.publish_hub(is_nl=False),
                refreshed=refreshed,
                failed=failed,
            )
            if bot.dutch_guild_id:
                await _run_step(
                    label="Dutch testimonials hub",
                    work=testimonial.publish_hub(is_nl=True),
                    refreshed=refreshed,
                    failed=failed,
                )
        else:
            skipped.append("testimonials hub")

        partner_finder = getattr(bot, "_partner_finder", None)
        if partner_finder is not None:
            await _run_step(
                label="English partner finder hub",
                work=partner_finder.publish_hub(is_nl=False),
                refreshed=refreshed,
                failed=failed,
            )
            if bot.dutch_guild_id:
                await _run_step(
                    label="Dutch partner finder hub",
                    work=partner_finder.publish_hub(is_nl=True),
                    refreshed=refreshed,
                    failed=failed,
                )
        else:
            skipped.append("partner finder hub")

        status = "Admin refresh complete." if not failed else "Admin refresh finished with issues."
        details = [status]
        if refreshed:
            details.append("Refreshed: " + ", ".join(refreshed))
        if skipped:
            details.append("Skipped: " + ", ".join(skipped))
        if failed:
            details.append("Failed: " + ", ".join(failed))

        message = "\n".join(details)
        await interaction.followup.send(message, ephemeral=True)
        await _send_admin_log(bot, message)
