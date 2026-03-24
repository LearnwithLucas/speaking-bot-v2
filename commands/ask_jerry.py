from __future__ import annotations

# commands/ask_jerry.py
import logging

import discord
from discord.ext import commands

log = logging.getLogger("commands.ask_jerry")

ASK_JERRY_CHANNEL_ID = 1226103187614728295  # 🦆┃ask-jerry
KV_ASK_JERRY_MSG_ID = "ask_jerry_hub_message_id"

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
                "Supported Speaking is a weekly practice membership for €4.99/month.\n\n"
                "Every Monday, Friday and Saturday you get the extended supporter edition practice guide. "
                "You also get 5 B1-level English stories with audio every month, error recognition training in every guide, "
                "and full community access on Discord, WhatsApp and Telegram.\n\n"
                "It is not a course. There is no fixed schedule you have to follow. "
                "You practice at your own pace with better materials than the free version.\n\n"
                f"More info: {EN_SUPPORTED_SPEAKING_URL}"
            ),
            (
                "How much does it cost?",
                "Supported Speaking costs **€4.99 per month** or **€49.90 per year** (2 months free).\n\n"
                "For comparison: a private lesson with Lucas costs €22 for 30 minutes. "
                "This is weekly practice material for less than one coffee a week.\n\n"
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

    async def publish(self) -> None:
        channel = self._bot.get_channel(ASK_JERRY_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self._bot.fetch_channel(ASK_JERRY_CHANNEL_ID)
            except Exception:
                log.warning("AskJerry: could not fetch channel %s", ASK_JERRY_CHANNEL_ID)
                return

        if not isinstance(channel, discord.TextChannel):
            return

        guild_id = channel.guild.id
        embed = build_hub_embed()
        view = AskJerryView(publisher=self)

        existing_id_raw = await self._repo.kv_get(guild_id, KV_ASK_JERRY_MSG_ID)
        if existing_id_raw:
            try:
                msg = await channel.fetch_message(int(existing_id_raw))
                await msg.edit(embed=embed, view=view)
                log.info("AskJerry: updated hub message %s", existing_id_raw)
                return
            except Exception:
                log.warning("AskJerry: could not edit hub message, recreating")

        try:
            sent = await channel.send(embed=embed, view=view)
            await self._repo.kv_set(guild_id, KV_ASK_JERRY_MSG_ID, str(sent.id))
            log.info("AskJerry: posted hub message %s", sent.id)
            try:
                await sent.pin()
            except discord.Forbidden:
                log.warning("AskJerry: missing pin permission")
            except Exception:
                log.warning("AskJerry: could not pin hub message")
        except Exception:
            log.exception("AskJerry: failed to post hub message")


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

    # Register all persistent category button views
    bot.add_view(AskJerryView(publisher=None))

    log.info("AskJerryCog loaded.")
    return publisher
