from __future__ import annotations

import logging
import time
from typing import Any

import discord
from discord import app_commands

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

log = logging.getLogger(__name__)

FREE_EN_GUIDES_URL = "https://learnwithlucas.com/nederlandse-leermaterialen/"
FREE_NL_GUIDES_URL = "https://learnwithlucas.com/nederlandse-leermaterialen/"
GUIDE_CHOICES = {"shy", "partner", "lessons", "words", "ask"}


def _channel_url(guild_id: int | None, channel_id: int) -> str | None:
    if guild_id is None:
        return None
    return f"https://discord.com/channels/{guild_id}/{channel_id}"


async def _record_guide_usage(bot: Any, interaction: discord.Interaction) -> None:
    if interaction.guild_id is None:
        return

    repo = getattr(bot, "repo", None)
    if repo is None or not hasattr(repo, "command_usage_record"):
        return

    try:
        await repo.command_usage_record(
            interaction.guild_id,
            interaction.user.id,
            "guide",
            int(time.time()),
        )
    except Exception:
        log.exception("guide: failed to record command usage")


class GuideChoiceButton(discord.ui.Button):
    def __init__(self, choice: str, label: str, *, row: int) -> None:
        style = discord.ButtonStyle.primary if choice == "shy" else discord.ButtonStyle.secondary
        super().__init__(label=label, style=style, custom_id=f"guide:{choice}", row=row)
        self.choice = choice

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, GuideChoiceView):
            await interaction.response.defer()
            return
        await view.show_choice(interaction, self.choice)


class GuideBackButton(discord.ui.Button):
    def __init__(self, label: str) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary, custom_id="guide:back", row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, GuideDetailView):
            await interaction.response.defer()
            return

        embed = build_nl_guide_embed() if view.is_nl else build_en_guide_embed()
        await interaction.response.edit_message(
            embed=embed,
            view=GuideChoiceView(bot=view.bot, guild_id=interaction.guild_id, is_nl=view.is_nl),
        )


class GuideChoiceView(discord.ui.View):
    def __init__(self, *, bot: Any, guild_id: int | None, is_nl: bool) -> None:
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id
        self.is_nl = is_nl

        labels = (
            [
                ("shy", "Ik ben onzeker"),
                ("partner", "Spreekpartner"),
                ("lessons", "Priveles"),
                ("words", "Woorden"),
                ("ask", "Vraag Jerry"),
            ]
            if is_nl
            else [
                ("shy", "I feel nervous"),
                ("partner", "Find a partner"),
                ("lessons", "Private lessons"),
                ("words", "Words / topics"),
                ("ask", "Ask Jerry"),
            ]
        )

        for index, (choice, label) in enumerate(labels):
            self.add_item(GuideChoiceButton(choice, label, row=0 if index < 3 else 1))

    async def show_choice(self, interaction: discord.Interaction, choice: str) -> None:
        is_nl = bool(self.is_nl)
        embed = build_choice_embed(choice, is_nl=is_nl)
        view = GuideDetailView(bot=self.bot, guild_id=interaction.guild_id, is_nl=is_nl, choice=choice)
        await interaction.response.edit_message(embed=embed, view=view)


class GuideDetailView(discord.ui.View):
    def __init__(self, *, bot: Any, guild_id: int | None, is_nl: bool, choice: str) -> None:
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id
        self.is_nl = is_nl

        if is_nl:
            self._add_nl_links(guild_id, choice)
        else:
            self._add_en_links(guild_id, choice)
        self.add_item(GuideBackButton("Terug" if is_nl else "Back"))

    def _add_en_links(self, guild_id: int | None, choice: str) -> None:
        supported_url = _channel_url(guild_id, EN_SUPPORTED_CHANNEL_ID) or EN_SUPPORTED_URL
        private_url = _channel_url(guild_id, EN_PRIVATE_CHANNEL_ID) or EN_PRIVATE_URL
        partner_url = _channel_url(guild_id, EN_LOOKING_CHANNEL_ID)
        vocab_url = _channel_url(guild_id, EN_VOCAB_CHANNEL_ID)
        ask_url = _channel_url(guild_id, ASK_JERRY_CHANNEL_ID)

        if choice in {"shy", "partner"}:
            self.add_item(discord.ui.Button(label="Supported speaking", style=discord.ButtonStyle.link, url=supported_url, row=0))
            if partner_url:
                self.add_item(discord.ui.Button(label="Find a partner", style=discord.ButtonStyle.link, url=partner_url, row=0))
        if choice == "lessons":
            self.add_item(discord.ui.Button(label="Private lessons", style=discord.ButtonStyle.link, url=private_url, row=0))
        if choice == "words":
            if vocab_url:
                self.add_item(discord.ui.Button(label="Vocabulary", style=discord.ButtonStyle.link, url=vocab_url, row=0))
            self.add_item(discord.ui.Button(label="Free materials", style=discord.ButtonStyle.link, url=FREE_EN_GUIDES_URL, row=0))
        if ask_url and choice in {"shy", "words", "ask"}:
            self.add_item(discord.ui.Button(label="Ask Jerry", style=discord.ButtonStyle.link, url=ask_url, row=0))
        if choice == "ask":
            self.add_item(discord.ui.Button(label="Free materials", style=discord.ButtonStyle.link, url=FREE_EN_GUIDES_URL, row=0))

    def _add_nl_links(self, guild_id: int | None, choice: str) -> None:
        supported_url = _channel_url(guild_id, NL_SUPPORTED_CHANNEL_ID) or NL_SUPPORTED_URL
        private_url = _channel_url(guild_id, NL_PRIVATE_CHANNEL_ID) or NL_PRIVATE_URL
        partner_url = _channel_url(guild_id, NL_LOOKING_CHANNEL_ID)
        ask_url = _channel_url(guild_id, NL_ASK_JERRY_CHANNEL_ID)

        if choice in {"shy", "partner"}:
            self.add_item(discord.ui.Button(label="Samen oefenen", style=discord.ButtonStyle.link, url=supported_url, row=0))
            if partner_url:
                self.add_item(discord.ui.Button(label="Spreekpartner", style=discord.ButtonStyle.link, url=partner_url, row=0))
        if choice == "lessons":
            self.add_item(discord.ui.Button(label="Priveles", style=discord.ButtonStyle.link, url=private_url, row=0))
        if choice == "words":
            self.add_item(discord.ui.Button(label="Gratis materiaal", style=discord.ButtonStyle.link, url=FREE_NL_GUIDES_URL, row=0))
        if ask_url and choice in {"shy", "words", "ask"}:
            self.add_item(discord.ui.Button(label="Vraag Jerry", style=discord.ButtonStyle.link, url=ask_url, row=0))
        if choice == "ask":
            self.add_item(discord.ui.Button(label="Gratis materiaal", style=discord.ButtonStyle.link, url=FREE_NL_GUIDES_URL, row=0))


def build_en_guide_embed() -> discord.Embed:
    embed = discord.Embed(
        title="What do you need right now?",
        description=(
            "Choose one private option below. "
            "I will give you the shortest useful next step."
        ),
    )
    embed.add_field(
        name="Not sure?",
        value="Pick **I feel nervous**. Starting small is a normal way to begin.",
        inline=False,
    )
    embed.set_footer(text="Learn with Lucas community guide")
    return embed


def build_nl_guide_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Wat heb je nu nodig?",
        description=(
            "Kies hieronder een prive optie. "
            "Dan krijg je meteen de kortste nuttige volgende stap."
        ),
    )
    embed.add_field(
        name="Twijfel je?",
        value="Kies **Ik ben onzeker**. Klein beginnen is heel normaal.",
        inline=False,
    )
    embed.set_footer(text="Learn with Lucas community guide")
    return embed


def build_choice_embed(choice: str, *, is_nl: bool) -> discord.Embed:
    if is_nl:
        return build_nl_choice_embed(choice)
    return build_en_choice_embed(choice)


def build_en_choice_embed(choice: str) -> discord.Embed:
    embed = discord.Embed()

    if choice == "partner":
        embed.title = "Find one person to speak with"
        embed.description = "Use the partner channel when you want a simple practice moment."
        embed.add_field(
            name="Best next step",
            value=f"Go to <#{EN_LOOKING_CHANNEL_ID}> and share when you are free.",
            inline=False,
        )
        embed.add_field(
            name="Keep it simple",
            value="Ask for 10 or 15 minutes. A short call still counts.",
            inline=False,
        )
    elif choice == "lessons":
        embed.title = "Private lessons"
        embed.description = "Choose this if you want personal feedback, structure, or help with a specific goal."
        embed.add_field(
            name="Best next step",
            value=f"Open <#{EN_PRIVATE_CHANNEL_ID}> and choose a trial session or package.",
            inline=False,
        )
        embed.add_field(
            name="Good for",
            value="Confidence, job interviews, presentations, daily speaking, grammar, or exam prep.",
            inline=False,
        )
    elif choice == "words":
        embed.title = "Words and conversation ideas"
        embed.description = "Use this when you know you want to practice, but your brain goes blank."
        embed.add_field(
            name="Best next step",
            value=f"Try `/topics`, `/d word: curious`, or visit <#{EN_VOCAB_CHANNEL_ID}>.",
            inline=False,
        )
        embed.add_field(
            name="Small prompt",
            value="Pick one word, make one sentence, then ask one follow-up question.",
            inline=False,
        )
    elif choice == "ask":
        embed.title = "Ask Jerry"
        embed.description = "Use this when you are lost, unsure what to practice, or need a quick explanation."
        embed.add_field(
            name="Best next step",
            value=f"Ask your question in <#{ASK_JERRY_CHANNEL_ID}>. Short questions are welcome.",
            inline=False,
        )
    else:
        embed.title = "A calm first step"
        embed.description = "You do not need to perform. Start with one small speaking moment."
        embed.add_field(
            name="Best next step",
            value=(
                f"Join <#{EN_SUPPORTED_CHANNEL_ID}> or ask for one partner in "
                f"<#{EN_LOOKING_CHANNEL_ID}>."
            ),
            inline=False,
        )
        embed.add_field(
            name="Make it easy",
            value="Say one sentence, listen for a bit, and leave when that is enough for today.",
            inline=False,
        )

    embed.set_footer(text="Use Back if you want a different path")
    return embed


def build_nl_choice_embed(choice: str) -> discord.Embed:
    embed = discord.Embed()

    if choice == "partner":
        embed.title = "Zoek een spreekpartner"
        embed.description = "Gebruik dit als je gewoon even met een persoon wilt oefenen."
        embed.add_field(
            name="Beste volgende stap",
            value=f"Ga naar <#{NL_LOOKING_CHANNEL_ID}> en zeg wanneer je tijd hebt.",
            inline=False,
        )
        embed.add_field(
            name="Hou het klein",
            value="Vraag om 10 of 15 minuten. Een kort gesprek telt ook.",
            inline=False,
        )
    elif choice == "lessons":
        embed.title = "Priveles"
        embed.description = "Kies dit als je persoonlijke feedback, structuur of hulp met een doel wilt."
        embed.add_field(
            name="Beste volgende stap",
            value=f"Open <#{NL_PRIVATE_CHANNEL_ID}> en kies een proefles of pakket.",
            inline=False,
        )
        embed.add_field(
            name="Goed voor",
            value="Zelfvertrouwen, werk, presentaties, dagelijks spreken, grammatica of examenvoorbereiding.",
            inline=False,
        )
    elif choice == "words":
        embed.title = "Woorden en gespreksonderwerpen"
        embed.description = "Gebruik dit als je wilt oefenen, maar even geen onderwerp weet."
        embed.add_field(
            name="Beste volgende stap",
            value="Probeer `/onderwerpen` of `/d word: voorbeeld`.",
            inline=False,
        )
        embed.add_field(
            name="Kleine oefening",
            value="Kies een woord, maak een zin en stel daarna een vervolgvraag.",
            inline=False,
        )
    elif choice == "ask":
        embed.title = "Vraag Jerry"
        embed.description = "Gebruik dit als je verdwaald bent, niet weet wat je moet oefenen, of iets kort wilt vragen."
        embed.add_field(
            name="Beste volgende stap",
            value=f"Stel je vraag in <#{NL_ASK_JERRY_CHANNEL_ID}>. Korte vragen zijn welkom.",
            inline=False,
        )
    else:
        embed.title = "Een rustige eerste stap"
        embed.description = "Je hoeft niet te presteren. Begin met een klein spreekmoment."
        embed.add_field(
            name="Beste volgende stap",
            value=(
                f"Begin in <#{NL_SUPPORTED_CHANNEL_ID}> of zoek een persoon in "
                f"<#{NL_LOOKING_CHANNEL_ID}>."
            ),
            inline=False,
        )
        embed.add_field(
            name="Maak het makkelijk",
            value="Zeg een zin, luister even mee en stop wanneer dat genoeg is voor vandaag.",
            inline=False,
        )

    embed.set_footer(text="Gebruik Terug als je iets anders zoekt")
    return embed


async def setup(bot: Any) -> None:
    @bot.tree.command(
        name="guide",
        description="Get a simple guide to the community and next steps.",
    )
    @app_commands.describe(choice="Choose what kind of help you need.")
    @app_commands.choices(
        choice=[
            app_commands.Choice(name="I feel nervous", value="shy"),
            app_commands.Choice(name="Find a speaking partner", value="partner"),
            app_commands.Choice(name="Private lessons", value="lessons"),
            app_commands.Choice(name="Words or topics", value="words"),
            app_commands.Choice(name="Ask Jerry", value="ask"),
        ]
    )
    async def cmd_guide(interaction: discord.Interaction, choice: str | None = None) -> None:
        await _record_guide_usage(bot, interaction)

        is_nl = bool(bot.dutch_guild_id and interaction.guild_id == bot.dutch_guild_id)
        if choice in GUIDE_CHOICES:
            embed = build_choice_embed(choice, is_nl=is_nl)
            view = GuideDetailView(bot=bot, guild_id=interaction.guild_id, is_nl=is_nl, choice=choice)
        else:
            embed = build_nl_guide_embed() if is_nl else build_en_guide_embed()
            view = GuideChoiceView(bot=bot, guild_id=interaction.guild_id, is_nl=is_nl)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
