from __future__ import annotations

# jobs/private_lessons.py
import logging

import discord

log = logging.getLogger("jobs.private_lessons")

# ---- Channel IDs ----
EN_PRIVATE_CHANNEL_ID = 1483062284346458122
NL_PRIVATE_CHANNEL_ID = 1483061444399464540
EN_SUPPORTED_CHANNEL_ID = 1483065969310961776
NL_SUPPORTED_CHANNEL_ID = 1483065869465682083

# ---- Info page links ----
EN_PRIVATE_URL = "https://learnwithlucas.com/private-lessons/"
NL_PRIVATE_URL = "https://learnwithlucas.com/priveles-nederlands/"
EN_SUPPORTED_URL = "https://learnwithlucas.com/supported-speaking/"
NL_SUPPORTED_URL = "https://learnwithlucas.com/ondersteund-spreken/"

# ---- Payment links: Supported Speaking EN ----
SS_STRIPE_MONTHLY = "https://buy.stripe.com/fZueVe9L7b0j5wf4jYg7e0d"
SS_STRIPE_6MO     = "https://buy.stripe.com/6oU4gA4qN7O7gaTg2Gg7e0e"
SS_STRIPE_YEARLY  = "https://buy.stripe.com/8x25kE0ax8Sb6Aj3fUg7e0f"
SS_AIR_MONTHLY    = "https://pay.airwallex.com/nlhgyqcoi3ac"
SS_AIR_6MO        = "https://pay.airwallex.com/nlhgyqdho4yt"
SS_AIR_YEARLY     = "https://pay.airwallex.com/nlhgyqe8hl5q"

# ---- Payment links: Ondersteund Spreken NL ----
OS_STRIPE_MONTHLY = "https://buy.stripe.com/eVqcN6e1n1pJ5wf8Aeg7e0a"
OS_STRIPE_6MO     = "https://buy.stripe.com/fZu6oI2iFfgzgaTcQug7e0b"
OS_STRIPE_YEARLY  = "https://buy.stripe.com/6oU3cw7CZ0lF9Mv3fUg7e0c"
OS_AIR_MONTHLY    = "https://pay.airwallex.com/nlhgm8kz6gwd"
OS_AIR_YEARLY     = "https://pay.airwallex.com/nlhgm950ux71"

# ---- Payment links: Private lessons NL ----
NL_TRIAL_LINK        = "https://buy.stripe.com/00w8wQbTfb0j1fZ17Mg7e08"
NL_BUILDER_LINK      = "https://buy.stripe.com/6oU7sMe1ngkDf6P17Mg7e09"
NL_INTENSIVE_LINK    = "https://buy.stripe.com/7sY5kEe1necv7En7wag7e05"
NL_INTENSIVE_P1_LINK = "https://buy.stripe.com/cNi6oIbTf9Wf8Ir6s6g7e06"
NL_INTENSIVE_P2_LINK = "https://buy.stripe.com/3cI7sM1eBb0j5wfbMqg7e07"
NL_EXAM_BUILDER_LINK   = "https://buy.stripe.com/7sY00k7CZc4n4sb4jYg7e0g"
NL_EXAM_INTENSIVE_LINK = "https://buy.stripe.com/28E6oI6yVd8rf6P7wag7e0h"

# ---- KV keys (bumped to force fresh posts) ----
KV_EN_PRIVATE_MSG  = "private_lessons_en_message_id_v2"
KV_NL_PRIVATE_MSG  = "private_lessons_nl_message_id_v2"
KV_EN_SUPPORTED_MSG = "supported_speaking_en_message_id_v3"
KV_NL_SUPPORTED_MSG = "supported_speaking_nl_message_id_v3"


# =======================================================
# FAQ CONTENT
# =======================================================

EN_PRIVATE_FAQS = {
    "cost": (
        "**What does it cost?**\n\n"
        "Trial session - 30 min - **€22** (one time)\n"
        "Speaking Builder - 4 x 60 min - **€159** (save 10%)\n"
        "Confidence Intensive - 10 x 60 min - **€349** (save 20%)\n\n"
        "Exam prep:\n"
        "Exam Prep Builder - 4 x 60 min - **€179**\n"
        "Exam Prep Intensive - 10 x 60 min - **€379**\n\n"
        f"Not sure which fits? Start with the trial. [View all packages]({EN_PRIVATE_URL})"
    ),
    "booking": (
        "**How do I book?**\n\n"
        f"1. Go to [learnwithlucas.com/private-lessons]({EN_PRIVATE_URL})\n"
        "2. Pick a session or package and complete checkout\n"
        "3. You receive a calendar link. Pick a time that works for you.\n"
        "4. We meet via Zoom or Discord. No setup needed.\n\n"
        "Questions before booking? Email english@learnwithlucas.com"
    ),
    "level": (
        "**What level do I need?**\n\n"
        "No minimum level. Private lessons work well if you:\n"
        "- Understand English but hesitate when it is time to speak\n"
        "- Want calm, personal feedback without an audience\n"
        "- Have a specific goal such as a job interview, presentation or daily confidence\n"
        "- Are preparing for IELTS, TOEFL, Cambridge or a workplace assessment\n\n"
        "The first session always starts with real conversation to find your level together."
    ),
    "format": (
        "**What happens in a session?**\n\n"
        "Real conversation from the start. No scripts, no exams, pauses included.\n\n"
        "- We talk about topics relevant to you\n"
        "- Calm feedback during or after, whatever works best for you\n"
        "- Short follow-up notes after the session if useful\n"
        "- Sessions are 30 or 60 minutes depending on what you booked\n"
        "- Platform: Zoom or Discord, your choice"
    ),
    "availability": (
        "**Is there space right now?**\n\n"
        "Private lessons are kept limited so they stay calm and focused.\n\n"
        "If there is no space right now, you are always welcome in the free live lessons "
        "and the speaking community here.\n\n"
        f"Check current availability: [learnwithlucas.com/private-lessons]({EN_PRIVATE_URL})"
    ),
    "vs_supported": (
        "**Private lessons vs Supported Speaking - which is better?**\n\n"
        "**Private lessons** are one-on-one with Lucas. Fully personalised, your pace, "
        "your topics, your goals. Best for specific targets or people who want dedicated attention. "
        "Trial from €22.\n\n"
        "**Supported Speaking** is a group subscription at €7.99/month. Weekly live sessions "
        "with up to 20 people, practice guides three times a week, stories with audio every month. "
        "Best for consistent practice at a sustainable cost.\n\n"
        "Many members use both."
    ),
    "exam_prep": (
        "**Can you help with IELTS, TOEFL or Cambridge?**\n\n"
        "Yes. The exam prep packages focus specifically on the speaking component.\n\n"
        "Exam Prep Builder - 4 x 60 min - **€179**\n"
        "Exam Prep Intensive - 10 x 60 min - **€379**\n\n"
        "Sessions cover: test format, timing, structuring answers, common mistakes under pressure.\n\n"
        f"[Book exam prep]({EN_PRIVATE_URL})"
    ),
    "payment": (
        "**How do I pay?**\n\n"
        "Payment is via Stripe (credit card, debit card).\n\n"
        f"All packages and checkout: [learnwithlucas.com/private-lessons]({EN_PRIVATE_URL})\n\n"
        "Questions about payment? Email english@learnwithlucas.com"
    ),
}

NL_PRIVATE_FAQS = {
    "kosten": (
        "**Wat kost het?**\n\n"
        f"Proefsessie - 30 min - **€28** (eenmalig) - [boek hier]({NL_TRIAL_LINK})\n"
        f"Speaking Builder - 4 x 60 min - **€219** - [boek hier]({NL_BUILDER_LINK})\n"
        f"Confidence Intensive - 10 x 60 min - **€469** - [boek hier]({NL_INTENSIVE_LINK})\n\n"
        "Confidence Intensive in twee delen:\n"
        f"Deel 1 - **€235** - [boek hier]({NL_INTENSIVE_P1_LINK})\n"
        f"Deel 2 - **€234** - [boek hier]({NL_INTENSIVE_P2_LINK})\n\n"
        "Examenvoorbereiding:\n"
        f"Builder - 4 x 60 min - **€249** - [boek hier]({NL_EXAM_BUILDER_LINK})\n"
        f"Intensive - 10 x 60 min - **€529** - [boek hier]({NL_EXAM_INTENSIVE_LINK})\n\n"
        f"Niet zeker? Begin met de proefsessie. [Alle pakketten]({NL_PRIVATE_URL})"
    ),
    "boeken": (
        "**Hoe boek ik?**\n\n"
        f"1. Ga naar [learnwithlucas.com/priveles-nederlands]({NL_PRIVATE_URL})\n"
        "2. Kies een sessie of pakket en rond de betaling af\n"
        "3. Je ontvangt een kalenderlink. Kies een tijd die voor jou werkt.\n"
        "4. We ontmoeten elkaar via Zoom of Discord. Geen installatie nodig.\n\n"
        "Vragen voor je boekt? Mail dutch@learnwithlucas.com"
    ),
    "niveau": (
        "**Welk niveau heb ik nodig?**\n\n"
        "Geen minimumniveau. Privélessen werken goed als je:\n"
        "- Nederlands begrijpt maar aarzelt als het tijd is om te spreken\n"
        "- Rustige, persoonlijke feedback wilt zonder publiek\n"
        "- Een specifiek doel hebt zoals een sollicitatie, presentatie of dagelijks zelfvertrouwen\n"
        "- Je voorbereidt op NT2, inburgeringsexamen of een zakelijke assessment\n\n"
        "De eerste sessie begint altijd met een echt gesprek om je niveau te ontdekken."
    ),
    "format": (
        "**Wat gebeurt er in een sessie?**\n\n"
        "Echt gesprek vanaf het begin. Geen scripts, geen examens, pauzes inbegrepen.\n\n"
        "- We praten over onderwerpen die voor jou relevant zijn\n"
        "- Rustige feedback tijdens of na de sessie, wat het beste werkt\n"
        "- Korte follow-up notities na de sessie als dat nuttig is\n"
        "- Sessies zijn 30 of 60 minuten afhankelijk van wat je hebt geboekt\n"
        "- Platform: Zoom of Discord, jouw keuze"
    ),
    "beschikbaarheid": (
        "**Is er nu plek?**\n\n"
        "Privélessen zijn beperkt zodat ze rustig en gefocust blijven.\n\n"
        "Als er nu geen plek is, ben je altijd welkom bij de gratis live lessen "
        "en de spreekgemeenschap hier.\n\n"
        f"Bekijk beschikbaarheid: [learnwithlucas.com/priveles-nederlands]({NL_PRIVATE_URL})"
    ),
    "bundels": (
        "**Zijn er bundels met Ondersteund Spreken?**\n\n"
        "Ja. De grotere pakketten bevatten gratis maanden Ondersteund Spreken:\n\n"
        f"Speaking Builder (4 uur, €219) - **3 maanden Ondersteund Spreken gratis** - [boek]({NL_BUILDER_LINK})\n"
        f"Confidence Intensive (10 uur, €469) - **6 maanden Ondersteund Spreken gratis** - [boek]({NL_INTENSIVE_LINK})\n\n"
        "Zo combineer je persoonlijke begeleiding met wekelijkse groepspraktijk."
    ),
    "examen": (
        "**Kunnen privélessen helpen bij NT2 of inburgering?**\n\n"
        "Ja. De examenvoorbereiding pakketten zijn specifiek gericht op spreektoetsen.\n\n"
        f"Examenvoorbereiding Builder - 4 x 60 min - **€249** - [boek hier]({NL_EXAM_BUILDER_LINK})\n"
        f"Examenvoorbereiding Intensive - 10 x 60 min - **€529** - [boek hier]({NL_EXAM_INTENSIVE_LINK})\n\n"
        "De sessies richten zich op het spreekonderdeel: testformaat, timing, veelgemaakte fouten "
        "en hoe je antwoorden structureert onder druk."
    ),
    "betaling": (
        "**Hoe betaal ik?**\n\n"
        "Betaling via Stripe (creditcard, debetkaart). Geen Airwallex voor privélessen.\n\n"
        "Directe betaallinks staan per pakket in het menu hierboven.\n\n"
        f"Alle pakketten: [learnwithlucas.com/priveles-nederlands]({NL_PRIVATE_URL})\n\n"
        "Vragen over betalen? Mail dutch@learnwithlucas.com"
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
        "- Error recognition training in every guide\n"
        "- Community access on Discord, WhatsApp and Telegram\n\n"
        "A private lesson with Lucas costs €22 for 30 minutes. "
        "This is a weekly live session and practice materials for €7.99 a month."
    ),
    "session": (
        "**When is the live session?**\n\n"
        "Every Saturday at 14:30 CEST. The first session is Saturday April 5, 2026.\n\n"
        "Session times by region:\n"
        "London - 13:30 BST\n"
        "Amsterdam / Brussels - 14:30 CEST\n"
        "Manila / Singapore / Malaysia - 20:30\n"
        "Indonesia (WIB) - 19:30\n"
        "Indonesia (WITA) - 20:30\n"
        "Sao Paulo - 09:30 BRT\n"
        "Colombia / Mexico - 07:30\n\n"
        "Max 20 people. No preparation needed. Just show up and speak."
    ),
    "guides": (
        "**What are the practice guides?**\n\n"
        "Every Monday, Friday and Saturday you get the supporter edition guide. "
        "These are extended versions of the free lesson guides and include:\n\n"
        "- 10 extra practice sentences\n"
        "- Error recognition paragraph (find and fix hidden mistakes)\n"
        "- Self-check questions\n"
        "- Quick recognition test\n\n"
        "Members get roughly 3 times more content than the free version."
    ),
    "joining": (
        "**How do I join?**\n\n"
        "EU / Netherlands:\n"
        f"Monthly €7.99 - [Stripe]({SS_STRIPE_MONTHLY})\n"
        f"6 months €39.95 - [Stripe]({SS_STRIPE_6MO})\n"
        f"Yearly €79.90 - [Stripe]({SS_STRIPE_YEARLY})\n\n"
        "Philippines / Indonesia / Malaysia / Thailand:\n"
        f"Monthly €7.99 - [GCash / DANA / Touch 'n Go]({SS_AIR_MONTHLY})\n"
        f"6 months €39.95 - [GCash / DANA / Touch 'n Go]({SS_AIR_6MO})\n"
        f"Yearly €79.90 - [GCash / DANA / Touch 'n Go]({SS_AIR_YEARLY})\n\n"
        "100% refund within 24 hours. Cancel anytime."
    ),
    "level": (
        "**What level do I need?**\n\n"
        "Supported Speaking works best at B1 or B2 level. "
        "That means you understand English reasonably well but hesitate when it is time to speak.\n\n"
        "If you are a complete beginner, start with the free live lessons first and join when you feel ready."
    ),
    "community": (
        "**What community access do I get?**\n\n"
        "Full access to:\n"
        "- This Discord server - all channels, voice rooms and live lessons\n"
        "- WhatsApp group - daily vocab and quick practice prompts\n"
        "- Telegram group - same content, different platform\n\n"
        "Discord is the main hub. WhatsApp and Telegram are optional extras."
    ),
    "cancel": (
        "**Can I cancel anytime?**\n\n"
        "Yes. Cancel anytime, no questions asked.\n\n"
        "There is also a 100% refund within 24 hours of joining if it turns out it is not what you expected. "
        "No forms, no waiting."
    ),
    "sea_payment": (
        "**Can I pay with GCash, DANA or Touch 'n Go?**\n\n"
        "Yes. If you are in the Philippines, Indonesia, Malaysia or Thailand, "
        "use the Airwallex links below.\n\n"
        f"Monthly €7.99 - [pay here]({SS_AIR_MONTHLY})\n"
        f"6 months €39.95 - [pay here]({SS_AIR_6MO})\n"
        f"Yearly €79.90 - [pay here]({SS_AIR_YEARLY})\n\n"
        "Accepted: GCash (PH), DANA (ID), Touch 'n Go (MY), Rabbit LINE Pay (TH)"
    ),
    "vs_private": (
        "**Supported Speaking vs private lessons - which is better?**\n\n"
        "**Supported Speaking** is a group subscription at €7.99/month. "
        "Weekly live sessions with up to 20 people, practice guides three times a week, "
        "stories with audio every month. Best for consistent affordable practice.\n\n"
        "**Private lessons** are one-on-one with Lucas from €22 for 30 minutes. "
        "Fully personalised, your pace, your topics. Best for specific goals.\n\n"
        "Many members use both."
    ),
}

NL_SUPPORTED_FAQS = {
    "watishet": (
        "**Wat is Ondersteund Spreken?**\n\n"
        "Een wekelijks oefenlidmaatschap voor **€11,99/maand**.\n\n"
        "Je krijgt:\n"
        "- Live sessie elke maandag of woensdag om 19:00 CET in een kleine groep\n"
        "- Leden editie oefengids elke vrijdag\n"
        "- Spreekonderwerp elke zondag (in 3 niveaus)\n"
        "- 5 verhalen met audio per maand\n"
        "- Discord community toegang\n\n"
        "Een privéles met Lucas kost €28 voor 30 minuten. "
        "Dit is elke week live Nederlands oefenen voor €11,99 per maand."
    ),
    "sessie": (
        "**Hoe werkt de live sessie?**\n\n"
        "Elke maandag en woensdag om 19:00 CET, een uur lang.\n\n"
        "- 0:00 tot 0:15 - introductie, iedereen samen\n"
        "- 0:15 tot 0:45 - breakout rooms op niveau (A2, B1 of B2), Lucas bezoekt elke kamer\n"
        "- 0:45 tot 1:00 - afsluiting, veelgemaakte fouten besproken\n\n"
        "Max 20 personen per sessie. Rustige sfeer. "
        "Je kiest zelf welke avond past. Je hoeft niet beide avonden te komen."
    ),
    "aanmelden": (
        "**Hoe meld ik me aan?**\n\n"
        "Nederland / Belgie / EU:\n"
        f"Maandelijks €11,99 - [Stripe]({OS_STRIPE_MONTHLY})\n"
        f"6 maanden €59,95 - [Stripe]({OS_STRIPE_6MO})\n"
        f"Jaarlijks €119,90 - [Stripe]({OS_STRIPE_YEARLY})\n\n"
        "Filipijnen / Indonesie / Maleisie / Thailand:\n"
        f"Maandelijks €11,99 - [GCash / DANA / Touch 'n Go]({OS_AIR_MONTHLY})\n"
        f"Jaarlijks €119,90 - [GCash / DANA / Touch 'n Go]({OS_AIR_YEARLY})\n\n"
        "100% terugbetaling binnen 24 uur. Op elk moment opzegbaar."
    ),
    "niveau": (
        "**Welk niveau heb ik nodig?**\n\n"
        "Ondersteund Spreken werkt het beste als je A2, B1 of B2 niveau hebt. "
        "Dat betekent dat je Nederlands redelijk begrijpt maar vastloopt als je moet spreken.\n\n"
        "Er zijn breakout rooms per niveau zodat je altijd oefent met mensen op jouw niveau. "
        "Je kiest zelf welke kamer je ingaat.\n\n"
        "Als je nog een complete beginner bent, begin dan met de gratis vrijdagsessie "
        "en sluit je aan als je er klaar voor bent."
    ),
    "community": (
        "**Welke community toegang krijg ik?**\n\n"
        "Volledige toegang tot:\n"
        "- Deze Discord server - alle kanalen, spraakkanalen en live lessen\n"
        "- Woord van de dag\n"
        "- Spreekpartner zoeken\n"
        "- Alle oefenmateriaal en gidsen\n\n"
        "De Discord is de hoofdhub voor alle leden."
    ),
    "opzeggen": (
        "**Kan ik opzeggen?**\n\n"
        "Ja. Op elk moment opzeggen, geen vragen gesteld.\n\n"
        "Er is ook 100% terugbetaling binnen 24 uur als het toch niet is wat je verwachtte. "
        "Geen formulieren, geen wachttijd."
    ),
    "sea_betaling": (
        "**Kan ik betalen met GCash, DANA of Touch 'n Go?**\n\n"
        "Ja. Als je in de Filipijnen, Indonesie, Maleisie of Thailand zit, "
        "gebruik dan de Airwallex links hieronder.\n\n"
        f"Maandelijks €11,99 - [betaal hier]({OS_AIR_MONTHLY})\n"
        f"Jaarlijks €119,90 - [betaal hier]({OS_AIR_YEARLY})\n\n"
        "Geaccepteerd: GCash (PH), DANA (ID), Touch 'n Go (MY), Rabbit LINE Pay (TH)"
    ),
    "verschil": (
        "**Wat is het verschil met privélessen?**\n\n"
        "**Ondersteund Spreken** is een groepslidmaatschap voor €11,99/maand. "
        "Wekelijks live oefenen in een kleine groep op jouw niveau, "
        "oefenmateriaal drie keer per week en verhalen met audio. "
        "Beste keuze voor consistente, betaalbare oefening.\n\n"
        "**Privélessen** zijn een-op-een met Lucas vanaf €28 voor 30 minuten. "
        "Volledig gepersonaliseerd, jouw tempo, jouw onderwerpen. "
        "Beste keuze voor een specifiek doel.\n\n"
        "Veel leden combineren beide."
    ),
    "gidsen": (
        "**Wat zijn de oefengidsen?**\n\n"
        "Elke vrijdag ontvang je de leden editie oefengids. "
        "Dit is een uitgebreide versie van de gratis gids met:\n\n"
        "- 10 extra oefenzinnen\n"
        "- Foutherkenning alinea (vind en verbeter verborgen fouten)\n"
        "- Zelfcontrole vragen\n"
        "- Snelle herkenningstest\n\n"
        "Leden krijgen ongeveer 3 keer meer inhoud dan de gratis versie."
    ),
}


# =======================================================
# EMBEDS
# =======================================================

def build_en_private_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎙️ Private English Lessons",
        description=(
            "One on one. Calm. Focused. Yours.\n\n"
            "For learners who understand English but want a quiet space to practice "
            "speaking with personal guidance. No scripts. No exams. Pauses included.\n\n"
            "**Sessions and Packages**\n"
            f"🔹 Trial session - 30 min - **€22** - [book]({EN_PRIVATE_URL})\n"
            f"🔹 Speaking Builder - 4 x 60 min - **€159** - [book]({EN_PRIVATE_URL})\n"
            f"🔹 Confidence Intensive - 10 x 60 min - **€349** - [book]({EN_PRIVATE_URL})\n"
            f"🔹 Exam Prep Builder - 4 x 60 min - **€179** - [book]({EN_PRIVATE_URL})\n"
            f"🔹 Exam Prep Intensive - 10 x 60 min - **€379** - [book]({EN_PRIVATE_URL})\n\n"
            "Platform: Zoom or Discord, your choice.\n\n"
            "Questions? Use the dropdown below or email english@learnwithlucas.com"
        ),
    )
    embed.set_footer(text="private-lessons:en:v2")
    return embed


def build_nl_private_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎙️ Privélessen Nederlands",
        description=(
            "Een op een. Rustig. Gericht. Voor jou.\n\n"
            "Voor leerlingen die Nederlands begrijpen maar een rustige plek willen om te spreken "
            "met persoonlijke begeleiding. Geen scripts. Geen examens. Pauzes inbegrepen.\n\n"
            "**Sessies en Pakketten**\n"
            f"🔹 Proefsessie - 30 min - **€28** - [boek]({NL_TRIAL_LINK})\n"
            f"🔹 Speaking Builder - 4 x 60 min - **€219** - [boek]({NL_BUILDER_LINK})\n"
            f"🔹 Confidence Intensive - 10 x 60 min - **€469** - [boek]({NL_INTENSIVE_LINK})\n"
            f"🔹 Examenvoorbereiding Builder - 4 x 60 min - **€249** - [boek]({NL_EXAM_BUILDER_LINK})\n"
            f"🔹 Examenvoorbereiding Intensive - 10 x 60 min - **€529** - [boek]({NL_EXAM_INTENSIVE_LINK})\n\n"
            "Speaking Builder en Confidence Intensive bevatten gratis maanden Ondersteund Spreken.\n"
            "Platform: Zoom of Discord, jouw keuze.\n\n"
            "Vragen? Gebruik het menu hieronder of mail dutch@learnwithlucas.com"
        ),
    )
    embed.set_footer(text="private-lessons:nl:v2")
    return embed


def build_en_supported_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🌟 Supported Speaking",
        description=(
            "Weekly live speaking practice. In a small group. At your level.\n\n"
            "Not a course. No fixed schedule. Just weekly practice with better materials "
            "and a live session every Saturday.\n\n"
            "**€7.99 / month** — or €39.95 for 6 months (1 month free) — or €79.90/year (2 months free)\n\n"
            "**What you get:**\n"
            "🎙️ Live session every Saturday 14:30 CEST (max 20 people)\n"
            "📖 Supporter edition guides every Mon, Fri and Sat\n"
            "📚 5 B1-level stories with audio every month\n"
            "🎯 Error recognition training in every guide\n"
            "💬 Community access on Discord, WhatsApp and Telegram\n\n"
            f"EU: [Monthly €7.99]({SS_STRIPE_MONTHLY}) · [6 months €39.95]({SS_STRIPE_6MO}) · [Yearly €79.90]({SS_STRIPE_YEARLY})\n"
            f"SEA: [Monthly €7.99]({SS_AIR_MONTHLY}) · [6 months €39.95]({SS_AIR_6MO}) · [Yearly €79.90]({SS_AIR_YEARLY})\n\n"
            "100% refund within 24 hours · cancel anytime\n\n"
            "Questions? Use the dropdown below."
        ),
    )
    embed.set_footer(text="supported-speaking:en:v3")
    return embed


def build_nl_supported_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🌟 Ondersteund Spreken",
        description=(
            "Elke week live Nederlands oefenen met Lucas. In een kleine groep, op jouw niveau.\n\n"
            "Geen cursus. Geen vast schema. Gewoon wekelijks live spreken "
            "met oefenmateriaal dat je echt verder helpt.\n\n"
            "**€11,99 / maand** — of €59,95 voor 6 maanden (1 maand gratis) — of €119,90/jaar (2 maanden gratis)\n\n"
            "**Wat je krijgt:**\n"
            "🎙️ Live sessie elke maandag of woensdag 19:00 CET\n"
            "📖 Leden oefengids elke vrijdag\n"
            "📅 Spreekonderwerp elke zondag (3 niveaus)\n"
            "📚 5 verhalen met audio per maand\n"
            "💬 Discord community toegang\n\n"
            f"EU: [Maandelijks €11,99]({OS_STRIPE_MONTHLY}) · [6 maanden €59,95]({OS_STRIPE_6MO}) · [Jaarlijks €119,90]({OS_STRIPE_YEARLY})\n"
            f"SEA: [Maandelijks €11,99]({OS_AIR_MONTHLY}) · [Jaarlijks €119,90]({OS_AIR_YEARLY})\n\n"
            "100% terugbetaling binnen 24 uur · op elk moment opzegbaar\n\n"
            "Vragen? Gebruik het menu hieronder."
        ),
    )
    embed.set_footer(text="supported-speaking:nl:v3")
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
            discord.SelectOption(label="GCash, DANA or Touch 'n Go payment", value="sea_payment", emoji="💳"),
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
            discord.SelectOption(label="GCash, DANA of Touch 'n Go betaling", value="sea_betaling", emoji="💳"),
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