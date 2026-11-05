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

EN_COMMUNITY_INVITE = "https://discord.gg/XHtNPNu8pU"
EN_SUPPORTED_SPEAKING_URL = "https://learnwithlucas.com/en/supported-speaking/"
EN_PRIVATE_LESSONS_URL = "https://learnwithlucas.com/en/private-lessons/"
EN_COMMUNITY_URL = "https://learnwithlucas.com/en/community/"
EN_LEVEL_CHECK_URL = "https://learnwithlucas.com/en/courses/english-level-check/"
EN_COURSES_URL = "https://learnwithlucas.com/en/courses/"
NL_COMMUNITY_URL = "https://learnwithlucas.com/nl/spreekgroep/"
NL_COURSES_URL = "https://learnwithlucas.com/nl/courses/"
NL_FREE_EXAMS_URL = "https://learnwithlucas.com/nl/courses/"
NL_SUPPORTED_SPEAKING_URL = "https://learnwithlucas.com/nl/ondersteund-spreken/"
NL_PRIVATE_LESSONS_URL = "https://learnwithlucas.com/nl/priveles-nederlands/"
TIKTOK_URL = "https://www.tiktok.com/@learnwithlucas"
YOUTUBE_EN_URL = "https://www.youtube.com/@learnenglishlucas"


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
                "Supported Speaking is a practice membership for €7.99 a month.\n\n"
                "Every Monday, Friday and Saturday you get the longer member version of the practice guide. "
                "Every month you get 5 B1 stories with audio. "
                "There is a live group session every Saturday at 14:30 CEST, "
                "and you can use the community on Discord, WhatsApp and Telegram.\n\n"
                "You practise at your own pace. Join the live session when it fits you.\n\n"
                f"More info: {EN_SUPPORTED_SPEAKING_URL}"
            ),
            (
                "How much does it cost?",
                "Supported Speaking costs **€7.99 a month**, **€39.95 for 6 months** (1 month free) or **€79.90 a year** (2 months free).\n\n"
                "A private lesson with Lucas costs €24 for 30 minutes. "
                "Supported Speaking is practice every week for €7.99 a month.\n\n"
                "Not what you expected? You get your money back within 14 days. Cancel anytime.\n\n"
                f"[Start today]({EN_SUPPORTED_SPEAKING_URL})"
            ),
            (
                "What do I get every week?",
                "Every week you get:\n"
                "• Monday, Friday and Saturday: the supporter edition practice guide\n"
                "• A paragraph with hidden mistakes to find and fix\n"
                "• Extra practice sentences (3x more than the free version)\n"
                "• Questions to test yourself\n\n"
                "Every month you also get 5 B1 stories with audio. "
                "You read and listen at the same time."
            ),
            (
                "Is there a live session?",
                "The Supported Speaking live group meets every Saturday at 14:30 CEST on Discord, "
                "with at most 20 learners.\n\n"
                "The free community is separate and stays open on Discord, WhatsApp and Telegram."
            ),
            (
                "Can I cancel anytime?",
                "Yes. You can cancel anytime, and you don't need to give a reason.\n\n"
                "If it's not what you expected, you get your money back within 14 days.\n\n"
                f"[Join here]({EN_SUPPORTED_SPEAKING_URL})"
            ),
            (
                "What level do I need?",
                "Supported Speaking fits best at B1 or B2. "
                "That means you understand most English but freeze or hesitate when you have to speak.\n\n"
                "If you are a complete beginner, start with the free community first and join when you feel ready."
            ),
            (
                "How is it different from the free guides?",
                "The free guides have the main phrases and 5 practice sentences.\n\n"
                "The member version adds:\n"
                "• 10 extra practice sentences\n"
                "• A paragraph with hidden mistakes to find and fix\n"
                "• Questions to test yourself\n"
                "• A quick recognition test\n\n"
                "That is about 3 times more per guide."
            ),
        ],
    },
    "private_lessons": {
        "label": "🎙️ Private Lessons",
        "emoji": "🎙️",
        "questions": [
            (
                "What are private lessons?",
                "Private lessons are one on one with Lucas, on Zoom or Discord.\n\n"
                "We start talking from the first minute, and you can stop and think whenever you need to. "
                "I listen, and I tell you what to fix and what already works.\n\n"
                f"More info: {EN_PRIVATE_LESSONS_URL}"
            ),
            (
                "How much do private lessons cost?",
                "**Trial session**, 30 minutes: €24 (one time)\n"
                "**Speaking Builder**, 4 x 60 minutes: €189\n"
                "**Confidence Intensive**, 10 x 60 minutes: €389\n\n"
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
                "The first session starts with a normal conversation. That's how we find your level."
            ),
            (
                "How do I book a private lesson?",
                f"Go to {EN_PRIVATE_LESSONS_URL} and pick a session or package.\n\n"
                "After you pay, you get a calendar link. Pick a time that works for you. "
                "Then we meet on Zoom or Discord.\n\n"
                "Questions before booking? Email english@learnwithlucas.com"
            ),
            (
                "What happens in a session?",
                "We talk from the first minute, about the topics you need English for.\n\n"
                "Lucas gives feedback during or after the session, you choose. "
                "You get short notes after the session if you want them.\n\n"
                "A session is 30 or 60 minutes, depending on what you booked. "
                "Grammar drills only if you ask for them."
            ),
            (
                "Is there space right now?",
                "I keep the number of private students small.\n\n"
                "No space right now? You can still join the free community and practise here.\n\n"
                f"The private lessons page shows when there is space: {EN_PRIVATE_LESSONS_URL}"
            ),
        ],
    },
    "speaking_tips": {
        "label": "💬 Speaking Tips",
        "emoji": "💬",
        "questions": [
            (
                "I understand English but freeze when I speak. What do I do?",
                "This happens to a lot of learners. Understanding and speaking are different skills, "
                "and you have trained the first one much more.\n\n"
                "The fix is speaking more, starting somewhere calm: a normal conversation "
                "with people who don't mind mistakes.\n\n"
                "Start here: join a voice channel and say one sentence. That's the whole exercise."
            ),
            (
                "How do I stop switching back to my first language?",
                "Switching happens when the pressure is too high or the word is not there yet.\n\n"
                "Two things help:\n"
                "1. Practise with people who know you are learning. Then there is less reason to switch.\n"
                "2. Learn phrases that give you time: 'how do I say this', 'give me a second', 'I think the word is'. "
                "They keep you in English while you look for the word.\n\n"
                "You do not need perfect sentences. You need to stay in English longer each time."
            ),
            (
                "How do I build confidence in speaking?",
                "Confidence comes after you speak. Waiting to feel ready usually doesn't work.\n\n"
                "Speak a little every day somewhere calm: the voice channels, the daily chat or the free community. "
                "After enough times, hearing your own voice in English starts to feel normal."
            ),
            (
                "How do I improve my pronunciation?",
                "Pronunciation gets better when you listen and speak a lot. Rules help less.\n\n"
                "Listen to a lot of English at your level. Repeat sentences out loud, not just words. "
                "Record yourself occasionally and compare.\n\n"
                "You don't need a native accent. You need people to understand you, "
                "and most learners are easier to understand than they think."
            ),
            (
                "How do I remember new vocabulary?",
                "You remember a word when you use it in a real sentence. Lists help less.\n\n"
                "When you learn a new word, make a sentence about your own life with it. "
                "Say it out loud. Use it in a conversation the same day if you can.\n\n"
                "The word of the day channel gives you one new word every morning."
            ),
            (
                "How often should I practice to improve?",
                "A little every day works better than one long session a week.\n\n"
                "15 minutes of speaking a day helps more than two hours on a Saturday, "
                "because it turns into a habit.\n\n"
                "Use the voice channels, the daily chat and the partner button when you are free."
            ),
            (
                "I feel embarrassed making mistakes. How do I get past that?",
                "Almost every learner feels this. It doesn't mean your English is bad.\n\n"
                "The people in this community are learning too. Nobody here is checking your grammar. "
                "And a mistake shows you what to work on next.\n\n"
                "The feeling goes away when speaking becomes normal for you. That takes time, and that's okay."
            ),
            (
                "What is the difference between fluency and being a good speaker?",
                "Fluency means speaking without long pauses or needing to translate in your head. "
                "Being a good speaker means communicating clearly and connecting with the person you are talking to.\n\n"
                "You can be a good speaker without being fluent. Being clear helps people more than being fast.\n\n"
                "In this community the goal is to speak, even when you feel nervous. Fluency comes later."
            ),
        ],
    },
    "community": {
        "label": "🏠 Community",
        "emoji": "🏠",
        "questions": [
            (
                "Where is the free community?",
                f"Start here: {EN_COMMUNITY_URL}\n\n"
                "You can practise on Discord, WhatsApp or Telegram. Read along first, "
                "say one sentence, or have a full conversation when you are ready."
            ),
            (
                "How do I find a speaking partner?",
                "Go to the looking-for-a-partner channel and press the button when you are free.\n\n"
                "If someone else is also free within 30 minutes, you both get a DM and can join a voice channel together. "
                "You don't need to plan anything. Press the button when you feel like practising."
            ),
            (
                "What are the voice channels for?",
                "The voice channels are open all day. You do not need to wait for a scheduled lesson.\n\n"
                "Drop In and Talk and Open Conversation are open anytime. "
                "Join when you feel like it and leave whenever you want."
            ),
            (
                "How do I use the /topics command?",
                "Type `/topics` anywhere in the server and a menu appears with 10 topic categories: "
                "family, food, hobbies, travel, work, learning, health, technology, emotions and future.\n\n"
                "Pick a topic and you get 10 conversation questions, one at a time, with useful words for each one. "
                "Use it when you don't know what to talk about."
            ),
            (
                "How do I look up a word?",
                "Type `/d word: [word]` anywhere in the server.\n\n"
                "You get the meaning, the word type, an example sentence and similar words. "
                "The result shows up in the channel, so everyone can see it.\n\n"
                "All lookups also appear in the vocabulary channel."
            ),
            (
                "What is the word of the day?",
                "Every morning at 09:00 CET a new B1/B2 level word goes up in the word of the day channel.\n\n"
                "Each post has the meaning, an example sentence and a small task: use the word in the chat. "
                "Using a word once makes it easier to remember."
            ),
            (
                "Where can I find free learning materials?",
                f"Free English level check: {EN_LEVEL_CHECK_URL}\n"
                f"Free community: {EN_COMMUNITY_URL}\n"
                f"All English courses: {EN_COURSES_URL}\n"
                f"TikTok lessons: {TIKTOK_URL}\n"
                f"YouTube: {YOUTUBE_EN_URL}\n\n"
                "Everything on those pages is free. For most of it you don't need an account."
            ),
            (
                "How is this community different from other English communities?",
                "This community is about speaking.\n\n"
                "The voice channels, the partner finder, the live lessons and the practice guides "
                "are all there for one reason: you get better at speaking by speaking more, "
                "somewhere calm where mistakes are normal."
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
                "Learners mix these up a lot. There is no perfect rule, "
                "but this pattern helps:\n\n"
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
                "To remember it: at is for the most exact time, in is for the longest period."
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
                "When you speak, 'could' and 'would' make almost any request sound more polite."
            ),
        ],
    },
    "bot_features": {
        "label": "🤖 Server Features",
        "emoji": "🤖",
        "questions": [
            (
                "What does this bot do?",
                "Jerry The Duck runs most of the automatic things in this server.\n\n"
                "Jerry posts the word of the day, runs the speaking partner finder and the `/d` word lookup, "
                "shows the topic cards and this FAQ, and posts the reminders and the product info channels.\n\n"
                "If something posts by itself, it is probably Jerry."
            ),
            (
                "How does the speaking partner finder work?",
                "Go to the looking-for-a-partner channel and press the button when you feel like practising.\n\n"
                "You show as free for 30 minutes. If someone else presses the button in that time, "
                "you both get a DM with a link to the voice channels.\n\n"
                "You don't need to plan anything. Press it when you are free and see who is around."
            ),
            (
                "How do I use /topics?",
                "Type `/topics` anywhere and a dropdown appears with 10 categories.\n\n"
                "Pick one and you get question cards with navigation arrows. "
                "Each card shows a conversation question and useful vocabulary for that question. "
                "Everyone in the channel can browse the cards.\n\n"
                "Use it when the conversation slows down and you want something new to talk about."
            ),
            (
                "How do I use /d to look up a word?",
                "Type `/d word: [word]` and you get the definition, part of speech, example sentence and synonyms.\n\n"
                "The result shows up in the channel, so others can learn the word too. "
                "You can also use it in the vocabulary channel."
            ),
            (
                "What is the word of the day?",
                "Every morning at 09:00 CET a new word appears in the word of the day channel.\n\n"
                "The words are B1/B2 level and useful in daily life. Each post has the meaning, an example sentence "
                "and a small task: use the word in a sentence in the chat."
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
                f"There is a channel with all the details and a menu with questions. "
                f"You can also go to {EN_SUPPORTED_SPEAKING_URL}"
            ),
            (
                "Where can I find info about private lessons?",
                f"There is a channel with all the details and a menu with questions. "
                f"You can also go to {EN_PRIVATE_LESSONS_URL}"
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
                "Ondersteund Spreken is een oefenlidmaatschap voor €11,99 per maand.\n\n"
                "Elke maandag of woensdag is er een live sessie in een kleine groep op jouw niveau (A2, B1 of B2). "
                "Op vrijdag krijg je de ledenversie van de oefengids. Op zondag krijg je het spreekonderwerp voor de sessie. "
                "Elke maand krijg je ook een verhaal met audio.\n\n"
                "Je spreekt elke week live, in een rustige groep en in je eigen tempo.\n\n"
                f"Meer info: {NL_SUPPORTED_SPEAKING_URL}"
            ),
            (
                "Hoeveel kost het?",
                "Ondersteund Spreken kost **€11,99 per maand** voor Standaard, **€19,99 per maand** voor Premium, "
                "of vanaf **€119,90 per jaar**.\n\n"
                "Een privéles met Lucas kost €28 voor 30 minuten. "
                "Ondersteund Spreken is elke week live oefenen voor €11,99 per maand.\n\n"
                "Is het niet wat je verwachtte? Dan krijg je binnen 14 dagen je geld terug. Op elk moment opzegbaar.\n\n"
                f"Begin vandaag: {NL_SUPPORTED_SPEAKING_URL}"
            ),
            (
                "Wat krijg ik elke week?",
                "Elke week:\n"
                "• Maandag 20:00 of woensdag 19:00: live sessie via WhatsApp, op jouw niveau\n"
                "• Vrijdag: de ledenversie van de oefengids, met fouten om te vinden en extra oefenzinnen\n"
                "• Zondag: het spreekonderwerp voor de sessie van maandag of woensdag\n\n"
                "Elke maand krijg je ook een B1-verhaal met audio. "
                "Je leest en luistert tegelijk."
            ),
            (
                "Hoe werkt de live sessie?",
                "Elke maandag om 20:00 en woensdag om 19:00, live via WhatsApp.\n\n"
                "• 0:00 tot 0:15: introductie, iedereen samen\n"
                "• 0:15 tot 0:45: breakout rooms per niveau (A2, B1 of B2), Lucas komt in elke kamer\n"
                "• 0:45 tot 1:00: afsluiting, we bespreken de fouten die vaak terugkwamen\n\n"
                "Max 20 personen per sessie. Je kiest zelf welke avond past, maandag of woensdag. "
                "Je hoeft niet allebei te komen."
            ),
            (
                "Kan ik op elk moment opzeggen?",
                "Ja. Je kunt op elk moment opzeggen. Je hoeft niet te zeggen waarom.\n\n"
                "Is het niet wat je verwachtte? Dan krijg je binnen 14 dagen je geld terug.\n\n"
                f"Begin hier: {NL_SUPPORTED_SPEAKING_URL}"
            ),
            (
                "Welk niveau heb ik nodig?",
                "Ondersteund Spreken werkt het beste als je A2, B1 of B2 niveau hebt. "
                "Dat betekent dat je Nederlands redelijk begrijpt maar vastloopt als je moet spreken.\n\n"
                "Er zijn breakout rooms per niveau, dus je oefent altijd met mensen op jouw niveau. "
                "Je kiest zelf welke kamer je ingaat.\n\n"
                "Als je nog een complete beginner bent, begin dan met de gratis spreekgroep en sluit je aan als je er klaar voor bent."
            ),
            (
                "Wat is het verschil met de gratis versie?",
                "De gratis gids heeft de uitleg en 5 oefenzinnen.\n\n"
                "In de ledenversie krijg je ook:\n"
                "• 10 extra oefenzinnen\n"
                "• Een alinea met verborgen fouten om te vinden en te verbeteren\n"
                "• Vragen om jezelf te testen\n"
                "• Een korte herkenningstest\n\n"
                "Dat is ongeveer 3 keer zoveel per gids. Daarbij krijg je de live sessie en elke maand een verhaal."
            ),
        ],
    },
    "priveles": {
        "label": "🎙️ Privélessen",
        "questions": [
            (
                "Wat zijn privélessen?",
                "Privélessen zijn een op een met Lucas, op Zoom of Discord.\n\n"
                "We praten vanaf de eerste minuut, en je mag altijd even stoppen en nadenken. "
                "Ik luister, en ik vertel je wat je kunt verbeteren en wat al goed gaat.\n\n"
                f"Meer info: {NL_PRIVATE_LESSONS_URL}"
            ),
            (
                "Hoeveel kosten privélessen?",
                "**Proefsessie**, 30 minuten: €28 (eenmalig)\n"
                "**Speaking Builder**, 4 x 60 minuten: €219 (+ 3 maanden Ondersteund Spreken)\n"
                "**Confidence Intensive**, 10 x 60 minuten: €469 (+ 6 maanden Ondersteund Spreken)\n\n"
                "Examentraining voor Inburgering, KNM, ONA, NT2 en CNaVT zit in de gewone pakketten.\n\n"
                "Niet zeker welk pakket past? Begin met de proefsessie. "
                f"Alle info: {NL_PRIVATE_LESSONS_URL}"
            ),
            (
                "Welk niveau heb ik nodig voor privélessen?",
                "Geen minimumniveau. Privélessen werken goed als je:\n"
                "• Nederlands begrijpt maar aarzelt als het tijd is om te spreken\n"
                "• Rustige, persoonlijke feedback wilt zonder publiek\n"
                "• Een specifiek doel hebt zoals een sollicitatiegesprek, presentatie of dagelijks zelfvertrouwen\n"
                "• Je voorbereidt op NT2, het inburgeringsexamen of een toets op je werk\n\n"
                "De eerste sessie begint met een gewoon gesprek. Zo ontdekken we samen je niveau."
            ),
            (
                "Hoe boek ik een privéles?",
                f"Ga naar {NL_PRIVATE_LESSONS_URL} en kies een sessie of pakket.\n\n"
                "Na het betalen krijg je een kalenderlink. Kies een tijd die voor jou werkt. "
                "Daarna spreken we af op Zoom of Discord.\n\n"
                "Vragen voor je boekt? Mail english@learnwithlucas.com"
            ),
            (
                "Wat gebeurt er in een sessie?",
                "We praten vanaf de eerste minuut, over de onderwerpen waarvoor jij Nederlands nodig hebt.\n\n"
                "Lucas geeft feedback tijdens of na de sessie, jij kiest. "
                "Na de sessie krijg je korte notities als je die wilt.\n\n"
                "Een sessie duurt 30 of 60 minuten, net wat je hebt geboekt. "
                "Grammaticaoefeningen doen we alleen als je erom vraagt."
            ),
            (
                "Is er nu plek?",
                "Ik houd het aantal privéleerlingen klein.\n\n"
                "Is er nu geen plek? Dan kun je nog steeds meedoen met de gratis spreekgroep en hier oefenen.\n\n"
                f"Op de privélespagina zie je wanneer er plek is: {NL_PRIVATE_LESSONS_URL}"
            ),
        ],
    },
    "spreektips": {
        "label": "💬 Spreektips",
        "questions": [
            (
                "Ik begrijp Nederlands maar loop vast als ik spreek. Wat doe ik?",
                "Dat gebeurt bij veel leerlingen. Begrijpen en spreken zijn verschillende dingen, "
                "en het eerste heb je veel meer geoefend.\n\n"
                "De oplossing is meer spreken, eerst op een rustige plek: een gewoon gesprek "
                "met mensen die fouten niet erg vinden.\n\n"
                "Begin hier: ga naar een spraakkanaal en zeg één zin. Meer hoeft niet."
            ),
            (
                "Hoe stop ik met terugvallen op mijn eigen taal?",
                "Terugvallen gebeurt als de druk te hoog is of het woord er nog niet is.\n\n"
                "Twee dingen helpen:\n"
                "1. Oefen met mensen die weten dat je aan het leren bent. Dan hoef je minder snel te wisselen.\n"
                "2. Leer zinnen die je tijd geven: 'hoe zeg je dat', 'even denken', 'ik denk dat het woord ... is'. "
                "Zo blijf je in het Nederlands terwijl je het woord zoekt.\n\n"
                "Je hebt geen perfecte zinnen nodig. Je moet alleen elke keer iets langer in het Nederlands blijven."
            ),
            (
                "Hoe bouw ik zelfvertrouwen op bij het spreken?",
                "Zelfvertrouwen komt nadat je spreekt. Wachten tot je je klaar voelt, werkt meestal niet.\n\n"
                "Spreek elke dag een beetje op een rustige plek: de spraakkanalen of de live sessies. "
                "Na genoeg keren voelt je eigen stem in het Nederlands normaal."
            ),
            (
                "Hoe verbeter ik mijn uitspraak?",
                "Je uitspraak wordt beter als je veel luistert en spreekt. Regels helpen minder.\n\n"
                "Luister veel naar Nederlands op jouw niveau. Herhaal zinnen hardop, niet alleen woorden. "
                "Neem jezelf af en toe op en vergelijk.\n\n"
                "Je hebt geen perfect accent nodig. Mensen moeten je kunnen verstaan, "
                "en de meeste leerlingen zijn beter te verstaan dan ze denken."
            ),
            (
                "Hoe onthoud ik nieuwe woorden?",
                "Je onthoudt een woord als je het in een echte zin gebruikt. Lijsten helpen minder.\n\n"
                "Leer je een nieuw woord? Maak er een zin mee over je eigen leven. "
                "Zeg het hardop. Gebruik het dezelfde dag nog in een gesprek als dat lukt.\n\n"
                "In het kanaal woord van de dag staat elke ochtend een nieuw woord."
            ),
            (
                "Hoe vaak moet ik oefenen om vooruit te gaan?",
                "Elke dag een beetje werkt beter dan één lange sessie per week.\n\n"
                "15 minuten spreken per dag helpt meer dan twee uur op zaterdag, "
                "omdat het een gewoonte wordt.\n\n"
                "Gebruik de spraakkanalen, doe mee met de live sessies en druk op de partnerknop als je vrij bent."
            ),
            (
                "Ik schaam me voor mijn fouten. Hoe kom ik daar overheen?",
                "Bijna elke leerling voelt dit. Het betekent niet dat je Nederlands slecht is.\n\n"
                "De mensen in deze community leren ook. Niemand let hier op je grammatica. "
                "En een fout laat je zien waar je nog aan kunt werken.\n\n"
                "Het gevoel gaat weg als spreken normaal wordt voor je. Dat kost tijd, en dat is oké."
            ),
        ],
    },
    "community_nl": {
        "label": "🏠 Community",
        "questions": [
            (
                "Waar is de gratis spreekgroep?",
                f"De gratis spreekgroep staat hier: {NL_COMMUNITY_URL}\n\n"
                "Je kunt oefenen via WhatsApp, Discord of Telegram. Lees eerst mee, "
                "zeg één zin, of praat mee zodra je er klaar voor bent."
            ),
            (
                "Hoe vind ik een spreekpartner?",
                "Ga naar het kanaal op-zoek-naar-een-partner en druk op de knop als je vrij bent.\n\n"
                "Is iemand anders binnen 30 minuten ook vrij? Dan krijgen jullie allebei een DM "
                "en kunnen jullie samen een spraakkanaal in. Je hoeft niets te plannen. "
                "Druk op de knop als je zin hebt om te oefenen."
            ),
            (
                "Waarvoor zijn de spraakkanalen?",
                "De spraakkanalen zijn de hele dag open. Je hoeft niet te wachten op een geplande les.\n\n"
                "Kom binnen als je zin hebt en ga weg wanneer je wilt."
            ),
            (
                "Hoe gebruik ik /onderwerpen?",
                "Typ `/onderwerpen` en er verschijnt een menu met 10 onderwerpscategorieën: "
                "familie, eten, hobby's, reizen, werk, leren, gezondheid, toekomst en meer.\n\n"
                "Kies een onderwerp en je krijgt gesprekskaarten met pijltjes. "
                "Op elke kaart staat een vraag met handige woorden. "
                "Iedereen in het kanaal kan door de kaarten bladeren.\n\n"
                "Gebruik het als het gesprek stilvalt en je iets nieuws wilt bespreken."
            ),
            (
                "Hoe zoek ik een woord op?",
                "Typ `/d word: [woord]`. Je krijgt dan links naar het woord op woorden.org en Van Dale.\n\n"
                "Het resultaat komt in het kanaal, dus iedereen kan het zien."
            ),
            (
                "Wat is het woord van de dag?",
                "Elke ochtend om 09:00 CET verschijnt er een nieuw Nederlands woord in het woord-van-de-dag kanaal.\n\n"
                "De woorden zijn B1/B2 en handig in het dagelijks leven. In elk bericht staan de uitleg, "
                "een voorbeeldzin en een kleine opdracht: gebruik het woord zelf in de chat."
            ),
            (
                "Waar vind ik gratis leermateriaal?",
                f"Gratis spreekgroep: {NL_COMMUNITY_URL}\n"
                f"Gratis oefenexamens en cursussen: {NL_COURSES_URL}\n"
                "YouTube: https://www.youtube.com/@learndutchlucas\n"
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
                "Kies je de verkeerde? Meestal begrijpen mensen je dan nog steeds."
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
                "**Omdat:** het werkwoord gaat naar het einde van de zin.\n"
                "Ik ben moe *omdat ik weinig heb geslapen*.\n\n"
                "**Want:** de normale volgorde blijft.\n"
                "Ik ben moe, *want ik heb weinig geslapen*.\n\n"
                "In gesproken taal worden beide veel gebruikt. 'Want' is iets informeler."
            ),
            (
                "Hoe gebruik ik de verleden tijd?",
                "Er zijn twee manieren om de verleden tijd te vormen:\n\n"
                "**Zwakke werkwoorden:** voeg -te of -de toe (en -ten/-den in meervoud).\n"
                "werken → ik werkte. leven → hij leefde.\n\n"
                "**Sterke werkwoorden:** de klinker verandert. Daar is geen vaste regel voor.\n"
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
                "'Er' heeft in het Nederlands vier functies. Daarom is het verwarrend.\n\n"
                "**1. Plaatsaanduiding** (there): Ik wil er niet naartoe. Ben je er al?\n\n"
                "**2. Met een getal**: Er zijn drie mensen. Er is één probleem.\n\n"
                "**3. Als verwijzing naar iets**: Ik heb er geen zin in. (= in dat)\n\n"
                "**4. Met voorzetsels**: Ik denk er vaak aan. Ze houdt er niet van.\n\n"
                "Het makkelijkst is om 'er' te leren in vaste combinaties. "
                "Begin met: er is/zijn, ernaartoe, ervan houden, eraan denken."
            ),
        ],
    },
    "server_functies": {
        "label": "🤖 Serverfuncties",
        "questions": [
            (
                "Wat doet deze bot?",
                "Jerry The Duck doet de meeste automatische dingen in deze server.\n\n"
                "Jerry plaatst het woord van de dag, regelt de spreekpartnerknop en `/d`, "
                "laat de onderwerpkaarten en deze FAQ zien en plaatst de info over lessen.\n\n"
                "Wordt er vanzelf iets gepost? Dan is het waarschijnlijk Jerry."
            ),
            (
                "Hoe werkt de spreekpartnervinder?",
                "Ga naar het kanaal op-zoek-naar-een-partner en druk op de knop als je zin hebt om te oefenen.\n\n"
                "Je staat dan 30 minuten als vrij. Drukt iemand anders in die tijd ook op de knop? "
                "Dan krijgen jullie allebei een DM met een link naar de spraakkanalen.\n\n"
                "Je hoeft niets te plannen. Druk als je vrij bent en kijk wie er is."
            ),
            (
                "Hoe gebruik ik /onderwerpen?",
                "Typ `/onderwerpen` en er verschijnt een dropdown met 10 categorieën.\n\n"
                "Kies er een en je krijgt gesprekskaarten met pijltjes. "
                "Op elke kaart staat een vraag met handige woorden. "
                "Iedereen in het kanaal kan door de kaarten bladeren.\n\n"
                "Gebruik het als het gesprek stilvalt en je iets nieuws wilt bespreken."
            ),
            (
                "Hoe gebruik ik /d om een woord op te zoeken?",
                "Typ `/d word: [woord]`. Je krijgt dan links naar het woord op woorden.org en Van Dale.\n\n"
                "Het resultaat komt in het kanaal, dus iedereen kan het zien."
            ),
            (
                "Wat is het woord van de dag?",
                "Elke ochtend om 09:00 CET verschijnt er een nieuw Nederlands woord in het woord-van-de-dag kanaal.\n\n"
                "De woorden zijn B1/B2 en handig in het dagelijks leven. In elk bericht staan de uitleg, "
                "een voorbeeldzin en een kleine opdracht: gebruik het woord zelf in de chat."
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
                "Er is een kanaal met alle details en een menu met vragen. "
                f"Je kunt ook naar {NL_SUPPORTED_SPEAKING_URL} gaan."
            ),
            (
                "Waar vind ik info over privélessen?",
                "Er is een kanaal met alle details en een menu met vragen. "
                f"Je kunt ook naar {NL_PRIVATE_LESSONS_URL} gaan."
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
            f"**{data['label']}**: pick a question.",
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
            f"**{data['label']}**: kies een vraag.",
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
            "📖 **Ondersteund Spreken:** wat het is, de prijs, wat je krijgt\n"
            "🎙️ **Privélessen:** hoe het werkt, de prijs, boeken\n"
            "💬 **Spreektips:** minder vastlopen, meer zelfvertrouwen\n"
            "🏠 **Community:** live sessies, spraakkanalen, hoe het hier werkt\n"
            "📝 **Grammatica:** vragen over Nederlandse grammatica\n"
            "🤖 **Serverfuncties:** de bot, commando's en kanalen\n\n"
            "Alleen jij ziet de antwoorden."
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
            "📖 **Supported Speaking:** what it is, the price, what you get\n"
            "🎙️ **Private lessons:** how it works, the price, booking\n"
            "💬 **Speaking tips:** freezing less, feeling more confident\n"
            "🏠 **Community:** live lessons, voice channels, how things work here\n"
            "📝 **Grammar:** questions about English grammar\n"
            "🤖 **Server features:** the bot, commands and channels\n\n"
            "Only you can see the answers."
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
