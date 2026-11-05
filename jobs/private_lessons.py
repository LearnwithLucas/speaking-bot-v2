from __future__ import annotations

# jobs/private_lessons.py
import logging

import discord

log = logging.getLogger("jobs.private_lessons")

# ---- Channel IDs ----
EN_PRIVATE_CHANNEL_ID = 1483062284346458122
NL_PRIVATE_CHANNEL_ID = 1483061444399464540
EN_SUPPORTED_CHANNEL_ID = EN_PRIVATE_CHANNEL_ID
NL_SUPPORTED_CHANNEL_ID = NL_PRIVATE_CHANNEL_ID

# ---- Info page links ----
EN_PRIVATE_URL = "https://learnwithlucas.com/en/private-lessons/"
NL_PRIVATE_URL = "https://learnwithlucas.com/nl/priveles-nederlands/"
EN_SUPPORTED_URL = "https://learnwithlucas.com/en/supported-speaking/"
NL_SUPPORTED_URL = "https://learnwithlucas.com/nl/ondersteund-spreken/"

# ---- Checkout pages ----
# Stripe payment links are never posted publicly (learnwithlucas-links.md).
# Members pick a plan on the live offer page, which starts checkout and counts the lead.
EN_SUPPORTED_CHECKOUT_URL = "https://learnwithlucas.com/en/courses/supported-speaking/"
NL_SUPPORTED_CHECKOUT_URL = "https://learnwithlucas.com/nl/courses/ondersteund-spreken/"
NL_PRIVATE_CHECKOUT_URL = "https://learnwithlucas.com/nl/courses/priveles-nederlands/"

# ---- Booking links: Private lessons NL (all go to the offer page) ----
NL_TRIAL_LINK = NL_PRIVATE_CHECKOUT_URL
NL_BUILDER_LINK = NL_PRIVATE_CHECKOUT_URL
NL_INTENSIVE_LINK = NL_PRIVATE_CHECKOUT_URL

# ---- KV keys (bumped to force fresh posts) ----
KV_EN_PRIVATE_MSG  = "private_lessons_en_message_id_v3"
KV_NL_PRIVATE_MSG  = "private_lessons_nl_message_id_v3"
KV_EN_SUPPORTED_MSG = "supported_speaking_en_message_id_v4"
KV_NL_SUPPORTED_MSG = "supported_speaking_nl_message_id_v4"


# =======================================================
# FAQ CONTENT
# =======================================================

EN_PRIVATE_FAQS = {
    "cost": (
        "**What does it cost?**\n\n"
        "Trial session, 30 min: **€24** (one time)\n"
        "Speaking Builder, 4 x 60 min: **€189** (€47.25/hour)\n"
        "Confidence Intensive, 10 x 60 min: **€389** (€38.90/hour)\n\n"
        "Use them for work calls, small talk, presentations or exam speaking.\n\n"
        f"Not sure which fits? Start with the trial. [View all packages]({EN_PRIVATE_URL})"
    ),
    "booking": (
        "**How do I book?**\n\n"
        f"1. Go to [learnwithlucas.com/en/private-lessons]({EN_PRIVATE_URL})\n"
        "2. Pick a session or package and pay\n"
        "3. You receive a calendar link. Pick a time that works for you.\n"
        "4. We meet on Zoom or Discord. You don't need to set anything up.\n\n"
        "Questions before booking? Email english@learnwithlucas.com"
    ),
    "level": (
        "**What level do I need?**\n\n"
        "No minimum level. Private lessons work well if you:\n"
        "- Understand English but hesitate when it is time to speak\n"
        "- Want calm, personal feedback without an audience\n"
        "- Have a specific goal such as a job interview, presentation or daily confidence\n"
        "- Are preparing for IELTS, TOEFL, Cambridge or a workplace assessment\n\n"
        "The first session starts with a normal conversation. That's how we find your level."
    ),
    "format": (
        "**What happens in a session?**\n\n"
        "We start talking from the first minute. You can stop and think whenever you need to.\n\n"
        "- We talk about the topics you need English for\n"
        "- Feedback during or after the session, you choose\n"
        "- Short notes after the session if you want them\n"
        "- A session is 30 or 60 minutes, depending on what you booked\n"
        "- Platform: Zoom or Discord, your choice"
    ),
    "availability": (
        "**Is there space right now?**\n\n"
        "I keep the number of private students small.\n\n"
        "No space right now? You can still join the free community and practise here.\n\n"
        f"Check if there is space: [learnwithlucas.com/en/private-lessons]({EN_PRIVATE_URL})"
    ),
    "vs_supported": (
        "**Private lessons or Supported Speaking?**\n\n"
        "**Private lessons** are one on one with Lucas. You set the pace and the topics. "
        "They fit best if you have a specific goal. Trial from €24.\n\n"
        "**Supported Speaking** is a group membership for €7.99 a month. You get a live session "
        "every week (max 20 people), practice guides three times a week and stories with audio every month. "
        "It fits best if you want to practise every week for a low price.\n\n"
        "Many members use both."
    ),
    "exam_prep": (
        "**Can you help with IELTS, TOEFL or Cambridge?**\n\n"
        "Yes. Private lessons can focus on an exam, interview, presentation, work call "
        "or any moment where nerves stop you from speaking.\n\n"
        "Start with the 30 minute trial, or email english@learnwithlucas.com if you want to ask about a package first.\n\n"
        f"[View private lessons]({EN_PRIVATE_URL})"
    ),
    "payment": (
        "**How do I pay?**\n\n"
        "You pay with Stripe (credit or debit card).\n\n"
        f"All packages and checkout: [learnwithlucas.com/en/private-lessons]({EN_PRIVATE_URL})\n\n"
        "Questions about payment? Email english@learnwithlucas.com"
    ),
}

NL_PRIVATE_FAQS = {
    "kosten": (
        "**Wat kost het?**\n\n"
        f"Proefsessie, 30 min: **€28** (eenmalig) · [boek hier]({NL_TRIAL_LINK})\n"
        f"Speaking Builder, 4 x 60 min: **€219** · [boek hier]({NL_BUILDER_LINK})\n"
        f"Confidence Intensive, 10 x 60 min: **€469** · [boek hier]({NL_INTENSIVE_LINK})\n\n"
        "De Confidence Intensive kun je ook in twee delen betalen: €235 en €234.\n\n"
        "Examentraining voor Inburgering, KNM, ONA, NT2 en CNaVT zit in de gewone pakketten.\n\n"
        f"Niet zeker? Begin met de proefsessie. [Alle pakketten]({NL_PRIVATE_URL})"
    ),
    "boeken": (
        "**Hoe boek ik?**\n\n"
        f"1. Ga naar [learnwithlucas.com/nl/priveles-nederlands]({NL_PRIVATE_URL})\n"
        "2. Kies een sessie of pakket en betaal\n"
        "3. Je ontvangt een kalenderlink. Kies een tijd die voor jou werkt.\n"
        "4. We spreken af op Zoom of Discord. Je hoeft niets in te stellen.\n\n"
        "Vragen voor je boekt? Mail english@learnwithlucas.com"
    ),
    "niveau": (
        "**Welk niveau heb ik nodig?**\n\n"
        "Geen minimumniveau. Privélessen werken goed als je:\n"
        "- Nederlands begrijpt maar aarzelt als het tijd is om te spreken\n"
        "- Rustige, persoonlijke feedback wilt zonder publiek\n"
        "- Een specifiek doel hebt zoals een sollicitatie, presentatie of dagelijks zelfvertrouwen\n"
        "- Je voorbereidt op NT2, het inburgeringsexamen of een toets op je werk\n\n"
        "De eerste sessie begint met een gewoon gesprek. Zo ontdekken we samen je niveau."
    ),
    "format": (
        "**Wat gebeurt er in een sessie?**\n\n"
        "We praten vanaf de eerste minuut. Je mag altijd even stoppen en nadenken.\n\n"
        "- We praten over de onderwerpen waarvoor jij Nederlands nodig hebt\n"
        "- Feedback tijdens of na de sessie, jij kiest\n"
        "- Korte notities na de sessie als je die wilt\n"
        "- Een sessie duurt 30 of 60 minuten, net wat je hebt geboekt\n"
        "- Platform: Zoom of Discord, jouw keuze"
    ),
    "beschikbaarheid": (
        "**Is er nu plek?**\n\n"
        "Ik houd het aantal privéleerlingen klein.\n\n"
        "Is er nu geen plek? Dan kun je nog steeds meedoen met de gratis spreekgroep en hier oefenen.\n\n"
        f"Bekijk of er plek is: [learnwithlucas.com/nl/priveles-nederlands]({NL_PRIVATE_URL})"
    ),
    "bundels": (
        "**Zijn er bundels met Ondersteund Spreken?**\n\n"
        "Ja. De grotere pakketten bevatten gratis maanden Ondersteund Spreken:\n\n"
        f"Speaking Builder (4 uur, €219): **3 maanden Ondersteund Spreken gratis** · [boek]({NL_BUILDER_LINK})\n"
        f"Confidence Intensive (10 uur, €469): **6 maanden Ondersteund Spreken gratis** · [boek]({NL_INTENSIVE_LINK})\n\n"
        "Zo krijg je privéles en oefen je ook elke week in de groep."
    ),
    "examen": (
        "**Kunnen privélessen helpen bij NT2 of inburgering?**\n\n"
        "Ja. Examentraining voor Inburgering, KNM, ONA, NT2 en CNaVT zit in de gewone pakketten, "
        "zonder extra kosten.\n\n"
        "We oefenen met spreken, werk, de gemeente, de dokter of jouw examenonderdelen."
    ),
    "betaling": (
        "**Hoe betaal ik?**\n\n"
        "Je betaalt met Stripe (creditcard of debetkaart).\n\n"
        "Kies je pakket op de cursuspagina. Daar betaal je meteen.\n\n"
        f"[Naar de pakketten →]({NL_PRIVATE_CHECKOUT_URL})\n\n"
        "Vragen over betalen? Mail english@learnwithlucas.com"
    ),
}

EN_SUPPORTED_FAQS = {
    "whatisit": (
        "**What is Supported Speaking?**\n\n"
        "A weekly practice membership for **€7.99/month**.\n\n"
        "You get:\n"
        "- Live group speaking session every Saturday at 14:30 CEST (max 20 people)\n"
        "- Extended practice guides every Monday, Friday and Saturday\n"
        "- 5 B1-level stories with audio every month\n"
        "- Find-the-mistake exercises in every guide\n"
        "- Community access on Discord, WhatsApp and Telegram\n\n"
        "A private lesson with Lucas costs €24 for 30 minutes. "
        "This is a weekly live session and practice materials for €7.99 a month."
    ),
    "session": (
        "**When is the live session?**\n\n"
        "Every Saturday at 14:30 CEST on Discord.\n\n"
        "Session times by region:\n"
        "London: 13:30 BST\n"
        "Amsterdam / Brussels: 14:30 CEST\n"
        "Manila / Singapore / Malaysia: 20:30\n"
        "Indonesia (WIB): 19:30\n"
        "Indonesia (WITA): 20:30\n"
        "Sao Paulo: 09:30 BRT\n"
        "Colombia / Mexico: 07:30\n\n"
        "Max 20 people. You don't need to prepare. Join and speak."
    ),
    "guides": (
        "**What are the practice guides?**\n\n"
        "Every Monday, Friday and Saturday you get the supporter edition guide. "
        "They are longer versions of the free guides. Each one has:\n\n"
        "- 10 extra practice sentences\n"
        "- A paragraph with hidden mistakes to find and fix\n"
        "- Questions to test yourself\n"
        "- A quick recognition test\n\n"
        "That's about 3 times more than the free version."
    ),
    "joining": (
        "**How do I join?**\n\n"
        "Choose a plan on the course page and pay there.\n"
        f"[Monthly €7.99, 6 months €39.95 or yearly €79.90 →]({EN_SUPPORTED_CHECKOUT_URL})\n\n"
        "14 day money back. Cancel anytime."
    ),
    "level": (
        "**What level do I need?**\n\n"
        "Supported Speaking fits best at B1 or B2. "
        "That means you understand most English but hesitate when you have to speak.\n\n"
        "If you are a complete beginner, start with the free community first and join when you feel ready."
    ),
    "community": (
        "**What community access do I get?**\n\n"
        "Full access to:\n"
        "- This Discord server: all channels, voice rooms and live lessons\n"
        "- The WhatsApp group: daily words and short practice questions\n"
        "- The Telegram group: the same content as WhatsApp\n\n"
        "Most things happen on Discord. WhatsApp and Telegram are optional."
    ),
    "cancel": (
        "**Can I cancel anytime?**\n\n"
        "Yes. You can cancel anytime, and you don't need to give a reason.\n\n"
        "If it's not what you expected, you get your money back within 14 days."
    ),
    "vs_private": (
        "**Supported Speaking or private lessons?**\n\n"
        "**Supported Speaking** is a group membership for €7.99 a month. You get a live session "
        "every week (max 20 people), practice guides three times a week and stories with audio every month. "
        "It fits best if you want to practise every week for a low price.\n\n"
        "**Private lessons** are one on one with Lucas, from €24 for 30 minutes. "
        "You set the pace and the topics. They fit best if you have a specific goal.\n\n"
        "Many members use both."
    ),
}

NL_SUPPORTED_FAQS = {
    "watishet": (
        "**Wat is Ondersteund Spreken?**\n\n"
        "Een wekelijks oefenlidmaatschap voor **€11,99/maand**.\n\n"
        "Je krijgt:\n"
        "- Live sessies maandag 20:00 en woensdag 19:00 via WhatsApp\n"
        "- De ledenversie van de oefengids, elke vrijdag\n"
        "- Spreekonderwerp elke zondag (in 3 niveaus)\n"
        "- 5 verhalen met audio per maand\n"
        "- Kamers op A2, B1 en B2, plus emailfeedback\n\n"
        "Een privéles met Lucas kost €28 voor 30 minuten. "
        "Dit is elke week live Nederlands oefenen voor €11,99 per maand."
    ),
    "sessie": (
        "**Hoe werkt de live sessie?**\n\n"
        "Elke maandag om 20:00 en woensdag om 19:00, live via WhatsApp.\n\n"
        "- 0:00 tot 0:15: introductie, iedereen samen\n"
        "- 0:15 tot 0:45: breakout rooms per niveau (A2, B1 of B2), Lucas komt in elke kamer\n"
        "- 0:45 tot 1:00: afsluiting, we bespreken de fouten die vaak terugkwamen\n\n"
        "Max 20 personen per sessie. Rustige sfeer. "
        "Je kiest zelf welke avond past. Met Standaard kom je een keer per week, met Premium twee keer per week."
    ),
    "aanmelden": (
        "**Hoe meld ik me aan?**\n\n"
        "Kies je abonnement op de cursuspagina en betaal daar.\n"
        f"[Standaard €11,99, Premium €19,99 per maand, of een jaarplan vanaf €119,90 →]({NL_SUPPORTED_CHECKOUT_URL})\n\n"
        "14 dagen geld-terug-garantie. Op elk moment opzegbaar."
    ),
    "niveau": (
        "**Welk niveau heb ik nodig?**\n\n"
        "Ondersteund Spreken werkt het beste als je A2, B1 of B2 niveau hebt. "
        "Dat betekent dat je Nederlands redelijk begrijpt maar vastloopt als je moet spreken.\n\n"
        "Er zijn breakout rooms per niveau zodat je altijd oefent met mensen op jouw niveau. "
        "Je kiest zelf welke kamer je ingaat.\n\n"
        "Als je nog een complete beginner bent, begin dan met de gratis spreekgroep "
        "en sluit je aan als je er klaar voor bent."
    ),
    "community": (
        "**Welke community toegang krijg ik?**\n\n"
        "Volledige toegang tot:\n"
        "- Deze Discord server: alle kanalen, spraakkanalen en live lessen\n"
        "- Woord van de dag\n"
        "- Spreekpartner zoeken\n"
        "- Alle oefenmateriaal en gidsen\n\n"
        "Bijna alles gebeurt op Discord."
    ),
    "opzeggen": (
        "**Kan ik opzeggen?**\n\n"
        "Ja. Je kunt op elk moment opzeggen. Je hoeft niet te zeggen waarom.\n\n"
        "Is het niet wat je verwachtte? Dan krijg je binnen 14 dagen je geld terug."
    ),
    "verschil": (
        "**Wat is het verschil met privélessen?**\n\n"
        "**Ondersteund Spreken** is een groepslidmaatschap voor €11,99 per maand. "
        "Je oefent elke week live in een kleine groep op jouw niveau. "
        "Je krijgt ook oefenmateriaal, een spreekonderwerp op zondag, verhalen met audio en feedback per mail. "
        "Het past het best als je elke week wilt oefenen voor een lage prijs.\n\n"
        "**Privélessen** zijn een op een met Lucas, vanaf €28 voor 30 minuten. "
        "Jij bepaalt het tempo en de onderwerpen. "
        "Ze passen het best als je een specifiek doel hebt.\n\n"
        "Veel leden combineren beide."
    ),
    "gidsen": (
        "**Wat zijn de oefengidsen?**\n\n"
        "Elke vrijdag ontvang je de leden editie oefengids. "
        "Dit is een langere versie van de gratis gids. Je krijgt:\n\n"
        "- 10 extra oefenzinnen\n"
        "- Een alinea met verborgen fouten om te vinden en te verbeteren\n"
        "- Vragen om jezelf te testen\n"
        "- Een korte herkenningstest\n\n"
        "Dat is ongeveer 3 keer zoveel als de gratis versie."
    ),
}


# =======================================================
# EMBEDS
# =======================================================

def build_en_private_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎙️ Private English Lessons",
        description=(
            "One on one with Lucas, at your pace.\n\n"
            "For learners who understand English but want a quiet place to practise "
            "speaking, with personal help. You can stop and think whenever you need to.\n\n"
            "**Sessions and Packages**\n"
            f"🔹 Trial session, 30 min: **€24** · [book]({EN_PRIVATE_URL})\n"
            f"🔹 Speaking Builder, 4 x 60 min: **€189** · [book]({EN_PRIVATE_URL})\n"
            f"🔹 Confidence Intensive, 10 x 60 min: **€389** · [book]({EN_PRIVATE_URL})\n\n"
            "Platform: Zoom or Discord, your choice.\n\n"
            "Questions? Use the dropdown below or email english@learnwithlucas.com"
        ),
    )
    embed.set_footer(text="private-lessons:en:v3")
    return embed


def build_nl_private_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎙️ Privélessen Nederlands",
        description=(
            "Een op een met Lucas, in jouw tempo.\n\n"
            "Voor wie Nederlands begrijpt maar een rustige plek zoekt om te spreken, "
            "met persoonlijke hulp. Je mag altijd even stoppen en nadenken.\n\n"
            "**Sessies en pakketten**\n"
            f"🔹 Proefsessie, 30 min: **€28** · [boek]({NL_TRIAL_LINK})\n"
            f"🔹 Speaking Builder, 4 x 60 min: **€219** · [boek]({NL_BUILDER_LINK})\n"
            f"🔹 Confidence Intensive, 10 x 60 min: **€469** · [boek]({NL_INTENSIVE_LINK})\n\n"
            "Speaking Builder en Confidence Intensive bevatten gratis maanden Ondersteund Spreken.\n"
            "Examentraining is inbegrepen voor Inburgering, KNM, ONA, NT2 en CNaVT.\n"
            "Platform: Zoom of Discord, jouw keuze.\n\n"
            "Vragen? Gebruik het menu hieronder of mail english@learnwithlucas.com"
        ),
    )
    embed.set_footer(text="private-lessons:nl:v3")
    return embed


def build_en_supported_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🌟 Supported Speaking",
        description=(
            "Live speaking practice every week, in a small group at your level.\n\n"
            "You practise with the member guides during the week and join the live session on Saturday.\n\n"
            "**€7.99 a month**, €39.95 for 6 months (1 month free) or €79.90 a year (2 months free and 1 free private lesson)\n\n"
            "**What you get:**\n"
            "🎙️ Live session every Saturday 14:30 CEST on Discord (max 20 people)\n"
            "📖 Supporter edition guides every Mon, Fri and Sat\n"
            "📚 5 B1-level stories with audio every month\n"
            "🎯 Find-the-mistake exercises in every guide\n"
            "💬 Community access on Discord, WhatsApp and Telegram\n\n"
            f"[Choose a plan →]({EN_SUPPORTED_CHECKOUT_URL})\n"
            "\n"
            "14 day money back · cancel anytime\n\n"
            "Questions? Use the dropdown below."
        ),
    )
    embed.set_footer(text="supported-speaking:en:v4")
    return embed


def build_nl_supported_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🌟 Ondersteund Spreken",
        description=(
            "Elke week live Nederlands oefenen met Lucas. In een kleine groep, op jouw niveau.\n\n"
            "Je spreekt elke week live en oefent met materiaal op jouw niveau.\n\n"
            "**Standaard €11,99 per maand**, Premium €19,99 per maand, jaarplan vanaf €119,90\n\n"
            "**Wat je krijgt:**\n"
            "🎙️ Live sessies maandag 20:00 en woensdag 19:00 via WhatsApp\n"
            "📖 Oefengids elke vrijdag\n"
            "📅 Spreekonderwerp elke zondag (3 niveaus)\n"
            "📚 5 verhalen met audio per maand\n"
            "✉️ Emailfeedback\n\n"
            f"[Kies je abonnement →]({NL_SUPPORTED_CHECKOUT_URL})\n"
            "\n"
            "14 dagen geld terug · op elk moment opzegbaar\n\n"
            "Vragen? Gebruik het menu hieronder."
        ),
    )
    embed.set_footer(text="supported-speaking:nl:v4")
    return embed


# =======================================================
# FAQ SELECTS
# =======================================================

class EnPrivateFAQSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="What does it cost?", value="cost", emoji="💰"),
            discord.SelectOption(label="How do I book?", value="booking", emoji="📅"),
            discord.SelectOption(label="What level do I need?", value="level", emoji="🎯"),
            discord.SelectOption(label="What happens in a session?", value="format", emoji="🎙️"),
            discord.SelectOption(label="Is there space right now?", value="availability", emoji="🕐"),
            discord.SelectOption(label="Private lessons vs Supported Speaking", value="vs_supported", emoji="🔄"),
            discord.SelectOption(label="IELTS, TOEFL or Cambridge prep", value="exam_prep", emoji="📝"),
            discord.SelectOption(label="How do I pay?", value="payment", emoji="💳"),
        ]
        super().__init__(
            placeholder="Questions? Select one…",
            min_values=1, max_values=1,
            options=options,
            custom_id="private_lessons:faq:en:v2",
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
            discord.SelectOption(label="Bundels met Ondersteund Spreken", value="bundels", emoji="🎁"),
            discord.SelectOption(label="NT2 of inburgeringsexamen", value="examen", emoji="📝"),
            discord.SelectOption(label="Hoe betaal ik?", value="betaling", emoji="💳"),
        ]
        super().__init__(
            placeholder="Vragen? Kies er een…",
            min_values=1, max_values=1,
            options=options,
            custom_id="private_lessons:faq:nl:v2",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            NL_PRIVATE_FAQS.get(self.values[0], "Antwoord niet gevonden."), ephemeral=True
        )


class EnSupportedFAQSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="What is Supported Speaking?", value="whatisit", emoji="🌟"),
            discord.SelectOption(label="When is the live session?", value="session", emoji="🎙️"),
            discord.SelectOption(label="What are the practice guides?", value="guides", emoji="📖"),
            discord.SelectOption(label="How do I join?", value="joining", emoji="🔗"),
            discord.SelectOption(label="What level do I need?", value="level", emoji="🎯"),
            discord.SelectOption(label="What community access do I get?", value="community", emoji="💬"),
            discord.SelectOption(label="Can I cancel anytime?", value="cancel", emoji="✅"),
            discord.SelectOption(label="Supported Speaking vs private lessons", value="vs_private", emoji="🔄"),
        ]
        super().__init__(
            placeholder="Questions? Select one…",
            min_values=1, max_values=1,
            options=options,
            custom_id="supported_speaking:faq:en:v2",
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
            discord.SelectOption(label="Kan ik opzeggen?", value="opzeggen", emoji="✅"),
            discord.SelectOption(label="Verschil met privélessen", value="verschil", emoji="🔄"),
            discord.SelectOption(label="Wat zijn de oefengidsen?", value="gidsen", emoji="📖"),
        ]
        super().__init__(
            placeholder="Vragen? Kies er een…",
            min_values=1, max_values=1,
            options=options,
            custom_id="supported_speaking:faq:nl:v2",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            NL_SUPPORTED_FAQS.get(self.values[0], "Antwoord niet gevonden."), ephemeral=True
        )


# =======================================================
# VIEWS
# =======================================================

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


# =======================================================
# PUBLISHER
# =======================================================

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
