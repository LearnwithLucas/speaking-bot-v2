from __future__ import annotations

# jobs/private_lessons.py
import logging

import discord

log = logging.getLogger("jobs.private_lessons")

# ---- Channel IDs ----
EN_PRIVATE_CHANNEL_ID = 1483062284346458122       # 💬┃private-lessons
NL_PRIVATE_CHANNEL_ID = 1483061444399464540       # 💬┃privéles-info
EN_SUPPORTED_CHANNEL_ID = 1483065969310961776     # 🌟┃supported-speaking
NL_SUPPORTED_CHANNEL_ID = 1483065869465682083     # 🌟┃ondersteund-spreken

# ---- Links ----
EN_PRIVATE_URL = "https://learnwithlucas.com/private-lessons"
NL_PRIVATE_URL = "https://learnwithlucas.com/priveles-nederlands/"
EN_SUPPORTED_URL = "https://learnwithlucas.com/supported-speaking/"
NL_SUPPORTED_URL = "https://learnwithlucas.com/ondersteund-spreken/"

# ---- KV keys ----
KV_EN_PRIVATE_MSG = "private_lessons_en_message_id"
KV_NL_PRIVATE_MSG = "private_lessons_nl_message_id"
KV_EN_SUPPORTED_MSG = "supported_speaking_en_message_id"
KV_NL_SUPPORTED_MSG = "supported_speaking_nl_message_id"


# ==============================================================
# PRIVATE LESSONS
# ==============================================================

EN_PRIVATE_FAQS = {
    "cost": (
        "**What does it cost?**\n\n"
        "Trial session — 30 min — **€22** (one time)\n"
        "Speaking Builder — 4 × 60 min — **€159** (save 10%)\n"
        "Confidence Intensive — 10 × 60 min — **€349** (save 20%)\n\n"
        "Exam prep:\n"
        "Exam Prep Builder — 4 × 60 min — **€179**\n"
        "Exam Prep Intensive — 10 × 60 min — **€379**\n\n"
        f"Not sure which fits? Start with the trial. [View all packages]({EN_PRIVATE_URL})"
    ),
    "booking": (
        "**How do I book?**\n\n"
        f"1. Go to [learnwithlucas.com/private-lessons]({EN_PRIVATE_URL})\n"
        "2. Pick a session or package\n"
        "3. After purchase you get a calendar link — pick a time that works\n"
        "4. We meet via Zoom or Discord. No setup needed.\n\n"
        "Questions before booking? Email english@learnwithlucas.com"
    ),
    "level": (
        "**What level do I need?**\n\n"
        "No minimum level. These lessons work well if you:\n"
        "• Understand English but hesitate when it's time to speak\n"
        "• Want calm, personal feedback without an audience\n"
        "• Have a specific goal — job interview, presentation, or daily confidence\n"
        "• Are preparing for IELTS, TOEFL, Cambridge or a workplace assessment\n\n"
        "The first session always starts with real conversation to find your level together."
    ),
    "format": (
        "**What happens in a session?**\n\n"
        "Real conversation from the start. No scripts, no exams, pauses included.\n\n"
        "• We talk about topics relevant to you\n"
        "• Calm feedback during or after — whatever works best\n"
        "• Short follow-up notes after the session if useful\n"
        "• Sessions are 30 or 60 minutes depending on what you booked"
    ),
    "availability": (
        "**Is there space right now?**\n\n"
        "Private lessons are kept limited so they stay calm and focused.\n\n"
        "If there's no space right now, you're always welcome in the free live lessons "
        "and the speaking community.\n\n"
        f"Check current availability at [learnwithlucas.com/private-lessons]({EN_PRIVATE_URL})"
    ),
}

NL_PRIVATE_FAQS = {
    "kosten": (
        "**Wat kost het?**\n\n"
        "Proefsessie — 30 min — **€28** (eenmalig)\n"
        "Speaking Builder — 4 × 60 min — **€219** (10% korting)\n"
        "Confidence Intensive — 10 × 60 min — **€469** (20% korting)\n\n"
        "Examenvoorbereiding:\n"
        "Examenvoorbereiding Builder — 4 × 60 min — **€249**\n"
        "Examenvoorbereiding Intensive — 10 × 60 min — **€529**\n\n"
        f"Niet zeker? Begin met de proefsessie. [Bekijk alle pakketten]({NL_PRIVATE_URL})"
    ),
    "boeken": (
        "**Hoe boek ik?**\n\n"
        f"1. Ga naar [learnwithlucas.com/private-lessons]({NL_PRIVATE_URL})\n"
        "2. Kies een sessie of pakket\n"
        "3. Na aankoop ontvang je een kalenderlink — kies een tijd die werkt\n"
        "4. We ontmoeten elkaar via Zoom of Discord. Geen installatie nodig.\n\n"
        "Vragen voor je boekt? Mail dutch@learnwithlucas.com"
    ),
    "niveau": (
        "**Welk niveau heb ik nodig?**\n\n"
        "Geen minimumniveau. Privélessen werken goed als je:\n"
        "• Nederlands begrijpt maar aarzelt als het tijd is om te spreken\n"
        "• Rustige, persoonlijke feedback wilt zonder publiek\n"
        "• Een specifiek doel hebt — sollicitatie, presentatie of dagelijks zelfvertrouwen\n"
        "• Je voorbereidt op NT2, inburgeringsexamen of een zakelijke assessment\n\n"
        "De eerste sessie begint altijd met een echt gesprek om je niveau te ontdekken."
    ),
    "format": (
        "**Wat gebeurt er in een sessie?**\n\n"
        "Echt gesprek vanaf het begin. Geen scripts, geen examens, pauzes inbegrepen.\n\n"
        "• We praten over onderwerpen die voor jou relevant zijn\n"
        "• Rustige feedback tijdens of na — wat het beste werkt\n"
        "• Korte follow-up notities na de sessie als dat nuttig is\n"
        "• Sessies zijn 30 of 60 minuten afhankelijk van wat je hebt geboekt"
    ),
    "beschikbaarheid": (
        "**Is er nu plek?**\n\n"
        "Privélessen zijn beperkt zodat ze rustig en gefocust blijven.\n\n"
        "Als er nu geen plek is, ben je altijd welkom bij de gratis live lessen "
        "en de spreekgemeenschap.\n\n"
        f"Bekijk huidige beschikbaarheid op [learnwithlucas.com/private-lessons]({NL_PRIVATE_URL})"
    ),
}


def build_en_private_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎙️ Private English Lessons",
        description=(
            "One on one. Calm. Focused. Yours.\n\n"
            "For learners who understand English but want a quiet space to practice "
            "speaking with personal guidance. No scripts. No exams. Pauses included.\n\n"
            "**Sessions & Packages**\n"
            "🔹 Trial session — 30 min — **€22**\n"
            "🔹 Speaking Builder — 4 × 60 min — **€159**\n"
            "🔹 Confidence Intensive — 10 × 60 min — **€349**\n"
            "🔹 Exam Prep Builder — 4 × 60 min — **€179**\n"
            "🔹 Exam Prep Intensive — 10 × 60 min — **€379**\n\n"
            f"[**View all sessions & book →**]({EN_PRIVATE_URL})\n\n"
            "Questions? Use the dropdown below or email english@learnwithlucas.com"
        ),
    )
    embed.set_footer(text="private-lessons:en:v1")
    return embed


def build_nl_private_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎙️ Privélessen Nederlands",
        description=(
            "Een op een. Rustig. Gericht. Voor jou.\n\n"
            "Voor leerlingen die Nederlands begrijpen maar een rustige plek willen om te spreken "
            "met persoonlijke begeleiding. Geen scripts. Geen examens. Pauzes inbegrepen.\n\n"
            "**Sessies & Pakketten**\n"
            "🔹 Proefsessie — 30 min — **€28**\n"
            "🔹 Speaking Builder — 4 × 60 min — **€219**\n"
            "🔹 Confidence Intensive — 10 × 60 min — **€469**\n"
            "🔹 Examenvoorbereiding Builder — 4 × 60 min — **€249**\n"
            "🔹 Examenvoorbereiding Intensive — 10 × 60 min — **€529**\n\n"
            f"[**Bekijk alle sessies & boek →**]({NL_PRIVATE_URL})\n\n"
            "Vragen? Gebruik het menu hieronder of mail dutch@learnwithlucas.com"
        ),
    )
    embed.set_footer(text="private-lessons:nl:v1")
    return embed


# ==============================================================
# SUPPORTED SPEAKING
# ==============================================================

EN_SUPPORTED_FAQS = {
    "whatisit": (
        "**What is Supported Speaking?**\n\n"
        "A weekly practice membership for €4.99/month (or €49.90/year — 2 months free).\n\n"
        "You get:\n"
        "• Extended practice guides every Monday, Friday and Saturday\n"
        "• 5 B1-level stories with audio every month\n"
        "• Error recognition training in every guide\n"
        "• Community access — Discord, WhatsApp and Telegram\n\n"
        "Private lessons with Lucas cost €22 per session. This is weekly practice for €4.99/month."
    ),
    "guides": (
        "**What are the practice guides?**\n\n"
        "Every Monday, Friday and Saturday you get the supporter edition guide — extended "
        "versions of the free lesson guides with:\n\n"
        "• 10 extra practice sentences\n"
        "• Error recognition paragraph (find and fix hidden mistakes)\n"
        "• Self-check questions\n"
        "• Quick recognition test\n\n"
        "Members get 3x more content than the free version."
    ),
    "joining": (
        "**How do I join?**\n\n"
        f"Go to [learnwithlucas.com/supported-speaking]({EN_SUPPORTED_URL})\n\n"
        "Monthly: **€4.99/month** — cancel anytime\n"
        "Annual: **€49.90/year** — 2 months free\n\n"
        "Paying from Philippines, Indonesia, Malaysia or Thailand? "
        f"GCash, DANA and Touch 'n Go options available on the [page]({EN_SUPPORTED_URL}).\n\n"
        "100% refund within 24 hours, no questions asked."
    ),
    "level": (
        "**What level do I need?**\n\n"
        "Supported Speaking works well if you:\n"
        "• Understand English but freeze when you have to speak\n"
        "• Are at B1 or B2 level and want to keep improving\n"
        "• Don't want an expensive course but do want structure\n"
        "• Prefer practicing over studying theory\n"
        "• Want to work at your own pace in a calm environment"
    ),
    "community": (
        "**What community access do I get?**\n\n"
        "As a member you get access to:\n"
        "• This Discord server (you're already here!)\n"
        "• WhatsApp group\n"
        "• Telegram group\n\n"
        "You can practice with other learners and ask questions anytime, "
        "alongside the free Monday and Friday live lessons."
    ),
}

NL_SUPPORTED_FAQS = {
    "watishet": (
        "**Wat is Ondersteund Spreken?**\n\n"
        "Een wekelijks oefeningslidmaatschap voor €7,99/maand (of €79,90/jaar — 2 maanden gratis).\n\n"
        "Je krijgt:\n"
        "• Live sessie elke maandag 19:00 CET in kleine breakout rooms op niveau\n"
        "• Leden oefengids elke vrijdag\n"
        "• Spreekonderwerp elke zondag (ter voorbereiding op maandag)\n"
        "• Maandelijks verhaal met audio\n\n"
        "Een privéles met Lucas kost €28. Dit is elke week live oefenen voor €7,99/maand."
    ),
    "sessie": (
        "**Hoe werkt de live sessie?**\n\n"
        "Elke maandag 19:00 CET — één uur:\n\n"
        "• 0:00–0:15 — Introductie. Lucas introduceert het onderwerp. Iedereen samen.\n"
        "• 0:15–0:45 — Breakout rooms op niveau (A2, B1, B2). Lucas bezoekt elke kamer.\n"
        "• 0:45–1:00 — Afsluiting. Terug samen. Veelgemaakte fouten besproken.\n\n"
        "Max 20 personen per sessie. Rustige sfeer."
    ),
    "aanmelden": (
        "**Hoe meld ik me aan?**\n\n"
        f"Ga naar [learnwithlucas.com/ondersteund-spreken]({NL_SUPPORTED_URL})\n\n"
        "Maandelijks: **€7,99/maand** — op elk moment opzegbaar\n"
        "Jaarlijks: **€79,90/jaar** — 2 maanden gratis\n\n"
        "Betaal je vanuit de Filipijnen, Indonesië, Maleisië of Thailand? "
        f"GCash, DANA en Touch 'n Go beschikbaar op de [pagina]({NL_SUPPORTED_URL}).\n\n"
        "100% terugbetaling binnen 24 uur, geen vragen gesteld."
    ),
    "niveau": (
        "**Welk niveau heb ik nodig?**\n\n"
        "Ondersteund Spreken is voor jou als:\n"
        "• Je Nederlands begrijpt maar moeite hebt met spreken\n"
        "• Je A2, B1 of B2 niveau hebt en verder wilt groeien\n"
        "• Je geen dure cursus wilt maar wel structuur\n"
        "• Je liever oefent dan theorie leert\n"
        "• Je op je eigen tempo wilt werken in een rustige omgeving"
    ),
    "community": (
        "**Welke community toegang krijg ik?**\n\n"
        "Als lid heb je toegang tot:\n"
        "• Deze Discord server (je bent er al!)\n"
        "• WhatsApp groep\n"
        "• Telegram groep\n\n"
        "Je kunt oefenen met andere leerlingen en vragen stellen wanneer je wilt, "
        "naast de gratis maandag- en vrijdagse live lessen."
    ),
}


def build_en_supported_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🌟 Supported Speaking",
        description=(
            "Get the practice materials that help your English actually improve.\n\n"
            "Extended practice guides every Monday, Friday and Saturday. "
            "Five stories with audio every month. Everything you need to keep improving "
            "between the free live lessons.\n\n"
            "**€4.99 / month** — or €49.90/year (2 months free)\n\n"
            "**What you get:**\n"
            "📖 Supporter edition guides every Mon, Fri & Sat\n"
            "📚 5 B1-level stories with audio every month\n"
            "🎯 Error recognition training in every guide\n"
            "💬 Community access — Discord, WhatsApp, Telegram\n\n"
            f"[**Start today for €4.99 →**]({EN_SUPPORTED_URL})\n\n"
            "100% refund within 24 hours · cancel anytime · no commitment\n\n"
            "Questions? Use the dropdown below."
        ),
    )
    embed.set_footer(text="supported-speaking:en:v1")
    return embed


def build_nl_supported_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🌟 Ondersteund Spreken",
        description=(
            "Elke week live Nederlands oefenen met Lucas. In een kleine groep, op jouw niveau.\n\n"
            "Geen cursus om doorheen te werken. Gewoon wekelijks live spreken met mensen op jouw niveau, "
            "met oefenmateriaal dat je echt verder helpt.\n\n"
            "**€7,99 / maand** — of €79,90/jaar (2 maanden gratis)\n\n"
            "**Wat je krijgt:**\n"
            "🎙️ Live sessie elke maandag 19:00 CET\n"
            "📖 Leden oefengids elke vrijdag\n"
            "📅 Spreekonderwerp elke zondag\n"
            "📚 Maandelijks verhaal met audio\n\n"
            f"[**Begin vandaag voor €7,99 →**]({NL_SUPPORTED_URL})\n\n"
            "100% terugbetaling binnen 24 uur · op elk moment opzegbaar\n\n"
            "Vragen? Gebruik het menu hieronder."
        ),
    )
    embed.set_footer(text="supported-speaking:nl:v1")
    return embed


# ==============================================================
# VIEWS
# ==============================================================

class EnPrivateFAQSelect(discord.ui.Select):
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
            min_values=1, max_values=1,
            options=options,
            custom_id="private_lessons:faq:en:v1",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            EN_PRIVATE_FAQS.get(self.values[0], "Answer not found."), ephemeral=True
        )


class NlPrivateFAQSelect(discord.ui.Select):
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
            min_values=1, max_values=1,
            options=options,
            custom_id="private_lessons:faq:nl:v1",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            NL_PRIVATE_FAQS.get(self.values[0], "Antwoord niet gevonden."), ephemeral=True
        )


class EnSupportedFAQSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="What is Supported Speaking?", value="whatisit", emoji="🌟"),
            discord.SelectOption(label="What are the practice guides?", value="guides", emoji="📖"),
            discord.SelectOption(label="How do I join?", value="joining", emoji="🔗"),
            discord.SelectOption(label="What level do I need?", value="level", emoji="🎯"),
            discord.SelectOption(label="What community access do I get?", value="community", emoji="💬"),
        ]
        super().__init__(
            placeholder="Questions? Select one…",
            min_values=1, max_values=1,
            options=options,
            custom_id="supported_speaking:faq:en:v1",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            EN_SUPPORTED_FAQS.get(self.values[0], "Answer not found."), ephemeral=True
        )


class NlSupportedFAQSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="Wat is Ondersteund Spreken?", value="watishet", emoji="🌟"),
            discord.SelectOption(label="Hoe werkt de live sessie?", value="sessie", emoji="🎙️"),
            discord.SelectOption(label="Hoe meld ik me aan?", value="aanmelden", emoji="🔗"),
            discord.SelectOption(label="Welk niveau heb ik nodig?", value="niveau", emoji="🎯"),
            discord.SelectOption(label="Welke community toegang krijg ik?", value="community", emoji="💬"),
        ]
        super().__init__(
            placeholder="Vragen? Kies er een…",
            min_values=1, max_values=1,
            options=options,
            custom_id="supported_speaking:faq:nl:v1",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            NL_SUPPORTED_FAQS.get(self.values[0], "Antwoord niet gevonden."), ephemeral=True
        )


class EnLessonsView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(EnPrivateFAQSelect())


class NlLessonsView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(NlPrivateFAQSelect())


class EnSupportedView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(EnSupportedFAQSelect())


class NlSupportedView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(NlSupportedFAQSelect())


# ==============================================================
# PUBLISHER
# ==============================================================

class PrivateLessonsPublisher:
    def __init__(self, *, bot: discord.Client, repo) -> None:
        self._bot = bot
        self._repo = repo

    async def publish_english(self) -> None:
        await self._publish(
            channel_id=EN_PRIVATE_CHANNEL_ID,
            embed=build_en_private_embed(),
            view=EnLessonsView(),
            kv_key=KV_EN_PRIVATE_MSG,
            guild_id=None,
        )

    async def publish_dutch(self) -> None:
        await self._publish(
            channel_id=NL_PRIVATE_CHANNEL_ID,
            embed=build_nl_private_embed(),
            view=NlLessonsView(),
            kv_key=KV_NL_PRIVATE_MSG,
            guild_id=None,
        )

    async def publish_en_supported(self) -> None:
        await self._publish(
            channel_id=EN_SUPPORTED_CHANNEL_ID,
            embed=build_en_supported_embed(),
            view=EnSupportedView(),
            kv_key=KV_EN_SUPPORTED_MSG,
            guild_id=None,
        )

    async def publish_nl_supported(self) -> None:
        await self._publish(
            channel_id=NL_SUPPORTED_CHANNEL_ID,
            embed=build_nl_supported_embed(),
            view=NlSupportedView(),
            kv_key=KV_NL_SUPPORTED_MSG,
            guild_id=None,
        )

    async def _publish(
        self,
        *,
        channel_id: int,
        embed: discord.Embed,
        view: discord.ui.View,
        kv_key: str,
        guild_id: int | None,
    ) -> None:
        channel = self._bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self._bot.fetch_channel(channel_id)
            except Exception:
                log.warning("Publisher: could not fetch channel %s", channel_id)
                return

        if not isinstance(channel, discord.TextChannel):
            log.warning("Publisher: channel %s is not a TextChannel", channel_id)
            return

        gid = guild_id or channel.guild.id

        existing_id_raw = await self._repo.kv_get(gid, kv_key)
        if existing_id_raw:
            try:
                msg = await channel.fetch_message(int(existing_id_raw))
                await msg.edit(embed=embed, view=view)
                log.info("Publisher: updated message in channel %s", channel_id)
                return
            except Exception:
                log.warning("Publisher: could not edit message in %s, recreating", channel_id)

        try:
            sent = await channel.send(embed=embed, view=view)
            await self._repo.kv_set(gid, kv_key, str(sent.id))
            log.info("Publisher: posted message %s in channel %s", sent.id, channel_id)
            try:
                await sent.pin()
            except discord.Forbidden:
                log.warning("Publisher: missing pin permission in channel %s", channel_id)
            except Exception:
                log.warning("Publisher: could not pin in channel %s", channel_id)
        except Exception:
            log.exception("Publisher: failed to post in channel %s", channel_id)