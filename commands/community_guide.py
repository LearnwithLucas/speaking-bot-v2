from __future__ import annotations

from typing import Any

import discord

from commands.ask_jerry import ASK_JERRY_CHANNEL_ID, NL_ASK_JERRY_CHANNEL_ID
from commands.dictionary import EN_VOCAB_CHANNEL_ID
from jobs.partner_finder import EN_LOOKING_CHANNEL_ID, NL_LOOKING_CHANNEL_ID
from jobs.private_lessons import (
    EN_PRIVATE_CHANNEL_ID,
    EN_PRIVATE_URL,
    EN_SUPPORTED_CHANNEL_ID,
    EN_SUPPORTED_URL,
    NL_PRIVATE_CHANNEL_ID,
    NL_PRIVATE_URL,
    NL_SUPPORTED_CHANNEL_ID,
    NL_SUPPORTED_URL,
)

FREE_EN_GUIDES_URL = "https://learnwithlucas.com/nederlandse-leermaterialen/"
FREE_NL_GUIDES_URL = "https://learnwithlucas.com/nederlandse-leermaterialen/"


def _channel_url(guild_id: int | None, channel_id: int) -> str | None:
    if guild_id is None:
        return None
    return f"https://discord.com/channels/{guild_id}/{channel_id}"


class GuideLinks(discord.ui.View):
    def __init__(self, *, guild_id: int | None, is_nl: bool) -> None:
        super().__init__(timeout=180)

        if is_nl:
            supported_url = _channel_url(guild_id, NL_SUPPORTED_CHANNEL_ID) or NL_SUPPORTED_URL
            private_url = _channel_url(guild_id, NL_PRIVATE_CHANNEL_ID) or NL_PRIVATE_URL
            partner_url = _channel_url(guild_id, NL_LOOKING_CHANNEL_ID)
            ask_url = _channel_url(guild_id, NL_ASK_JERRY_CHANNEL_ID)
            self.add_item(discord.ui.Button(label="Oefenen", style=discord.ButtonStyle.link, url=supported_url))
            self.add_item(discord.ui.Button(label="Priveles", style=discord.ButtonStyle.link, url=private_url))
            if partner_url:
                self.add_item(discord.ui.Button(label="Spreekpartner", style=discord.ButtonStyle.link, url=partner_url))
            if ask_url:
                self.add_item(discord.ui.Button(label="Vraag Jerry", style=discord.ButtonStyle.link, url=ask_url))
            self.add_item(discord.ui.Button(label="Gratis materiaal", style=discord.ButtonStyle.link, url=FREE_NL_GUIDES_URL))
            return

        supported_url = _channel_url(guild_id, EN_SUPPORTED_CHANNEL_ID) or EN_SUPPORTED_URL
        private_url = _channel_url(guild_id, EN_PRIVATE_CHANNEL_ID) or EN_PRIVATE_URL
        partner_url = _channel_url(guild_id, EN_LOOKING_CHANNEL_ID)
        vocab_url = _channel_url(guild_id, EN_VOCAB_CHANNEL_ID)
        ask_url = _channel_url(guild_id, ASK_JERRY_CHANNEL_ID)
        self.add_item(discord.ui.Button(label="Practice speaking", style=discord.ButtonStyle.link, url=supported_url))
        self.add_item(discord.ui.Button(label="Private lessons", style=discord.ButtonStyle.link, url=private_url))
        if partner_url:
            self.add_item(discord.ui.Button(label="Find a partner", style=discord.ButtonStyle.link, url=partner_url))
        if vocab_url:
            self.add_item(discord.ui.Button(label="Vocabulary", style=discord.ButtonStyle.link, url=vocab_url))
        if ask_url:
            self.add_item(discord.ui.Button(label="Ask Jerry", style=discord.ButtonStyle.link, url=ask_url))


def build_en_guide_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Where should I start?",
        description=(
            "Pick the path that fits what you need today. "
            "You do not need to read the whole server first."
        ),
    )
    embed.add_field(
        name="I want to practice speaking",
        value=(
            f"Start in <#{EN_SUPPORTED_CHANNEL_ID}> if you want a structured path, "
            f"or use <#{EN_LOOKING_CHANNEL_ID}> when you want a quick speaking partner."
        ),
        inline=False,
    )
    embed.add_field(
        name="I want personal help",
        value=(
            f"Go to <#{EN_PRIVATE_CHANNEL_ID}> for private lessons with Lucas. "
            "Best for interviews, presentations, confidence, or a specific deadline."
        ),
        inline=False,
    )
    embed.add_field(
        name="I need words or conversation ideas",
        value=(
            f"Use `/topics` for conversation cards, `/d word: curious` for definitions, "
            f"and <#{EN_VOCAB_CHANNEL_ID}> for vocabulary practice."
        ),
        inline=False,
    )
    embed.add_field(
        name="I am new or a bit lost",
        value=(
            f"Ask questions in <#{ASK_JERRY_CHANNEL_ID}> or use `/guide` again anytime. "
            "A good first step is simple: introduce yourself, then try one small speaking moment."
        ),
        inline=False,
    )
    embed.set_footer(text="Learn with Lucas community guide")
    return embed


def build_nl_guide_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Waar begin ik?",
        description=(
            "Kies wat vandaag bij je past. "
            "Je hoeft niet eerst de hele server te begrijpen."
        ),
    )
    embed.add_field(
        name="Ik wil Nederlands spreken oefenen",
        value=(
            f"Begin in <#{NL_SUPPORTED_CHANNEL_ID}> als je structuur wilt, "
            f"of gebruik <#{NL_LOOKING_CHANNEL_ID}> als je nu een spreekpartner zoekt."
        ),
        inline=False,
    )
    embed.add_field(
        name="Ik wil persoonlijke hulp",
        value=(
            f"Ga naar <#{NL_PRIVATE_CHANNEL_ID}> voor privelessen met Lucas. "
            "Handig voor zelfvertrouwen, werk, examens of een duidelijk doel."
        ),
        inline=False,
    )
    embed.add_field(
        name="Ik heb woorden of gespreksonderwerpen nodig",
        value=(
            "Gebruik `/onderwerpen` voor gesprekskaarten en `/d word: voorbeeld` "
            "om snel een woord op te zoeken."
        ),
        inline=False,
    )
    embed.add_field(
        name="Ik ben nieuw of een beetje verdwaald",
        value=(
            f"Stel vragen in <#{NL_ASK_JERRY_CHANNEL_ID}> of gebruik `/guide` opnieuw. "
            "Een goede eerste stap: stel jezelf kort voor en probeer een klein spreekmoment."
        ),
        inline=False,
    )
    embed.set_footer(text="Learn with Lucas community guide")
    return embed


async def setup(bot: Any) -> None:
    @bot.tree.command(
        name="guide",
        description="Get a simple guide to the community and next steps.",
    )
    async def cmd_guide(interaction: discord.Interaction) -> None:
        is_nl = bool(bot.dutch_guild_id and interaction.guild_id == bot.dutch_guild_id)
        embed = build_nl_guide_embed() if is_nl else build_en_guide_embed()
        view = GuideLinks(guild_id=interaction.guild_id, is_nl=is_nl)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
