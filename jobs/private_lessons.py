from __future__ import annotations

# jobs/private_lessons.py
import logging

import discord

log = logging.getLogger("jobs.private_lessons")

# ---- Channel IDs ----
EN_CHANNEL_ID = 1483062284346458122  # 💬┃private-lessons
NL_CHANNEL_ID = 1483061444399464540  # 💬┃privéles-info

# ---- Booking links ----
EN_BOOKING_URL = "https://learnwithlucas.com/private-lessons"
NL_BOOKING_URL = "https://learnwithlucas.nl/priveles"

# KV keys
KV_EN_MSG_ID = "private_lessons_en_message_id"
KV_NL_MSG_ID = "private_lessons_nl_message_id"

# ---- FAQ content ----

EN_FAQS = {
    "cost": (
        "💰 **What does it cost?**\n\n"
        "**Trial session** — 30 min — €22 (one time)\n"
        "**Speaking Builder** — 4 × 60 min — €159 (save 10%)\n"
        "**Confidence Intensive** — 10 × 60 min — €349 (save 20%)\n\n"
        "**Exam prep options:**\n"
        "Exam Prep Builder — 4 × 60 min — €179\n"
        "Exam Prep Intensive — 10 × 60 min — €379\n\n"
        f"Not sure which fits? Start with the trial. [View all packages]({EN_BOOKING_URL})"
    ),
    "booking": (
        "📅 **How do I book?**\n\n"
        f"1. Go to [learnwithlucas.com/private-lessons]({EN_BOOKING_URL})\n"
        "2. Pick a session or package\n"
        "3. After purchase you receive a calendar link — pick a time that works\n"
        "4. We meet via Zoom or Discord. No setup needed.\n\n"
        "Questions before booking? Email english@learnwithlucas.com — no pressure, no sales pitch."
    ),
    "level": (
        "🎯 **What level do I need to be?**\n\n"
        "No minimum level. These lessons work well if you:\n"
        "• Understand English but hesitate when it's time to speak\n"
        "• Want calm, personal feedback without an audience\n"
        "• Have a specific goal — job interview, presentation, or daily confidence\n"
        "• Are preparing for IELTS, TOEFL, Cambridge or a workplace assessment\n\n"
        "The first session always starts with real conversation so we can find your level together."
    ),
    "format": (
        "🎙️ **What happens in a session?**\n\n"
        "Real conversation from the start. No scripts, no exams, pauses included.\n\n"
        "• We talk about topics that are relevant to you\n"
        "• Calm feedback during or after — whatever works best\n"
        "• Short follow-up notes after the session if useful\n"
        "• Sessions are 30 or 60 minutes depending on what you booked\n\n"
        "The goal is speaking practice in a low-pressure environment — nothing more."
    ),
    "availability": (
        "🕐 **Is there space right now?**\n\n"
        "Private lessons are kept limited so they stay calm and focused.\n\n"
        "If there's no space right now, you're always welcome in:\n"
        "• The free live lessons (Mon, Wed, Thu, Fri, Sat)\n"
        "• The speaking community here on Discord\n\n"
        f"Check current availability at [learnwithlucas.com/private-lessons]({EN_BOOKING_URL})"
    ),
}

NL_FAQS = {
    "kosten": (
        "💰 **Wat kost het?**\n\n"
        "**Proefsessie** — 30 min — €28 (eenmalig)\n"
        "**Speaking Builder** — 4 × 60 min — €219 (10% korting)\n"
        "**Confidence Intensive** — 10 × 60 min — €469 (20% korting)\n\n"
        "**Examenvoorbereiding:**\n"
        "Examenvoorbereiding Builder — 4 × 60 min — €249\n"
        "Examenvoorbereiding Intensive — 10 × 60 min — €529\n\n"
        f"Niet zeker? Begin met de proefsessie. [Bekijk alle pakketten]({NL_BOOKING_URL})"
    ),
    "boeken": (
        "📅 **Hoe boek ik?**\n\n"
        f"1. Ga naar [learnwithlucas.nl/priveles]({NL_BOOKING_URL})\n"
        "2. Kies een sessie of pakket\n"
        "3. Na aankoop ontvang je een kalenderlink — kies een tijd die werkt\n"
        "4. We ontmoeten elkaar via Zoom of Discord. Geen installatie nodig.\n\n"
        "Vragen voor je boekt? Mail dutch@learnwithlucas.com — geen druk, geen verkooppraatje."
    ),
    "niveau": (
        "🎯 **Welk niveau heb ik nodig?**\n\n"
        "Geen minimumniveau. Privélessen werken goed als je:\n"
        "• Nederlands begrijpt maar aarzelt als het tijd is om te spreken\n"
        "• Rustige, persoonlijke feedback wilt zonder publiek\n"
        "• Een specifiek doel hebt — sollicitatie, presentatie of dagelijks zelfvertrouwen\n"
        "• Je voorbereidt op NT2, inburgeringsexamen of een zakelijke assessment\n\n"
        "De eerste sessie begint altijd met een echt gesprek om je niveau samen te ontdekken."
    ),
    "format": (
        "🎙️ **Wat gebeurt er in een sessie?**\n\n"
        "Echt gesprek vanaf het begin. Geen scripts, geen examens, pauzes inbegrepen.\n\n"
        "• We praten over onderwerpen die voor jou relevant zijn\n"
        "• Rustige feedback tijdens of na — wat het beste werkt\n"
        "• Korte follow-up notities na de sessie als dat nuttig is\n"
        "• Sessies zijn 30 of 60 minuten afhankelijk van wat je hebt geboekt\n\n"
        "Het doel is spreekoefening in een omgeving zonder druk — niets meer."
    ),
    "beschikbaarheid": (
        "🕐 **Is er nu plek?**\n\n"
        "Privélessen zijn beperkt zodat ze rustig en gefocust blijven.\n\n"
        "Als er nu geen plek is, ben je altijd welkom bij:\n"
        "• De gratis live lessen (ma, wo, do, vr, za)\n"
        "• De spreekgemeenschap hier op Discord\n\n"
        f"Bekijk huidige beschikbaarheid op [learnwithlucas.nl/priveles]({NL_BOOKING_URL})"
    ),
}


# ---- Embeds ----

def build_en_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎙️ Private English Lessons",
        description=(
            "One on one. Calm. Focused. Yours.\n\n"
            "These lessons are for learners who understand English but want a quiet space "
            "to practice speaking with personal guidance.\n\n"
            "**Sessions & Packages**\n"
            f"🔹 Trial session — 30 min — **€22**\n"
            f"🔹 Speaking Builder — 4 × 60 min — **€159**\n"
            f"🔹 Confidence Intensive — 10 × 60 min — **€349**\n"
            f"🔹 Exam Prep Builder — 4 × 60 min — **€179**\n"
            f"🔹 Exam Prep Intensive — 10 × 60 min — **€379**\n\n"
            f"[**View all sessions & book →**]({EN_BOOKING_URL})\n\n"
            "Questions? Use the dropdown below or email english@learnwithlucas.com"
        ),
    )
    embed.set_footer(text="No scripts. No exams. Pauses included. | private-lessons:en:v1")
    return embed


def build_nl_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎙️ Privélessen Nederlands",
        description=(
            "Een op een. Rustig. Gericht. Voor jou.\n\n"
            "Deze lessen zijn voor leerlingen die Nederlands begrijpen maar een rustige plek "
            "willen om te spreken met persoonlijke begeleiding.\n\n"
            "**Sessies & Pakketten**\n"
            f"🔹 Proefsessie — 30 min — **€28**\n"
            f"🔹 Speaking Builder — 4 × 60 min — **€219**\n"
            f"🔹 Confidence Intensive — 10 × 60 min — **€469**\n"
            f"🔹 Examenvoorbereiding Builder — 4 × 60 min — **€249**\n"
            f"🔹 Examenvoorbereiding Intensive — 10 × 60 min — **€529**\n\n"
            f"[**Bekijk alle sessies & boek →**]({NL_BOOKING_URL})\n\n"
            "Vragen? Gebruik het menu hieronder of mail dutch@learnwithlucas.com"
        ),
    )
    embed.set_footer(text="Geen scripts. Geen examens. Pauzes inbegrepen. | private-lessons:nl:v1")
    return embed


# ---- FAQ Views ----

class EnFAQSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="What does it cost?", value="cost", emoji="💰"),
            discord.SelectOption(label="How do I book?", value="booking", emoji="📅"),
            discord.SelectOption(label="What level do I need?", value="level", emoji="🎯"),
            discord.SelectOption(label="What happens in a session?", value="format", emoji="🎙️"),
            discord.SelectOption(label="Is there space right now?", value="availability", emoji="🕐"),
        ]
        super().__init__(
            placeholder="Questions? Select one…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="private_lessons:faq:en:v1",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        key = self.values[0]
        answer = EN_FAQS.get(key, "Answer not found.")
        await interaction.response.send_message(answer, ephemeral=True)


class NlFAQSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="Wat kost het?", value="kosten", emoji="💰"),
            discord.SelectOption(label="Hoe boek ik?", value="boeken", emoji="📅"),
            discord.SelectOption(label="Welk niveau heb ik nodig?", value="niveau", emoji="🎯"),
            discord.SelectOption(label="Wat gebeurt er in een sessie?", value="format", emoji="🎙️"),
            discord.SelectOption(label="Is er nu plek?", value="beschikbaarheid", emoji="🕐"),
        ]
        super().__init__(
            placeholder="Vragen? Kies er een…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="private_lessons:faq:nl:v1",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        key = self.values[0]
        answer = NL_FAQS.get(key, "Antwoord niet gevonden.")
        await interaction.response.send_message(answer, ephemeral=True)


class EnLessonsView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(EnFAQSelect())


class NlLessonsView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(NlFAQSelect())


# ---- Publisher ----

class PrivateLessonsPublisher:
    def __init__(self, *, bot: discord.Client, repo) -> None:
        self._bot = bot
        self._repo = repo

    async def publish_english(self) -> None:
        await self._publish(
            channel_id=EN_CHANNEL_ID,
            embed=build_en_embed(),
            view=EnLessonsView(),
            kv_key=KV_EN_MSG_ID,
            marker="private-lessons:en:v1",
        )

    async def publish_dutch(self) -> None:
        await self._publish(
            channel_id=NL_CHANNEL_ID,
            embed=build_nl_embed(),
            view=NlLessonsView(),
            kv_key=KV_NL_MSG_ID,
            marker="private-lessons:nl:v1",
        )

    async def _publish(
        self,
        *,
        channel_id: int,
        embed: discord.Embed,
        view: discord.ui.View,
        kv_key: str,
        marker: str,
    ) -> None:
        channel = self._bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self._bot.fetch_channel(channel_id)
            except Exception:
                log.warning("PrivateLessons: could not fetch channel %s", channel_id)
                return

        if not isinstance(channel, discord.TextChannel):
            log.warning("PrivateLessons: channel %s is not a TextChannel", channel_id)
            return

        # Try to find existing message by footer marker in history
        existing: discord.Message | None = None
        existing_id_raw = await self._repo.kv_get(channel.guild.id, kv_key)
        if existing_id_raw:
            try:
                existing = await channel.fetch_message(int(existing_id_raw))
            except Exception:
                log.warning("PrivateLessons: could not fetch existing message, will recreate")
                existing = None

        if existing:
            try:
                await existing.edit(embed=embed, view=view)
                log.info("PrivateLessons: updated message in channel %s", channel_id)
                return
            except Exception:
                log.warning("PrivateLessons: could not edit, recreating")

        # Post new
        try:
            sent = await channel.send(embed=embed, view=view)
            await self._repo.kv_set(channel.guild.id, kv_key, str(sent.id))
            log.info("PrivateLessons: posted message %s in channel %s", sent.id, channel_id)
            try:
                await sent.pin()
                log.info("PrivateLessons: pinned message in channel %s", channel_id)
            except discord.Forbidden:
                log.warning("PrivateLessons: missing pin permission in channel %s", channel_id)
            except Exception:
                log.warning("PrivateLessons: could not pin in channel %s", channel_id)
        except Exception:
            log.exception("PrivateLessons: failed to post in channel %s", channel_id)
