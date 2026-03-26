from __future__ import annotations

# commands/ask_jerry.py
import logging

import discord
from discord.ext import commands

log = logging.getLogger("commands.ask_jerry")

ASK_JERRY_CHANNEL_ID = 1486110286523138108  # 🦆┃ask-jerry
KV_ASK_JERRY_MSG_ID = "ask_jerry_hub_message_id"
NL_ASK_JERRY_CHANNEL_ID = 1486110860786270438  # 🦆┃vraag-het-jerry
KV_NL_ASK_JERRY_MSG_ID = "ask_jerry_nl_hub_message_id"

EN_COMMUNITY_INVITE = "https://discord.gg/uhz4DZMPYv"
EN_SUPPORTED_SPEAKING_URL = "https://learnwithlucas.com/supported-speaking/"
EN_PRIVATE_LESSONS_URL = "https://learnwithlucas.com/private-lessons"
EN_FREE_GUIDES_URL = "https://learnwithlucas.com/nederlandse-leermaterialen/"
EN_FREE_BOOK_URL = "https://learnwithlucas.com/gratis-maandelijks-boek/"
TIKTOK_URL = "https://www.tiktok.com/@learnwithlucas"
YOUTUBE_EN_URL = "https://www.youtube.com/@LearnEnglishWithLucas"


# =====================
# FAQ DATA
# category -> list of (question_label, answer)
# =====================

FAQ: dict[str, dict] = {
    "supported_speaking": {
        "label": "📖 Supported Speaking",
        "emoji": "📖",
        "questions": [
            (
                "What is Supported Speaking?",
                "Supported Speaking is a weekly practice membership for €7.99/month.\n\n"
                "Every Monday, Friday and Saturday you get the extended supporter edition practice guide. "
                "You also get 5 B1-level English stories with audio every month, error recognition training in every guide, "
                "and full community access on Discord, WhatsApp and Telegram.\n\n"
                "It is not a course. There is no fixed schedule you have to follow. "
                "You practice at your own pace with better materials than the free version.\n\n"
                f"More info: {EN_SUPPORTED_SPEAKING_URL}"
            ),
            (
                "How much does it cost?",
                "Supported Speaking costs **€7.99 per month**, **€39.95 for 6 months** (1 month free), or **€79.90 per year** (2 months free).\n\n"
                "For comparison: a private lesson with Lucas costs €22 for 30 minutes. "
                "This is weekly practice for less than one coffee a week.\n\n"
                "100% refund within 24 hours if it is not what you expected. No questions asked.\n\n"
                f"[Start today]({EN_SUPPORTED_SPEAKING_URL})"
            ),
            (
                "What do I get every week?",
                "Every week you get:\n"
                "• Monday, Friday and Saturday: the supporter edition practice guide\n"
                "• Error recognition paragraphs — find and fix hidden mistakes\n"
                "• Extra practice sentences (3x more than the free version)\n"
                "• Self-check questions\n\n"
                "Every month you also get 5 B1-level English stories with audio. "
                "Read and listen at the same time, written specifically for intermediate learners."
            ),
            (
                "Is there a live session?",
                "The free live lessons run on Monday, Wednesday, Thursday, Friday and Saturday. "
                "Those are open to everyone — no membership needed.\n\n"
                "Supported Speaking gives you the extended practice guides to prepare and follow up. "
                "The live sessions themselves are free and always will be."
            ),
            (
                "Can I cancel anytime?",
                "Yes. Cancel anytime, no questions asked.\n\n"
                "There is also a 100% refund within 24 hours of joining if it turns out it is not what you expected. "
                "No forms, no waiting.\n\n"
                f"[Join here]({EN_SUPPORTED_SPEAKING_URL})"
            ),
            (
                "What level do I need?",
                "Supported Speaking works best if you are at B1 or B2 level. "
                "That means you understand English reasonably well but freeze or hesitate when it is time to speak.\n\n"
                "If you are a complete beginner, start with the free live lessons first and join when you feel ready."
            ),
            (
                "How is it different from the free guides?",
                "The free guides include the key phrases and 5 practice sentences.\n\n"
                "The supporter edition adds:\n"
                "• 10 extra practice sentences\n"
                "• An error recognition paragraph (find and fix hidden mistakes)\n"
                "• Self-check questions\n"
                "• A quick recognition test\n\n"
                "That is roughly 3 times more content per guide."
            ),
            (
                "Can I pay with GCash, DANA or Touch n Go?",
                "Yes. If you are based in the Philippines, Indonesia, Malaysia or Thailand, "
                "there are Airwallex payment links that accept GCash, DANA and Touch 'n Go.\n\n"
                f"Go to {EN_SUPPORTED_SPEAKING_URL} and scroll down to the payment section. "
                "You will see the SEA payment option there."
            ),
        ],
    },
    "private_lessons": {
        "label": "🎙️ Private Lessons",
        "emoji": "🎙️",
        "questions": [
            (
                "What are private lessons?",
                "Private lessons are one-on-one sessions with Lucas, via Zoom or Discord.\n\n"
                "No scripts, no exams, pauses included. Real conversation from the start. "
                "The goal is calm, personal speaking practice with someone who actually listens and gives you useful feedback.\n\n"
                f"More info: {EN_PRIVATE_LESSONS_URL}"
            ),
            (
                "How much do private lessons cost?",
                "**Trial session** — 30 minutes — €22 (one time)\n"
                "**Speaking Builder** — 4 x 60 minutes — €159 (save 10%)\n"
                "**Confidence Intensive** — 10 x 60 minutes — €349 (save 20%)\n\n"
                "**Exam prep:**\n"
                "Exam Prep Builder — 4 x 60 minutes — €179\n"
                "Exam Prep Intensive — 10 x 60 minutes — €379\n\n"
                "Not sure which fits? Start with the trial. "
                f"[View all packages]({EN_PRIVATE_LESSONS_URL})"
            ),
            (
                "What level do I need for private lessons?",
                "No minimum level. Private lessons work well if you:\n"
                "• Understand English but hesitate when it is time to speak\n"
                "• Want calm, personal feedback without an audience\n"
                "• Have a specific goal like a job interview, a presentation, or daily confidence\n"
                "• Are preparing for IELTS, TOEFL, Cambridge or a workplace assessment\n\n"
                "The first session always starts with real conversation so you can find your level together."
            ),
            (
                "How do I book a private lesson?",
                f"Go to {EN_PRIVATE_LESSONS_URL} and pick a session or package.\n\n"
                "After you pay you get a calendar link. Pick a time that works for you. "
                "Then you meet via Zoom or Discord. No setup needed.\n\n"
                "Questions before booking? Email english@learnwithlucas.com"
            ),
            (
                "What happens in a session?",
                "Real conversation from the start. You talk about topics that are relevant to you.\n\n"
                "Lucas gives calm feedback during or after the session, whichever works best for you. "
                "There is a short follow-up after the session if it is useful.\n\n"
                "Sessions are 30 or 60 minutes depending on what you booked. "
                "No scripts, no grammar drills unless you ask for them."
            ),
            (
                "Is there space right now?",
                "Private lessons are kept limited so they stay calm and focused.\n\n"
                "If there is no space right now, you are always welcome in the free live lessons "
                "and the speaking community here.\n\n"
                f"Check current availability at {EN_PRIVATE_LESSONS_URL}"
            ),
        ],
    },
    "speaking_tips": {
        "label": "💬 Speaking Tips",
        "emoji": "💬",
        "questions": [
            (
                "I understand English but freeze when I speak. What do I do?",
                "That is the most common pattern and it makes sense. "
                "Understanding and speaking use different parts of your brain.\n\n"
                "The only fix is speaking more, but the key is speaking in low-pressure situations first. "
                "Not a test. Not a presentation. Just a real conversation where mistakes are fine.\n\n"
                "Start here: join the voice channels and say one sentence. That is it. That is the whole exercise."
            ),
            (
                "How do I stop switching back to my first language?",
                "Switching happens when the pressure is too high or the word is not there yet.\n\n"
                "Two things help:\n"
                "1. Lower the stakes. If you are practicing with people who understand that you are learning, "
                "there is no reason to switch.\n"
                "2. Learn to buy time. Phrases like 'how do I say this', 'give me a second' or 'I think the word is' "
                "keep you in English while you find the word.\n\n"
                "You do not need perfect sentences. You need to stay in English longer each time."
            ),
            (
                "How do I build confidence in speaking?",
                "Confidence comes after doing it, not before.\n\n"
                "Most people wait until they feel ready. That feeling does not come on its own. "
                "It comes from speaking enough times that it starts to feel normal.\n\n"
                "The practical answer: speak a little every day in a low-pressure setting. "
                "This server, the voice channels, the live lessons. "
                "Not to perform. Just to get used to the sound of your own voice in English."
            ),
            (
                "How do I improve my pronunciation?",
                "Pronunciation improves through listening and speaking together, not through rules.\n\n"
                "Listen to a lot of English at your level. Repeat sentences out loud, not just words. "
                "Record yourself occasionally and compare.\n\n"
                "The goal is not a native accent. The goal is being clearly understood. "
                "Most people are more understandable than they think."
            ),
            (
                "How do I remember new vocabulary?",
                "You remember words best when you use them in real sentences, not when you memorise lists.\n\n"
                "When you learn a new word, use it in a sentence that is relevant to your life. "
                "Say it out loud. Use it in a conversation the same day if you can.\n\n"
                "Check the word of the day channel every morning. That is what it is there for."
            ),
            (
                "How often should I practice to improve?",
                "A little every day beats a long session once a week.\n\n"
                "15 minutes of real speaking practice daily will move you forward faster than "
                "two hours on a Saturday. The consistency is what builds the habit.\n\n"
                "Use the voice channels. Join the live lessons. Press the partner button when you are free. "
                "Small steps add up."
            ),
            (
                "I feel embarrassed making mistakes. How do I get past that?",
                "Everyone feels this. It is not a sign that you are bad at English. "
                "It is a sign that you care.\n\n"
                "The people in this community are learning too. Nobody is judging your grammar. "
                "Mistakes are actually useful because they tell you what to fix.\n\n"
                "The only way to stop feeling embarrassed is to speak often enough that it becomes normal. "
                "That takes time. Give yourself that time."
            ),
            (
                "What is the difference between fluency and being a good speaker?",
                "Fluency means speaking without long pauses or needing to translate in your head. "
                "Being a good speaker means communicating clearly and connecting with the person you are talking to.\n\n"
                "You can be a good speaker without being fluent. "
                "Clear, honest, direct communication matters more than speed.\n\n"
                "This community is not about becoming fluent. It is about being able to speak without pressure getting in the way."
            ),
        ],
    },
    "community": {
        "label": "🏠 Community",
        "emoji": "🏠",
        "questions": [
            (
                "When are the free live lessons?",
                "Free live lessons run on Monday, Wednesday, Thursday, Friday and Saturday.\n\n"
                "Just show up. You can listen, say one sentence, or have a full conversation. "
                "Whatever feels right that day. No preparation needed."
            ),
            (
                "How do I find a speaking partner?",
                "Go to the looking-for-a-partner channel and press the button when you are free.\n\n"
                "If someone else is also free within 30 minutes, you both get a DM and can jump into a voice channel together. "
                "No scheduling, no planning. Just press the button when you feel like practicing."
            ),
            (
                "What are the voice channels for?",
                "The voice channels are open all day. You do not need to wait for a scheduled lesson.\n\n"
                "Drop In and Talk and Open Conversation are both available anytime. "
                "Join when you feel like it. Stay as long as you want. Leave whenever. No pressure."
            ),
            (
                "How do I use the /topics command?",
                "Type `/topics` anywhere in the server and a menu appears with 10 topic categories: "
                "family, food, hobbies, travel, work, learning, health, technology, emotions and future.\n\n"
                "Pick a topic and you get 10 conversation questions, one at a time, with useful vocabulary for each one. "
                "Use it as a starting point when you are not sure what to talk about."
            ),
            (
                "How do I look up a word?",
                "Type `/d word: [word]` anywhere in the server.\n\n"
                "You get the definition, part of speech, a usage example and similar words. "
                "The result posts in the channel so everyone can see it.\n\n"
                "There is also a dedicated vocabulary channel where all lookups appear."
            ),
            (
                "What is the word of the day?",
                "Every morning at 09:00 CET a new B1/B2 level word goes up in the word of the day channel.\n\n"
                "Each post includes the definition, a usage example and a prompt to use the word in the chat. "
                "It is a simple daily habit that helps vocabulary stick."
            ),
            (
                "Where can I find free learning materials?",
                f"Free practice guides: {EN_FREE_GUIDES_URL}\n"
                f"Free monthly story: {EN_FREE_BOOK_URL}\n"
                f"TikTok lessons: {TIKTOK_URL}\n"
                f"YouTube: {YOUTUBE_EN_URL}\n\n"
                "Everything on those pages is free. No sign-up needed for most of it."
            ),
            (
                "How is this community different from other English communities?",
                "Most English communities focus on grammar or vocabulary. This one focuses on speaking.\n\n"
                "The whole setup, the voice channels, the partner finder, the live lessons, the practice guides, "
                "is built around one idea: the best way to get better at speaking is to speak more, "
                "in a calm environment where making mistakes is part of the process.\n\n"
                "No pressure, no tests, no leaderboard for grammar. Just speaking practice."
            ),
        ],
    },
    "grammar": {
        "label": "📝 Grammar",
        "emoji": "📝",
        "questions": [
            (
                "When do I use 'a' vs 'an'?",
                "Use **a** before words that start with a consonant sound.\n"
                "Use **an** before words that start with a vowel sound.\n\n"
                "The key word is *sound*, not spelling.\n\n"
                "**a** dog, **a** university (starts with 'yoo' sound), **a** European\n"
                "**an** apple, **an** hour (the h is silent), **an** honest mistake\n\n"
                "Say the word out loud. If it starts with a vowel sound, use 'an'."
            ),
            (
                "What is the difference between 'make' and 'do'?",
                "This is one of the most common mistakes and there is no perfect rule, "
                "but here is the pattern that helps:\n\n"
                "**Make** is used when you produce or create something.\n"
                "Make a decision, make a mistake, make coffee, make a plan\n\n"
                "**Do** is used for actions, tasks and activities.\n"
                "Do the dishes, do your homework, do exercise, do your best\n\n"
                "When in doubt: if there is a physical or creative result, use make. If it is a task or activity, use do."
            ),
            (
                "When do I use present perfect vs simple past?",
                "**Simple past**: something happened at a specific time in the past.\n"
                "I *went* to London in 2019. She *called* yesterday.\n\n"
                "**Present perfect**: the connection to now is more important than when it happened.\n"
                "I *have been* to London (at some point, relevant now). She *has called* (and I still need to reply).\n\n"
                "If you can answer 'when exactly?', use simple past. "
                "If the timing does not matter but the result does, use present perfect."
            ),
            (
                "How do I use 'I' vs 'me'?",
                "Use **I** as the subject (the one doing the action).\n"
                "Use **me** as the object (the one receiving the action).\n\n"
                "**I** called him. He called **me**.\n\n"
                "The tricky part is when there are two people:\n"
                "*She and **I** went to the store.* (We are the subjects)\n"
                "*She told **him and me**.* (We are the objects)\n\n"
                "Quick test: remove the other person. 'Me went to the store' sounds wrong. "
                "'I went to the store' is right. So use 'I'."
            ),
            (
                "What is the difference between 'since' and 'for'?",
                "**For** is used with a duration, a length of time.\n"
                "I have lived here *for* three years. She studied *for* two hours.\n\n"
                "**Since** is used with a starting point.\n"
                "I have lived here *since* 2021. She has been studying *since* Monday.\n\n"
                "For = how long. Since = from when."
            ),
            (
                "When do I use 'in', 'on' and 'at' for time?",
                "**At** for specific times and fixed expressions.\n"
                "at 3 o'clock, at midnight, at the weekend\n\n"
                "**On** for days and dates.\n"
                "on Monday, on 14 March, on my birthday\n\n"
                "**In** for longer periods.\n"
                "in the morning, in March, in 2024, in the 20th century\n\n"
                "A useful way to remember: the more specific the time, the smaller the preposition. "
                "At is the most specific, in is the least."
            ),
            (
                "What is the difference between 'its' and 'it's'?",
                "**it's** = it is (or it has). The apostrophe replaces a letter.\n"
                "*It's raining.* (It is raining.) *It's been a long day.* (It has been.)\n\n"
                "**its** = belonging to it. No apostrophe.\n"
                "*The dog wagged its tail.* *The company lost its contract.*\n\n"
                "Quick test: replace it with 'it is'. If the sentence still makes sense, use it's. If not, use its."
            ),
            (
                "How do I use 'would', 'could' and 'should'?",
                "**Would**: used for conditional situations, polite requests and habits in the past.\n"
                "I *would* go if I had time. *Would* you help me? We *would* always eat together.\n\n"
                "**Could**: used for past ability, possibility and polite requests.\n"
                "She *could* swim when she was five. That *could* work. *Could* you repeat that?\n\n"
                "**Should**: used for advice and expectation.\n"
                "You *should* practice every day. He *should* be here by now.\n\n"
                "In speaking, 'could' and 'would' are your most useful polite tools. "
                "They soften almost any request."
            ),
        ],
    },
    "bot_features": {
        "label": "🤖 Server Features",
        "emoji": "🤖",
        "questions": [
            (
                "What does this bot do?",
                "Jerry The Duck runs most of the automated features in this server.\n\n"
                "That includes the word of the day, the speaking partner finder, encouragement messages in voice channels, "
                "the vocabulary lookup command, the topic cards, the FAQ you are reading right now, "
                "scheduled nudge messages and the product info channels.\n\n"
                "If something posts automatically, it is probably Jerry."
            ),
            (
                "How does the speaking partner finder work?",
                "Go to the looking-for-a-partner channel and press the button when you feel like practicing.\n\n"
                "You are marked as available for 30 minutes. If someone else presses the button in that same window, "
                "you both get a DM with a link to the voice channels.\n\n"
                "No scheduling. No slots. Just press it when you are free and see who is around."
            ),
            (
                "How do I use /topics?",
                "Type `/topics` anywhere and a dropdown appears with 10 categories.\n\n"
                "Pick one and you get question cards with navigation arrows. "
                "Each card shows a conversation question and useful vocabulary for that question. "
                "Everyone in the channel can browse the cards.\n\n"
                "Good for when the conversation has slowed down and you want a new direction."
            ),
            (
                "How do I use /d to look up a word?",
                "Type `/d word: [word]` and you get the definition, part of speech, example sentence and synonyms.\n\n"
                "The result posts in the channel so everyone benefits, not just you. "
                "You can also go directly to the vocabulary channel and use it there."
            ),
            (
                "What is the word of the day?",
                "Every morning at 09:00 CET a new word appears in the word of the day channel.\n\n"
                "B1/B2 level, practical vocabulary. Each post includes the definition, a usage example and "
                "an invitation to use the word in a sentence in the chat. "
                "Simple daily habit that helps new words stick."
            ),
            (
                "Why do I get messages in the voice channel?",
                "When you join a voice channel, Jerry sends a short message at 5 minutes and again at 30 minutes.\n\n"
                "At 5 minutes it is just an acknowledgement that you showed up. "
                "At 30 minutes it is a note recognising the effort.\n\n"
                "There are also occasional conversation starters posted in the channel chat. "
                "If you are not sure what to talk about, use /topics or the vocabulary channel."
            ),
            (
                "Where can I find info about Supported Speaking?",
                f"There is a dedicated channel with all the details and a FAQ dropdown. "
                f"Or go directly to {EN_SUPPORTED_SPEAKING_URL}"
            ),
            (
                "Where can I find info about private lessons?",
                f"There is a dedicated channel with all the details and a FAQ dropdown. "
                f"Or go directly to {EN_PRIVATE_LESSONS_URL}"
            ),
        ],
    },
}

NL_FAQ: dict[str, dict] = {
    "ondersteund_spreken": {
        "label": "📖 Ondersteund Spreken",
        "questions": [
            (
                "Wat is Ondersteund Spreken?",
                "Ondersteund Spreken is een wekelijks oefenlidmaatschap voor €11,99 per maand.\n\n"
                "Je krijgt elke maandag of woensdag een live sessie in een kleine groep op jouw niveau (A2, B1 of B2). "
                "Op vrijdag krijg je de uitgebreide leden oefengids. Op zondag het spreekonderwerp voor maandag. "
                "Elke maand ook een verhaal met audio.\n\n"
                "Geen cursus. Geen vast schema dat je moet volgen. "
                "Wekelijks live spreken in een rustige sfeer, op jouw eigen tempo.\n\n"
                f"Meer info: https://learnwithlucas.com/ondersteund-spreken/"
            ),
            (
                "Hoeveel kost het?",
                "Ondersteund Spreken kost **€11,99 per maand**, **€59,95 voor 6 maanden** (1 maand gratis) of **€119,90 per jaar** (2 maanden gratis).\n\n"
                "Ter vergelijking: een privéles met Lucas kost €28 voor 30 minuten. "
                "Dit is elke week live oefenen voor minder dan twee kopjes koffie per maand.\n\n"
                "100% terugbetaling binnen 24 uur als het toch niet is wat je verwachtte. Geen vragen gesteld.\n\n"
                "Begin vandaag: https://learnwithlucas.com/ondersteund-spreken/"
            ),
            (
                "Wat krijg ik elke week?",
                "Elke week:\n"
                "• Maandag of woensdag 19:00 CET: live sessie in een kleine groep op jouw niveau\n"
                "• Vrijdag: de uitgebreide leden oefengids met foutherkenning en extra oefenzinnen\n"
                "• Zondag: het spreekonderwerp voor de sessie van maandag of woensdag\n\n"
                "Elke maand ook een compleet B1-verhaal met audio. "
                "Lezen en luisteren tegelijk, speciaal geschreven voor leerlingen op jouw niveau."
            ),
            (
                "Hoe werkt de live sessie?",
                "Elke maandag en woensdag om 19:00 CET, één uur.\n\n"
                "• 0:00 tot 0:15 — introductie, iedereen samen\n"
                "• 0:15 tot 0:45 — breakout rooms op niveau (A2, B1 of B2), Lucas bezoekt elke kamer\n"
                "• 0:45 tot 1:00 — afsluiting, veelgemaakte fouten besproken\n\n"
                "Max 20 personen per sessie. Rustige sfeer. Je kiest zelf welke avond past, maandag of woensdag. "
                "Je hoeft niet beide te komen."
            ),
            (
                "Kan ik op elk moment opzeggen?",
                "Ja. Op elk moment opzeggen, geen vragen gesteld.\n\n"
                "Er is ook 100% terugbetaling binnen 24 uur als het toch niet is wat je verwachtte. "
                "Geen formulieren, geen wachttijd.\n\n"
                "Begin hier: https://learnwithlucas.com/ondersteund-spreken/"
            ),
            (
                "Welk niveau heb ik nodig?",
                "Ondersteund Spreken werkt het beste als je A2, B1 of B2 niveau hebt. "
                "Dat betekent dat je Nederlands redelijk begrijpt maar vastloopt als je moet spreken.\n\n"
                "Er zijn breakout rooms per niveau, dus je oefent altijd met mensen op jouw niveau. "
                "Je kiest zelf welke kamer je ingaat.\n\n"
                "Als je nog een complete beginner bent, begin dan met de gratis vrijdagsessie en sluit je aan als je er klaar voor bent."
            ),
            (
                "Kan ik betalen met GCash, DANA of Touch n Go?",
                "Ja. Als je in de Filipijnen, Indonesië, Maleisië of Thailand zit, "
                "zijn er Airwallex betaallinks die GCash, DANA en Touch 'n Go accepteren.\n\n"
                "Ga naar https://learnwithlucas.com/ondersteund-spreken/ en scroll naar het betalingsgedeelte. "
                "Daar zie je de SEA betaaloptie."
            ),
            (
                "Wat is het verschil met de gratis versie?",
                "De gratis gids heeft de kernuitleg en 5 oefenzinnen.\n\n"
                "De leden editie voegt toe:\n"
                "• 10 extra oefenzinnen\n"
                "• Een foutherkenning alinea (vind en verbeter verborgen fouten)\n"
                "• Zelfcontrole vragen\n"
                "• Een snelle herkenningstest\n\n"
                "Dat is ongeveer 3 keer meer inhoud per gids. Plus de live sessie en het maandelijkse verhaal."
            ),
        ],
    },
    "priveles": {
        "label": "🎙️ Privélessen",
        "questions": [
            (
                "Wat zijn privélessen?",
                "Privélessen zijn een-op-een sessies met Lucas, via Zoom of Discord.\n\n"
                "Geen scripts, geen examens, pauzes inbegrepen. Echt gesprek vanaf het begin. "
                "Het doel is rustige, persoonlijke spreekoefening met iemand die echt luistert en nuttige feedback geeft.\n\n"
                "Meer info: https://learnwithlucas.com/priveles-nederlands/"
            ),
            (
                "Hoeveel kosten privélessen?",
                "**Proefsessie** — 30 minuten — €28 (eenmalig)\n"
                "**Speaking Builder** — 4 x 60 minuten — €219 (10% korting)\n"
                "**Confidence Intensive** — 10 x 60 minuten — €469 (20% korting)\n\n"
                "**Examenvoorbereiding:**\n"
                "Examenvoorbereiding Builder — 4 x 60 minuten — €249\n"
                "Examenvoorbereiding Intensive — 10 x 60 minuten — €529\n\n"
                "Niet zeker welk pakket past? Begin met de proefsessie. "
                "Alle info: https://learnwithlucas.com/priveles-nederlands/"
            ),
            (
                "Welk niveau heb ik nodig voor privélessen?",
                "Geen minimumniveau. Privélessen werken goed als je:\n"
                "• Nederlands begrijpt maar aarzelt als het tijd is om te spreken\n"
                "• Rustige, persoonlijke feedback wilt zonder publiek\n"
                "• Een specifiek doel hebt zoals een sollicitatiegesprek, presentatie of dagelijks zelfvertrouwen\n"
                "• Je voorbereidt op NT2, inburgeringsexamen of een zakelijke assessment\n\n"
                "De eerste sessie begint altijd met een echt gesprek om samen je niveau te ontdekken."
            ),
            (
                "Hoe boek ik een privéles?",
                "Ga naar https://learnwithlucas.com/priveles-nederlands/ en kies een sessie of pakket.\n\n"
                "Na betaling ontvang je een kalenderlink. Kies een tijd die voor jou werkt. "
                "Dan ontmoeten jullie elkaar via Zoom of Discord. Geen installatie nodig.\n\n"
                "Vragen voor je boekt? Mail dutch@learnwithlucas.com"
            ),
            (
                "Wat gebeurt er in een sessie?",
                "Echt gesprek vanaf het begin. Je praat over onderwerpen die voor jou relevant zijn.\n\n"
                "Lucas geeft rustige feedback tijdens of na de sessie, wat het beste voor jou werkt. "
                "Een korte follow-up na de sessie als dat nuttig is.\n\n"
                "Sessies zijn 30 of 60 minuten afhankelijk van wat je hebt geboekt. "
                "Geen scripts, geen grammaticaoefeningen tenzij je daar om vraagt."
            ),
            (
                "Is er nu plek?",
                "Privélessen zijn beperkt zodat ze rustig en gefocust blijven.\n\n"
                "Als er nu geen plek is, ben je altijd welkom bij de gratis sessies "
                "en de spreekgemeenschap hier.\n\n"
                "Bekijk huidige beschikbaarheid op https://learnwithlucas.com/priveles-nederlands/"
            ),
        ],
    },
    "spreektips": {
        "label": "💬 Spreektips",
        "questions": [
            (
                "Ik begrijp Nederlands maar loop vast als ik spreek. Wat doe ik?",
                "Dat is het meest voorkomende patroon en het heeft een logische reden. "
                "Begrijpen en spreken gebruiken verschillende delen van je brein.\n\n"
                "De enige oplossing is meer spreken, maar het gaat erom dat je begint in situaties zonder druk. "
                "Geen test. Geen presentatie. Gewoon een echt gesprek waarbij fouten maken prima is.\n\n"
                "Begin hier: ga naar de spraakkanalen en zeg één zin. Dat is het. Dat is de oefening."
            ),
            (
                "Hoe stop ik met terugvallen op mijn eigen taal?",
                "Terugvallen gebeurt als de druk te hoog is of het woord er nog niet is.\n\n"
                "Twee dingen helpen:\n"
                "1. Verlaag de druk. Als je oefent met mensen die begrijpen dat je aan het leren bent, "
                "is er geen reden om te wisselen.\n"
                "2. Leer tijd te kopen. Zinnen zoals 'hoe zeg je dat', 'even nadenken' of 'ik denk dat het woord is' "
                "houden je in het Nederlands terwijl je het woord zoekt.\n\n"
                "Je hebt geen perfecte zinnen nodig. Je moet alleen elke keer iets langer in het Nederlands blijven."
            ),
            (
                "Hoe bouw ik zelfvertrouwen op bij het spreken?",
                "Zelfvertrouwen komt na het doen, niet ervoor.\n\n"
                "De meeste mensen wachten tot ze zich klaar voelen. Dat gevoel komt niet vanzelf. "
                "Het komt van genoeg keren spreken totdat het normaal begint te voelen.\n\n"
                "Het praktische antwoord: spreek elke dag een beetje in een omgeving zonder druk. "
                "Deze server, de spraakkanalen, de live sessies. "
                "Niet om te presteren. Gewoon om te wennen aan je eigen stem in het Nederlands."
            ),
            (
                "Hoe verbeter ik mijn uitspraak?",
                "Uitspraak verbetert door luisteren en spreken samen, niet door regels.\n\n"
                "Luister veel naar Nederlands op jouw niveau. Herhaal zinnen hardop, niet alleen woorden. "
                "Neem jezelf af en toe op en vergelijk.\n\n"
                "Het doel is geen perfect accent. Het doel is duidelijk begrepen worden. "
                "De meeste mensen zijn beter te verstaan dan ze denken."
            ),
            (
                "Hoe onthoud ik nieuwe woorden?",
                "Je onthoudt woorden het best als je ze gebruikt in echte zinnen, niet door lijsten te leren.\n\n"
                "Als je een nieuw woord leert, gebruik het dan in een zin die relevant is voor jouw leven. "
                "Zeg het hardop. Gebruik het dezelfde dag nog in een gesprek als je kunt.\n\n"
                "Kijk elke ochtend naar het woord van de dag. Daar is dat kanaal voor."
            ),
            (
                "Hoe vaak moet ik oefenen om vooruit te gaan?",
                "Een beetje elke dag werkt beter dan een lange sessie één keer per week.\n\n"
                "15 minuten echte spreekoefening per dag brengt je sneller verder dan "
                "twee uur op zaterdag. De regelmaat is wat de gewoonte opbouwt.\n\n"
                "Gebruik de spraakkanalen. Doe mee met de live sessies. Druk op de partnerknop als je vrij bent. "
                "Kleine stappen tellen op."
            ),
            (
                "Ik schaam me voor mijn fouten. Hoe kom ik daar overheen?",
                "Iedereen voelt dit. Het is geen teken dat je slecht bent in Nederlands. "
                "Het is een teken dat het je wat kan schelen.\n\n"
                "De mensen in deze community leren ook. Niemand beoordeelt je grammatica. "
                "Fouten zijn eigenlijk nuttig want ze laten zien wat je kunt verbeteren.\n\n"
                "De enige manier om je niet meer te schamen is genoeg spreken totdat het normaal wordt. "
                "Dat kost tijd. Gun jezelf die tijd."
            ),
        ],
    },
    "community_nl": {
        "label": "🏠 Community",
        "questions": [
            (
                "Wanneer zijn de gratis live sessies?",
                "Gratis live sessies zijn elke vrijdag om 20:30 CET. Open voor iedereen, geen lidmaatschap nodig.\n\n"
                "Leden van Ondersteund Spreken hebben ook toegang tot de maandag en woensdag sessies om 19:00.\n\n"
                "Gewoon binnenkomen. Je kunt luisteren, één zin zeggen of een heel gesprek voeren. "
                "Wat die dag goed voelt. Geen voorbereiding nodig."
            ),
            (
                "Hoe vind ik een spreekpartner?",
                "Ga naar het kanaal op-zoek-naar-een-partner en druk op de knop als je vrij bent.\n\n"
                "Als iemand anders ook vrij is binnen 30 minuten, krijgen jullie allebei een DM "
                "en kunnen jullie samen een spraakkanaal in. Geen planning, geen tijdslots. "
                "Druk gewoon op de knop als je zin hebt om te oefenen."
            ),
            (
                "Waarvoor zijn de spraakkanalen?",
                "De spraakkanalen zijn de hele dag open. Je hoeft niet te wachten op een geplande les.\n\n"
                "Kom binnen als je zin hebt. Blijf zo lang als je wilt. Ga weg wanneer je wilt. Geen druk."
            ),
            (
                "Hoe gebruik ik /onderwerpen?",
                "Typ `/onderwerpen` en er verschijnt een menu met 10 onderwerpscategorieën: "
                "familie, eten, hobby's, reizen, werk, leren, gezondheid, toekomst en meer.\n\n"
                "Kies een onderwerp en je krijgt gesprekskaarten met navigatiepijlen. "
                "Elke kaart toont een gespreksvraag en handige woordenschat. "
                "Iedereen in het kanaal kan de kaarten doorbladeren.\n\n"
                "Handig als het gesprek is stilgevallen en je een nieuwe richting wilt."
            ),
            (
                "Hoe zoek ik een woord op?",
                "Typ `/d word: [woord]` en je krijgt een definitie, woordtype, voorbeeldzin en synoniemen.\n\n"
                "De bot probeert eerst de Engelse API. Als het woord daar niet in staat, "
                "krijg je directe links naar woorden.org en Van Dale.\n\n"
                "Het resultaat wordt gepost in het kanaal zodat iedereen het kan zien."
            ),
            (
                "Wat is het woord van de dag?",
                "Elke ochtend om 09:00 CET verschijnt er een nieuw Nederlands woord in het woord-van-de-dag kanaal.\n\n"
                "B1/B2 niveau, praktisch woordgebruik. Elk bericht bevat de Nederlandse uitleg, "
                "een voorbeeldzin en een uitnodiging om het woord zelf te gebruiken in de chat."
            ),
            (
                "Waar vind ik gratis leermateriaal?",
                "Gratis oefengidsen: https://learnwithlucas.com/nederlandse-leermaterialen/\n"
                "Gratis maandelijks verhaal: https://learnwithlucas.com/gratis-maandelijks-boek/\n"
                "YouTube: https://www.youtube.com/@learndutchwithlucas\n"
                "TikTok: https://www.tiktok.com/@dutchwithlucas\n\n"
                "Alles op die pagina's is gratis. Voor de meeste onderdelen heb je geen account nodig."
            ),
        ],
    },
    "grammatica": {
        "label": "📝 Grammatica",
        "questions": [
            (
                "Wanneer gebruik ik 'de' en wanneer 'het'?",
                "Er is geen perfecte regel, maar deze patronen helpen:\n\n"
                "**Altijd 'het':** verkleinwoorden (het huisje, het meisje), landen, talen, metalen, "
                "namen van letters en namen van wetenschappen.\n\n"
                "**Altijd 'de':** beroepen (de leraar), mensen en dieren met een duidelijk geslacht, "
                "namen van bergen en rivieren, meervouden.\n\n"
                "Alles wat niet in een categorie past is onvoorspelbaar en moet je onthouden. "
                "Het goede nieuws: in de meeste gevallen begrijpen mensen je ook als je de verkeerde kiest."
            ),
            (
                "Wat is het verschil tussen 'er is' en 'er zijn'?",
                "Gebruik **er is** als er één iets is of als het woord enkelvoud is.\n"
                "Er is een probleem. Er is geen melk.\n\n"
                "Gebruik **er zijn** als er meerdere dingen zijn of als het woord meervoud is.\n"
                "Er zijn drie mensen. Er zijn geen stoelen meer.\n\n"
                "De truc: kijk naar het zelfstandig naamwoord dat erachter komt. Enkelvoud = er is. Meervoud = er zijn."
            ),
            (
                "Wanneer gebruik ik 'mij' en wanneer 'me'?",
                "In gesproken Nederlands zijn ze vrijwel uitwisselbaar, maar er is een verschil:\n\n"
                "**Me** gebruik je als de nadruk niet op het woord ligt.\n"
                "Hij zag me. Ze gaf het aan me.\n\n"
                "**Mij** gebruik je als het woord nadruk krijgt of na een voorzetsel.\n"
                "Hij zag míj, niet jou. Met mij. Voor mij.\n\n"
                "In spreektaal maakt het niet veel uit. 'Me' is informeler en wordt vaker gebruikt."
            ),
            (
                "Wat is het verschil tussen 'omdat' en 'want'?",
                "Beide betekenen 'because', maar de woordvolgorde is anders.\n\n"
                "**Omdat** — het werkwoord gaat naar het einde van de zin.\n"
                "Ik ben moe *omdat ik weinig heb geslapen*.\n\n"
                "**Want** — de normale volgorde blijft.\n"
                "Ik ben moe, *want ik heb weinig geslapen*.\n\n"
                "In gesproken taal worden beide veel gebruikt. 'Want' is iets informeler."
            ),
            (
                "Hoe gebruik ik de verleden tijd?",
                "Er zijn twee manieren om de verleden tijd te vormen:\n\n"
                "**Zwakke werkwoorden** — voeg -te of -de toe (en -ten/-den in meervoud).\n"
                "werken → ik werkte. leven → hij leefde.\n\n"
                "**Sterke werkwoorden** — de klinker verandert, geen vaste regel.\n"
                "rijden → ik reed. schrijven → ik schreef. lopen → ik liep.\n\n"
                "De meeste werkwoorden zijn zwak. De sterke moet je per stuk leren. "
                "Begin met de meest gebruikte: zijn, hebben, gaan, komen, zien, zeggen, weten."
            ),
            (
                "Wanneer gebruik ik 'zijn' en wanneer 'hebben' in de voltooide tijd?",
                "Dit is een van de lastigste punten van Nederlands.\n\n"
                "**Hebben** gebruik je voor de meeste werkwoorden.\n"
                "Ik heb gegeten. Ze heeft gewerkt. Hij heeft gebeld.\n\n"
                "**Zijn** gebruik je voor werkwoorden die een beweging of verandering uitdrukken "
                "waarbij je van A naar B gaat.\n"
                "Ik ben gegaan. Ze is gekomen. Hij is gevallen. We zijn gegroeid.\n\n"
                "Handig ezelsbruggetje: als je het werkwoord kunt combineren met een richting "
                "(naar huis gaan, omhoog vallen), gebruik dan 'zijn'."
            ),
            (
                "Wat is het verschil tussen 'nog' en 'al'?",
                "**Nog** betekent dat iets nog steeds het geval is, of dat je verwacht dat het snel zal veranderen.\n"
                "Ze woont nog in Amsterdam. Heb je nog honger?\n\n"
                "**Al** betekent dat iets eerder is gebeurd dan verwacht, of dat iets inmiddels het geval is.\n"
                "Hij is al klaar. Ze heeft al gegeten.\n\n"
                "In vragen kun je ze allebei gebruiken maar met een ander gevoel:\n"
                "'Ben je al klaar?' → ik verwacht ja.\n"
                "'Ben je nog niet klaar?' → ik verwacht nee."
            ),
            (
                "Hoe gebruik ik 'er' in een zin?",
                "'Er' heeft meerdere functies in het Nederlands en dat maakt het verwarrend.\n\n"
                "**1. Plaatsaanduiding** (there): Ik wil er niet naartoe. Ben je er al?\n\n"
                "**2. Met een getal**: Er zijn drie mensen. Er is één probleem.\n\n"
                "**3. Als verwijzing naar iets**: Ik heb er geen zin in. (= in dat)\n\n"
                "**4. Met voorzetsels**: Ik denk er vaak aan. Ze houdt er niet van.\n\n"
                "Het makkelijkst is om 'er' te leren in vaste combinaties. "
                "Begin met: er is/zijn, er naartoe, er van houden, er aan denken."
            ),
        ],
    },
    "server_functies": {
        "label": "🤖 Serverfuncties",
        "questions": [
            (
                "Wat doet deze bot?",
                "Jerry The Duck verzorgt de meeste geautomatiseerde functies in deze server.\n\n"
                "Dat omvat het woord van de dag, de spreekpartnervinder, aanmoedigingsberichten in de spraakkanalen, "
                "de woordenboekzoekfunctie, de onderwerpkaarten, deze FAQ en de productinfopagina's.\n\n"
                "Als er automatisch iets wordt gepost, is het waarschijnlijk Jerry."
            ),
            (
                "Hoe werkt de spreekpartnervinder?",
                "Ga naar het kanaal op-zoek-naar-een-partner en druk op de knop als je zin hebt om te oefenen.\n\n"
                "Je bent 30 minuten beschikbaar. Als iemand anders in datzelfde venster op de knop drukt, "
                "krijgen jullie allebei een DM met een link naar de spraakkanalen.\n\n"
                "Geen planning. Geen tijdslots. Druk gewoon als je vrij bent en kijk wie er is."
            ),
            (
                "Hoe gebruik ik /onderwerpen?",
                "Typ `/onderwerpen` en er verschijnt een dropdown met 10 categorieën.\n\n"
                "Kies er een en je krijgt gesprekskaarten met navigatiepijlen. "
                "Elke kaart toont een gespreksvraag en handige woordenschat. "
                "Iedereen in het kanaal kan de kaarten doorbladeren.\n\n"
                "Handig als het gesprek is stilgevallen en je een nieuwe richting wilt."
            ),
            (
                "Hoe gebruik ik /d om een woord op te zoeken?",
                "Typ `/d word: [woord]` en je krijgt een definitie, woordtype, voorbeeldzin en synoniemen.\n\n"
                "De bot probeert eerst de Engelse API. Als het woord daar niet in staat, "
                "krijg je directe links naar woorden.org en Van Dale.\n\n"
                "Het resultaat wordt gepost in het kanaal zodat iedereen het kan zien."
            ),
            (
                "Wat is het woord van de dag?",
                "Elke ochtend om 09:00 CET verschijnt er een nieuw Nederlands woord in het woord-van-de-dag kanaal.\n\n"
                "B1/B2 niveau, praktisch woordgebruik. Elk bericht bevat de Nederlandse uitleg, "
                "een voorbeeldzin en een uitnodiging om het woord zelf te gebruiken in de chat."
            ),
            (
                "Waarom krijg ik berichten in het spraakkanaal?",
                "Als je een spraakkanaal binnenkomt, stuurt Jerry op het 5- en 30-minutenpunt een kort berichtje.\n\n"
                "Bij 5 minuten is het gewoon een erkenning dat je er bent. "
                "Bij 30 minuten een berichtje dat het moeite waard is.\n\n"
                "Af en toe verschijnt er ook een gespreksopener in de chat. "
                "Als je niet weet waarover te praten, gebruik /onderwerpen of het woordenboekkanaal."
            ),
            (
                "Waar vind ik info over Ondersteund Spreken?",
                "Er is een apart kanaal met alle details en een FAQ-menu. "
                "Of ga direct naar https://learnwithlucas.com/ondersteund-spreken/"
            ),
            (
                "Waar vind ik info over privélessen?",
                "Er is een apart kanaal met alle details en een FAQ-menu. "
                "Of ga direct naar https://learnwithlucas.com/priveles-nederlands/"
            ),
        ],
    },
}



# =====================
# CATEGORY BUTTONS
# =====================

class AskJerryView(discord.ui.View):
    """Persistent hub view with one button per category."""

    def __init__(self, *, publisher: "AskJerryPublisher | None" = None) -> None:
        super().__init__(timeout=None)
        self._publisher = publisher

        for key, data in FAQ.items():
            self.add_item(CategoryButton(
                category_key=key,
                label=data["label"],
                publisher=publisher,
            ))


class CategoryButton(discord.ui.Button):
    def __init__(
        self,
        *,
        category_key: str,
        label: str,
        publisher: "AskJerryPublisher | None",
    ) -> None:
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=f"askjerry:cat:{category_key}:v1",
            row=_button_row(category_key),
        )
        self._category_key = category_key
        self._publisher = publisher

    async def callback(self, interaction: discord.Interaction) -> None:
        data = FAQ.get(self._category_key)
        if not data:
            await interaction.response.send_message("Category not found.", ephemeral=True)
            return

        view = QuestionPickerView(category_key=self._category_key, questions=data["questions"])
        await interaction.response.send_message(
            f"**{data['label']}** — pick a question:",
            view=view,
            ephemeral=True,
        )


def _button_row(key: str) -> int:
    rows = {
        "supported_speaking": 0,
        "private_lessons": 0,
        "speaking_tips": 1,
        "community": 1,
        "grammar": 2,
        "bot_features": 2,
    }
    return rows.get(key, 0)


# =====================
# QUESTION PICKER
# =====================

class QuestionSelect(discord.ui.Select):
    def __init__(self, *, questions: list[tuple[str, str]]) -> None:
        options = [
            discord.SelectOption(label=q[:100], value=str(i))
            for i, (q, _) in enumerate(questions)
        ]
        super().__init__(
            placeholder="Choose a question…",
            min_values=1,
            max_values=1,
            options=options,
        )
        self._questions = questions

    async def callback(self, interaction: discord.Interaction) -> None:
        idx = int(self.values[0])
        question, answer = self._questions[idx]
        embed = discord.Embed(
            title=question,
            description=answer,
        )
        embed.set_footer(text="Ask Jerry | Online English Café")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class QuestionPickerView(discord.ui.View):
    def __init__(self, *, category_key: str, questions: list[tuple[str, str]]) -> None:
        super().__init__(timeout=120)
        self.add_item(QuestionSelect(questions=questions))


class AskJerryViewNL(discord.ui.View):
    """Dutch persistent view in #vraag-het-jerry."""

    def __init__(self, *, publisher: "AskJerryPublisher | None" = None) -> None:
        super().__init__(timeout=None)
        self._publisher = publisher

        for key, data in NL_FAQ.items():
            self.add_item(CategoryButtonNL(
                category_key=key,
                label=data["label"],
                publisher=publisher,
            ))


class CategoryButtonNL(discord.ui.Button):
    def __init__(
        self,
        *,
        category_key: str,
        label: str,
        publisher: "AskJerryPublisher | None",
    ) -> None:
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=f"askjerry:nl:cat:{category_key}:v1",
            row=_nl_button_row(category_key),
        )
        self._category_key = category_key

    async def callback(self, interaction: discord.Interaction) -> None:
        data = NL_FAQ.get(self._category_key)
        if not data:
            await interaction.response.send_message("Categorie niet gevonden.", ephemeral=True)
            return
        view = QuestionPickerView(category_key=self._category_key, questions=data["questions"])
        await interaction.response.send_message(
            f"**{data['label']}** — kies een vraag:",
            view=view,
            ephemeral=True,
        )


def _nl_button_row(key: str) -> int:
    rows = {
        "ondersteund_spreken": 0,
        "priveles": 0,
        "spreektips": 1,
        "community_nl": 1,
        "grammatica": 2,
        "server_functies": 2,
    }
    return rows.get(key, 0)


def build_nl_hub_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🦆 Vraag het Jerry",
        description=(
            "Heb je een vraag? Kies een categorie hieronder.\n\n"
            "📖 **Ondersteund Spreken** — wat het is, prijs, wat je krijgt\n"
            "🎙️ **Privélessen** — hoe het werkt, prijs, boeken\n"
            "💬 **Spreektips** — hoe stop je met vastlopen, zelfvertrouwen opbouwen\n"
            "🏠 **Community** — live sessies, spraakkanalen, hoe dingen hier werken\n"
            "📝 **Grammatica** — veelgestelde vragen over Nederlandse grammatica\n"
            "🤖 **Serverfuncties** — hoe gebruik je de bot, commando's en kanalen\n\n"
            "Je antwoorden zijn alleen zichtbaar voor jou."
        ),
    )
    embed.set_footer(text="vraag-het-jerry:nl:v1")
    return embed



# =====================
# PUBLISHER
# =====================

def build_hub_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🦆 Ask Jerry",
        description=(
            "Got a question? Pick a category below.\n\n"
            "📖 **Supported Speaking** — what it is, pricing, what you get\n"
            "🎙️ **Private Lessons** — how it works, pricing, booking\n"
            "💬 **Speaking Tips** — how to stop freezing, build confidence, improve\n"
            "🏠 **Community** — live lessons, voice channels, how things work here\n"
            "📝 **Grammar** — common questions about English grammar\n"
            "🤖 **Server Features** — how to use the bot, commands and channels\n\n"
            "Your answers are only visible to you."
        ),
    )
    embed.set_footer(text="ask-jerry:en:v1")
    return embed


class AskJerryPublisher:
    def __init__(self, *, bot: discord.Client, repo) -> None:
        self._bot = bot
        self._repo = repo

    async def _publish_to_channel(
        self,
        *,
        channel_id: int,
        guild_id: int,
        embed: discord.Embed,
        view: discord.ui.View,
        kv_key: str,
        label: str,
    ) -> None:
        channel = self._bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self._bot.fetch_channel(channel_id)
            except Exception:
                log.warning("AskJerry: could not fetch channel %s", channel_id)
                return

        if not isinstance(channel, discord.TextChannel):
            return

        existing_id_raw = await self._repo.kv_get(guild_id, kv_key)
        if existing_id_raw:
            try:
                msg = await channel.fetch_message(int(existing_id_raw))
                await msg.edit(embed=embed, view=view)
                log.info("AskJerry: updated %s hub message %s", label, existing_id_raw)
                return
            except Exception:
                log.warning("AskJerry: could not edit %s hub message, recreating", label)

        try:
            sent = await channel.send(embed=embed, view=view)
            await self._repo.kv_set(guild_id, kv_key, str(sent.id))
            log.info("AskJerry: posted %s hub message %s", label, sent.id)
            try:
                await sent.pin()
            except discord.Forbidden:
                log.warning("AskJerry: missing pin permission channel=%s", channel_id)
            except Exception:
                log.warning("AskJerry: could not pin hub message channel=%s", channel_id)
        except Exception:
            log.exception("AskJerry: failed to post hub message channel=%s", channel_id)

    async def publish(self, guild_id: int) -> None:
        await self._publish_to_channel(
            channel_id=ASK_JERRY_CHANNEL_ID,
            guild_id=guild_id,
            embed=build_hub_embed(),
            view=AskJerryView(publisher=self),
            kv_key=KV_ASK_JERRY_MSG_ID,
            label="EN",
        )

    async def publish_dutch(self, guild_id: int) -> None:
        await self._publish_to_channel(
            channel_id=NL_ASK_JERRY_CHANNEL_ID,
            guild_id=guild_id,
            embed=build_nl_hub_embed(),
            view=AskJerryViewNL(publisher=self),
            kv_key=KV_NL_ASK_JERRY_MSG_ID,
            label="NL",
        )


# =====================
# COG
# =====================

class AskJerryCog(commands.Cog):
    def __init__(self, bot: commands.Bot, publisher: AskJerryPublisher) -> None:
        self.bot = bot
        self._publisher = publisher


async def setup(bot: commands.Bot, repo, *, guild_id: int) -> AskJerryPublisher:
    publisher = AskJerryPublisher(bot=bot, repo=repo)
    cog = AskJerryCog(bot, publisher)
    await bot.add_cog(cog)

    # Register persistent views for both languages
    bot.add_view(AskJerryView(publisher=None))
    bot.add_view(AskJerryViewNL(publisher=None))

    log.info("AskJerryCog loaded.")
    return publisher