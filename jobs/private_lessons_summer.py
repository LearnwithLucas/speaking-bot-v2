from __future__ import annotations

import discord

from jobs import private_lessons as base


EN_PRIVATE_FAQS = {
    "cost": (
        "**What does it cost?**\n\n"
        "Trial session - 30 min - **EUR 24** (one time)\n"
        "Speaking Builder - 4 x 60 min - **EUR 189** (EUR 47.25/hour)\n"
        "Confidence Intensive - 10 x 60 min - **EUR 389** (EUR 38.90/hour)\n\n"
        "Split payments are possible. Use private lessons for work, calls, small talk, presentations, "
        "confidence, or exam speaking practice.\n\n"
        f"Not sure which fits? Start with the trial. [View all packages]({base.EN_PRIVATE_URL})"
    ),
    "booking": base.EN_PRIVATE_FAQS["booking"],
    "level": (
        "**What level do I need?**\n\n"
        "No minimum level. Private lessons work well if you:\n"
        "- Understand English but hesitate when it is time to speak\n"
        "- Want calm, personal feedback without an audience\n"
        "- Have a specific goal such as a job interview, presentation or daily confidence\n"
        "- Are preparing for an exam, interview or workplace situation\n\n"
        "The first session always starts with real conversation to find your level together."
    ),
    "format": base.EN_PRIVATE_FAQS["format"],
    "availability": (
        "**Is there space right now?**\n\n"
        "Private lessons are kept limited so they stay calm and focused.\n\n"
        "Current availability is shown on the private lessons page.\n\n"
        f"Check current availability: [learnwithlucas.com/en/private-lessons]({base.EN_PRIVATE_URL})"
    ),
    "vs_supported": (
        "**Private lessons vs Supported Speaking - which is better?**\n\n"
        "**Private lessons** are one-on-one with Lucas. Fully personalised, your pace, "
        "your topics, your goals. Best for specific targets or people who want dedicated attention. "
        "Trial from EUR 24.\n\n"
        "**Supported Speaking** is a group subscription. Best for consistent practice at a sustainable cost.\n\n"
        "Many members use both."
    ),
    "exam_prep": (
        "**Can you help with exam prep?**\n\n"
        "Yes. Private lessons can focus on an exam, interview, presentation, work call, "
        "or any speaking situation where pressure gets in the way.\n\n"
        f"[View packages]({base.EN_PRIVATE_URL})"
    ),
    "payment": (
        "**How do I pay?**\n\n"
        "Payment is via the website checkout. Sociabuzz is available as an alternative option.\n\n"
        f"All packages and checkout: [learnwithlucas.com/en/private-lessons]({base.EN_PRIVATE_URL})\n\n"
        "Questions about payment? Email english@learnwithlucas.com"
    ),
}


NL_PRIVATE_FAQS = {
    "kosten": (
        "**Wat kost het?**\n\n"
        f"Proefsessie - 30 min - **EUR 28** - [boek hier]({base.NL_TRIAL_LINK})\n"
        f"Speaking Builder - 4 x 60 min - **EUR 219** (+ 3 maanden Ondersteund Spreken) - [boek hier]({base.NL_BUILDER_LINK})\n"
        f"Confidence Intensive - 10 x 60 min - **EUR 469** (+ 6 maanden Ondersteund Spreken) - [boek hier]({base.NL_INTENSIVE_LINK})\n\n"
        "Examentraining voor Inburgering, KNM, ONA, NT2 en CNaVT zit in de gewone pakketten.\n\n"
        f"Niet zeker? Begin met de proefsessie. [Alle pakketten]({base.NL_PRIVATE_URL})"
    ),
    "boeken": base.NL_PRIVATE_FAQS["boeken"],
    "niveau": base.NL_PRIVATE_FAQS["niveau"],
    "format": base.NL_PRIVATE_FAQS["format"],
    "beschikbaarheid": (
        "**Is er nu plek?**\n\n"
        "Privelessen zijn beperkt zodat ze rustig en gefocust blijven.\n\n"
        "De actuele beschikbaarheid staat op de privelespagina.\n\n"
        f"Bekijk beschikbaarheid: [learnwithlucas.com/nl/priveles-nederlands]({base.NL_PRIVATE_URL})"
    ),
    "bundels": base.NL_PRIVATE_FAQS["bundels"],
    "examen": base.NL_PRIVATE_FAQS["examen"],
    "betaling": base.NL_PRIVATE_FAQS["betaling"],
}


def build_en_private_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Private English Lessons",
        description=(
            "One on one. Calm. Focused. Yours.\n\n"
            "For learners who understand English but want a quiet space to practice speaking "
            "with personal guidance. No scripts. No exams. Pauses included.\n\n"
            "Split payments are possible for larger packages.\n\n"
            "**Sessions and Packages**\n"
            f"- Trial session - 30 min - **EUR 24** - [book]({base.EN_PRIVATE_URL})\n"
            f"- Speaking Builder - 4 x 60 min - **EUR 189** (EUR 47.25/hour) - [book]({base.EN_PRIVATE_URL})\n"
            f"- Confidence Intensive - 10 x 60 min - **EUR 389** (EUR 38.90/hour) - [book]({base.EN_PRIVATE_URL})\n"
            "\n"
            "Platform: Zoom or Discord, your choice.\n\n"
            "Questions? Use the dropdown below or email english@learnwithlucas.com"
        ),
    )
    embed.set_footer(text="private-lessons:en:v3")
    return embed


def build_nl_private_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Privelessen Nederlands",
        description=(
            "Een op een. Rustig. Gericht. Voor jou.\n\n"
            "Voor leerlingen die Nederlands begrijpen maar een rustige plek willen om te spreken "
            "met persoonlijke begeleiding. Geen scripts. Geen examens. Pauzes inbegrepen.\n\n"
            "Speaking Builder en Confidence Intensive bevatten gratis maanden Ondersteund Spreken.\n\n"
            "**Sessies en Pakketten**\n"
            f"- Proefsessie - 30 min - **EUR 28** - [boek]({base.NL_TRIAL_LINK})\n"
            f"- Speaking Builder - 4 x 60 min - **EUR 219** - [boek]({base.NL_BUILDER_LINK})\n"
            f"- Confidence Intensive - 10 x 60 min - **EUR 469** - [boek]({base.NL_INTENSIVE_LINK})\n\n"
            "Speaking Builder bevat 3 maanden Ondersteund Spreken gratis.\n"
            "Confidence Intensive bevat 6 maanden Ondersteund Spreken gratis.\n"
            "Platform: Zoom of Discord, jouw keuze.\n\n"
            "Vragen? Gebruik het menu hieronder of mail english@learnwithlucas.com"
        ),
    )
    embed.set_footer(text="private-lessons:nl:v3")
    return embed


class EnPrivateFAQSelect(discord.ui.Select):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Questions? Select one...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="What does it cost?", value="cost"),
                discord.SelectOption(label="How do I book?", value="booking"),
                discord.SelectOption(label="What level do I need?", value="level"),
                discord.SelectOption(label="What happens in a session?", value="format"),
                discord.SelectOption(label="Is there space right now?", value="availability"),
                discord.SelectOption(label="Private lessons vs Supported Speaking", value="vs_supported"),
                discord.SelectOption(label="Exam prep", value="exam_prep"),
                discord.SelectOption(label="How do I pay?", value="payment"),
            ],
            custom_id="private_lessons:faq:en:v2",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            EN_PRIVATE_FAQS.get(self.values[0], "Answer not found."), ephemeral=True
        )


class NlPrivateFAQSelect(discord.ui.Select):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Vragen? Kies er een...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Wat kost het?", value="kosten"),
                discord.SelectOption(label="Hoe boek ik?", value="boeken"),
                discord.SelectOption(label="Welk niveau heb ik nodig?", value="niveau"),
                discord.SelectOption(label="Wat gebeurt er in een sessie?", value="format"),
                discord.SelectOption(label="Is er nu plek?", value="beschikbaarheid"),
                discord.SelectOption(label="Bundels met Ondersteund Spreken", value="bundels"),
                discord.SelectOption(label="NT2 of inburgeringsexamen", value="examen"),
                discord.SelectOption(label="Hoe betaal ik?", value="betaling"),
            ],
            custom_id="private_lessons:faq:nl:v2",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            NL_PRIVATE_FAQS.get(self.values[0], "Antwoord niet gevonden."), ephemeral=True
        )


class EnLessonsView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(EnPrivateFAQSelect())


class NlLessonsView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(NlPrivateFAQSelect())


class EnSupportedView(base.EnSupportedView):
    pass


class NlSupportedView(base.NlSupportedView):
    pass


class PrivateLessonsPublisher(base.PrivateLessonsPublisher):
    async def publish_english(self) -> None:
        await self._publish(
            channel_id=base.EN_PRIVATE_CHANNEL_ID,
            embed=build_en_private_embed(),
            view=EnLessonsView(),
            kv_key=base.KV_EN_PRIVATE_MSG,
            guild_id=None,
        )

    async def publish_dutch(self) -> None:
        await self._publish(
            channel_id=base.NL_PRIVATE_CHANNEL_ID,
            embed=build_nl_private_embed(),
            view=NlLessonsView(),
            kv_key=base.KV_NL_PRIVATE_MSG,
            guild_id=None,
        )
