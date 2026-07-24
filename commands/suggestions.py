from __future__ import annotations

import datetime as dt
import logging
from typing import Any

import discord
from discord.ext import commands

log = logging.getLogger(__name__)

SUGGESTION_BOX_CHANNEL_ID = 1530192789529165855
ADMIN_SUGGESTIONS_CHANNEL_ID = 1530193017053642805
KV_SUGGESTION_BOX_MSG = "suggestion_box_message_id_v1"


def build_suggestion_box_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Suggestion box",
        description=(
            "Have an idea for the community, the bot, lessons, channels, or events?\n\n"
            "Press the button below and send it privately to the team."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Suggestions are sent privately to the admins.")
    return embed


class SuggestionModal(discord.ui.Modal, title="Send a suggestion"):
    suggestion = discord.ui.TextInput(
        label="Your suggestion",
        placeholder="Write your idea here...",
        style=discord.TextStyle.paragraph,
        min_length=3,
        max_length=1200,
        required=True,
    )

    def __init__(self, *, publisher: "SuggestionBoxPublisher") -> None:
        super().__init__()
        self._publisher = publisher

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self._publisher.submit_suggestion(
            interaction=interaction,
            suggestion=str(self.suggestion.value).strip(),
        )


class SuggestionBoxView(discord.ui.View):
    def __init__(self, *, publisher: "SuggestionBoxPublisher | None" = None) -> None:
        super().__init__(timeout=None)
        self._publisher = publisher

    @discord.ui.button(
        label="Send a suggestion",
        style=discord.ButtonStyle.primary,
        custom_id="suggestion_box:send:v1",
    )
    async def send_suggestion(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if self._publisher is None:
            await interaction.response.send_message(
                "Suggestion box is not ready yet. Try again in a moment.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(SuggestionModal(publisher=self._publisher))


class SuggestionBoxPublisher:
    def __init__(self, *, bot: discord.Client, repo: Any) -> None:
        self._bot = bot
        self._repo = repo

    async def _get_text_channel(self, channel_id: int) -> discord.TextChannel | None:
        channel = self._bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self._bot.fetch_channel(channel_id)
            except Exception:
                log.warning("SuggestionBox: could not fetch channel %s", channel_id)
                return None

        if not isinstance(channel, discord.TextChannel):
            log.warning("SuggestionBox: channel %s is not a text channel", channel_id)
            return None
        return channel

    async def publish(self, guild_id: int) -> None:
        channel = await self._get_text_channel(SUGGESTION_BOX_CHANNEL_ID)
        if channel is None:
            return

        embed = build_suggestion_box_embed()
        view = SuggestionBoxView(publisher=self)

        existing_id_raw = await self._repo.kv_get(guild_id, KV_SUGGESTION_BOX_MSG)
        if existing_id_raw:
            try:
                msg = await channel.fetch_message(int(existing_id_raw))
                await msg.edit(
                    content=None,
                    embed=embed,
                    view=view,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                log.info("SuggestionBox: updated hub message %s", existing_id_raw)
                return
            except Exception:
                log.warning("SuggestionBox: could not edit hub message, recreating")

        try:
            sent = await channel.send(
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            await self._repo.kv_set(guild_id, KV_SUGGESTION_BOX_MSG, str(sent.id))
            log.info("SuggestionBox: posted hub message %s", sent.id)
            try:
                await sent.pin(reason="SpeakingBot: suggestion box")
            except discord.Forbidden:
                log.warning("SuggestionBox: missing pin permission channel=%s", channel.id)
            except Exception:
                log.warning("SuggestionBox: could not pin hub message")
        except Exception:
            log.exception("SuggestionBox: failed to publish hub")

    async def submit_suggestion(
        self,
        *,
        interaction: discord.Interaction,
        suggestion: str,
    ) -> None:
        if not suggestion:
            await interaction.response.send_message(
                "Please write a suggestion before sending.",
                ephemeral=True,
            )
            return

        admin_channel = await self._get_text_channel(ADMIN_SUGGESTIONS_CHANNEL_ID)
        if admin_channel is None:
            await interaction.response.send_message(
                "I could not send your suggestion right now. Please tell Lucas to check the bot logs.",
                ephemeral=True,
            )
            return

        user = interaction.user
        embed = discord.Embed(
            title="New community suggestion",
            description=suggestion,
            color=discord.Color.green(),
            timestamp=dt.datetime.now(dt.timezone.utc),
        )
        embed.add_field(
            name="From",
            value=f"{user.mention}\n`{user.id}`",
            inline=False,
        )
        if interaction.guild is not None:
            embed.add_field(
                name="Server",
                value=f"{interaction.guild.name}\n`{interaction.guild.id}`",
                inline=True,
            )
        embed.add_field(
            name="Source",
            value=f"<#{SUGGESTION_BOX_CHANNEL_ID}>",
            inline=True,
        )

        try:
            await admin_channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            await interaction.response.send_message(
                "Thanks. Your suggestion was sent privately to the admins.",
                ephemeral=True,
            )
            log.info("SuggestionBox: submitted suggestion user=%s", user.id)
        except Exception:
            log.exception("SuggestionBox: failed to submit suggestion user=%s", user.id)
            await interaction.response.send_message(
                "Something went wrong while sending your suggestion. Try again in a moment.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot, repo: Any, *, guild_id: int) -> SuggestionBoxPublisher:
    publisher = SuggestionBoxPublisher(bot=bot, repo=repo)
    bot.add_view(SuggestionBoxView(publisher=publisher))
    log.info("SuggestionBox loaded.")
    return publisher
