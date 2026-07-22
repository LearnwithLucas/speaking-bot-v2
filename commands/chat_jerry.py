from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import random
import re
import string
import time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("commands.chat_jerry")

CHAT_WITH_JERRY_CHANNEL_ID = 1523060567621763163
EN_DAILY_CHAT_CHANNEL_ID = 1181652390835916814
NL_DAILY_CHAT_CHANNEL_ID = 1336419902155919410
KV_CHAT_JERRY_HUB_MSG = "chat_jerry_hub_message_id_v1"
KV_CHAT_JERRY_DAILY_EN_DATE = "chat_jerry_daily_check_in_en_date_v1"
KV_CHAT_JERRY_DAILY_NL_DATE = "chat_jerry_daily_check_in_nl_date_v1"
REPLY_RULES_PATH = Path(__file__).with_name("chat_jerry_replies.json")

MIN_TYPING_DELAY_SECONDS = 1.0
MAX_TYPING_DELAY_SECONDS = 3.5

GREETING_WORDS = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
NERVOUS_WORDS = {"nervous", "scared", "shy", "afraid", "embarrassed", "anxious", "stress", "worried"}
HELP_WORDS = {"help", "stuck", "confused", "hard", "difficult", "don't know", "dont know"}
THANKS_WORDS = {"thanks", "thank you", "thx"}

QUESTION_SETS = [
    "How are you today?",
    "What did you do today?",
    "What food do you like?",
    "Where would you like to travel?",
    "What do you want to get better at?",
    "What was the best part of your day?",
]

EN_DAILY_QUESTIONS: list[str] = [
    "What is one small thing you want to practise saying today?",
    "What was a good moment from yesterday?",
    "What is something you are looking forward to this week?",
    "What is one habit that helps you learn a language?",
    "What is something you can explain in two simple sentences?",
    "What is one thing you found difficult recently, and how did you handle it?",
    "What advice would you give to someone who is nervous about speaking?",
    "What is one sentence you use often in daily life?",
    "What is something you learned this week?",
    "What is a place you know well, and why do you like it?",
    "What is one question you can ask someone to start a conversation?",
    "What is something you would like to do more often?",
    "What is one thing you are proud of?",
    "What is a small goal you can finish today?",
    "What is something you usually do in the morning?",
    "What is a word or phrase you want to use more confidently?",
    "What is something that makes a conversation easier for you?",
    "What is one mistake you made that taught you something useful?",
    "What is something you can describe without translating first?",
    "What is one friendly follow-up question you can ask after someone answers?",
    "What is a simple opinion you can explain with one reason?",
    "What is something you do when you do not know the right word?",
    "What is a topic you can talk about for one minute?",
    "What is one thing you want to ask the community today?",
]

NL_DAILY_QUESTIONS: list[str] = [
    "Wat is een klein ding dat je vandaag wilt oefenen met zeggen?",
    "Wat was een goed moment van gisteren?",
    "Waar kijk je deze week naar uit?",
    "Welke gewoonte helpt jou om een taal te leren?",
    "Wat kun je uitleggen in twee simpele zinnen?",
    "Wat vond je de laatste tijd moeilijk, en hoe ging je ermee om?",
    "Welk advies zou je geven aan iemand die zenuwachtig is om te spreken?",
    "Welke zin gebruik je vaak in het dagelijks leven?",
    "Wat heb je deze week geleerd?",
    "Welke plek ken je goed, en waarom vind je die plek fijn?",
    "Welke vraag kun je stellen om een gesprek te beginnen?",
    "Wat zou je vaker willen doen?",
    "Waar ben je trots op?",
    "Welk klein doel kun je vandaag afmaken?",
    "Wat doe je meestal in de ochtend?",
    "Welk woord of welke zin wil je met meer vertrouwen gebruiken?",
    "Wat maakt een gesprek makkelijker voor jou?",
    "Welke fout heeft jou iets nuttigs geleerd?",
    "Wat kun je beschrijven zonder eerst te vertalen?",
    "Welke vriendelijke vervolgvraag kun je stellen nadat iemand antwoord geeft?",
    "Welke simpele mening kun je uitleggen met een reden?",
    "Wat doe je als je het juiste woord niet weet?",
    "Over welk onderwerp kun je een minuut praten?",
    "Wat wil je vandaag aan de community vragen?",
]

DEFAULT_REPLY_RULES: dict[str, Any] = {
    "fallback_suggestions": ["your day", "travel", "food", "work", "English practice"],
    "intents": [
        {
            "id": "greeting",
            "match": "greeting",
            "keywords": ["hey", "hi", "hello"],
            "replies": ["Hey {name}. How are you?"],
            "follow_ups": ["What are you doing today?"],
        }
    ],
}
_REPLY_RULES_CACHE: dict[str, Any] | None = None


def _pick_question(seed: int | None = None) -> str:
    if seed is None:
        return random.choice(QUESTION_SETS)
    return QUESTION_SETS[seed % len(QUESTION_SETS)]


def _daily_question_for_date(date_key: str, *, is_nl: bool = False) -> str:
    seed = sum(ord(ch) for ch in date_key)
    questions = NL_DAILY_QUESTIONS if is_nl else EN_DAILY_QUESTIONS
    return questions[seed % len(questions)]


def _clean_text(text: str) -> str:
    cleaned = text.lower().strip()
    cleaned = cleaned.strip(string.whitespace + string.punctuation)
    return " ".join(cleaned.split())


def _is_greeting(text: str) -> bool:
    cleaned = _clean_text(text)
    if cleaned in GREETING_WORDS:
        return True
    return any(cleaned.startswith(greeting + " ") for greeting in GREETING_WORDS)


def _reply_seed(text: str, display_name: str) -> int:
    return sum(ord(ch) for ch in f"{display_name}:{text}")


def _reply_rules() -> dict[str, Any]:
    global _REPLY_RULES_CACHE
    if _REPLY_RULES_CACHE is not None:
        return _REPLY_RULES_CACHE

    try:
        with REPLY_RULES_PATH.open("r", encoding="utf-8") as fp:
            rules = json.load(fp)
        if not isinstance(rules, dict) or not isinstance(rules.get("intents"), list):
            raise ValueError("chat_jerry_replies.json must contain an intents list")
        _REPLY_RULES_CACHE = rules
    except Exception:
        log.exception("ChatJerry: could not load reply rules from %s", REPLY_RULES_PATH)
        _REPLY_RULES_CACHE = DEFAULT_REPLY_RULES
    return _REPLY_RULES_CACHE


def _choose(items: Any, *, text: str, display_name: str) -> str:
    if isinstance(items, str):
        return items
    if not isinstance(items, list) or not items:
        return ""
    return str(items[_reply_seed(text, display_name) % len(items)])


def _render_template(template: str, *, display_name: str) -> str:
    try:
        time_amsterdam = dt.datetime.now(ZoneInfo("Europe/Amsterdam")).strftime("%H:%M")
    except Exception:
        time_amsterdam = dt.datetime.now().strftime("%H:%M")

    try:
        return template.format(
            name=discord.utils.escape_markdown(display_name),
            time_amsterdam=time_amsterdam,
        )
    except Exception:
        return template


def _keyword_in_text(keyword: str, *, lower: str, cleaned: str) -> bool:
    keyword = keyword.lower().strip()
    if not keyword:
        return False
    if " " in keyword or "'" in keyword:
        return keyword in lower
    return bool(re.search(rf"\b{re.escape(keyword)}\b", cleaned))


def _rule_matches(rule: dict[str, Any], text: str) -> bool:
    lower = text.lower().strip()
    cleaned = _clean_text(text)
    keywords = [str(k) for k in rule.get("keywords", [])]
    match_type = str(rule.get("match", "contains"))

    if match_type == "greeting":
        return _is_greeting(text)
    if match_type == "exact":
        return cleaned in {keyword.lower().strip() for keyword in keywords}
    return any(_keyword_in_text(keyword, lower=lower, cleaned=cleaned) for keyword in keywords)


def _matched_reply_rule(text: str) -> dict[str, Any] | None:
    for rule in _reply_rules().get("intents", []):
        if isinstance(rule, dict) and _rule_matches(rule, text):
            return rule
    return None


def _fallback_suggestions(text: str, display_name: str) -> list[str]:
    suggestions = _reply_rules().get("fallback_suggestions", [])
    if not isinstance(suggestions, list) or not suggestions:
        suggestions = DEFAULT_REPLY_RULES["fallback_suggestions"]

    ordered = [str(item) for item in suggestions if str(item).strip()]
    if not ordered:
        return ["your day"]
    start = _reply_seed(text, display_name) % len(ordered)
    return (ordered[start:] + ordered[:start])[:2]


def _plain_reply_from_rule(rule: dict[str, Any], text: str, display_name: str) -> str:
    reply = _render_template(
        _choose(rule.get("replies", ""), text=text, display_name=display_name),
        display_name=display_name,
    )
    follow_up = _render_template(
        _choose(rule.get("follow_ups", ""), text=text, display_name=display_name),
        display_name=display_name,
    )
    parts = [part for part in (reply, follow_up) if part]

    lower = text.lower()
    if rule.get("id") == "travel" and ("evil tour" in lower or "evil tower" in lower):
        parts.append('Small correction: say "the Eiffel Tower".')

    if parts:
        return " ".join(parts)
    return f"I'm here, {discord.utils.escape_markdown(display_name)}. What do you want to talk about?"


def _fallback_plain_reply(text: str, display_name: str) -> str:
    suggestions = _fallback_suggestions(text, display_name)
    topic = suggestions[0] if suggestions else "your day"
    return f"I'm not sure what to say to that yet. Try asking about {topic}."


def _plain_reply_for_text(text: str, display_name: str) -> str:
    lower = text.lower().strip()
    rule = _matched_reply_rule(text)

    if rule is not None:
        return _plain_reply_from_rule(rule, text, display_name)
    if any(word in lower for word in NERVOUS_WORDS):
        return "That feeling is normal. Start tiny: one sentence is enough."
    if any(word in lower for word in HELP_WORDS):
        return "Tell me one small idea, and I will help you make it clearer."
    if any(word in lower for word in THANKS_WORDS):
        return "You're welcome. Want to keep going?"
    return _fallback_plain_reply(text, display_name)


def _typing_delay_seconds(text: str) -> float:
    return min(MAX_TYPING_DELAY_SECONDS, MIN_TYPING_DELAY_SECONDS + len(text) / 80)


class ChatJerryHubView(discord.ui.View):
    def __init__(self, *, publisher: "ChatJerryPublisher | None" = None) -> None:
        super().__init__(timeout=None)
        self._publisher = publisher

    @discord.ui.button(label="Ask me a question", style=discord.ButtonStyle.primary, custom_id="chatjerry:question:v1")
    async def ask_question(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        prompt = _pick_question(interaction.user.id + int(time.time() // 3600))
        await interaction.response.send_message(prompt)

    @discord.ui.button(label="Useful words", style=discord.ButtonStyle.secondary, custom_id="chatjerry:words:v1")
    async def useful_words(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            'Useful phrases: "Give me a second." "How do I say this?" "Can I try again?"',
            ephemeral=True,
        )

    @discord.ui.button(label="I feel nervous", style=discord.ButtonStyle.secondary, custom_id="chatjerry:nervous:v1")
    async def nervous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            'Start smaller: "Today I feel..." or "I want to practise..." One sentence is enough.',
            ephemeral=True,
        )


class ChatJerryPublisher:
    def __init__(self, *, bot: discord.Client, repo: Any) -> None:
        self._bot = bot
        self._repo = repo

    async def _get_text_channel(self, channel_id: int) -> discord.TextChannel | None:
        channel = self._bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self._bot.fetch_channel(channel_id)
            except Exception:
                log.warning("ChatJerry: could not fetch channel %s", channel_id)
                return None
        if not isinstance(channel, discord.TextChannel):
            log.warning("ChatJerry: channel %s is not a text channel", channel_id)
            return None
        return channel

    async def publish(self, guild_id: int) -> None:
        channel = await self._get_text_channel(CHAT_WITH_JERRY_CHANNEL_ID)
        if channel is None:
            return

        content = (
            "Chat with Jerry\n\n"
            'Send a normal message like "hey", "how are you?", or "give me a question". '
            "Jerry replies once to each message, like a simple chat."
        )
        existing_id_raw = await self._repo.kv_get(guild_id, KV_CHAT_JERRY_HUB_MSG)
        if existing_id_raw:
            try:
                msg = await channel.fetch_message(int(existing_id_raw))
                await msg.edit(content=content, embed=None, view=None)
                log.info("ChatJerry: updated hub message %s", existing_id_raw)
                return
            except Exception:
                log.warning("ChatJerry: could not edit hub message, recreating")

        try:
            sent = await channel.send(content)
            await self._repo.kv_set(guild_id, KV_CHAT_JERRY_HUB_MSG, str(sent.id))
            log.info("ChatJerry: posted hub message %s", sent.id)
            try:
                await sent.pin()
            except discord.Forbidden:
                log.warning("ChatJerry: missing pin permission channel=%s", CHAT_WITH_JERRY_CHANNEL_ID)
        except Exception:
            log.exception("ChatJerry: failed to post hub")

    async def publish_daily_question(
        self,
        guild_id: int,
        *,
        force: bool = False,
        is_nl: bool = False,
        date_key: str | None = None,
    ) -> None:
        if date_key is None:
            try:
                now = dt.datetime.now(ZoneInfo("Europe/Amsterdam"))
            except Exception:
                now = dt.datetime.now()
            date_key = now.date().isoformat()

        channel_id = NL_DAILY_CHAT_CHANNEL_ID if is_nl else EN_DAILY_CHAT_CHANNEL_ID
        kv_key = KV_CHAT_JERRY_DAILY_NL_DATE if is_nl else KV_CHAT_JERRY_DAILY_EN_DATE

        if not force:
            last_posted = await self._repo.kv_get(guild_id, kv_key)
            if last_posted == date_key:
                return

        channel = await self._get_text_channel(channel_id)
        if channel is None:
            return

        question = _daily_question_for_date(date_key, is_nl=is_nl)
        if is_nl:
            content = (
                "Goedemorgen. Dagelijkse vraag:\n\n"
                f"**{question}**\n\n"
                "Antwoord met een of twee zinnen. Fouten zijn welkom."
            )
        else:
            content = (
                "Good morning. Daily question:\n\n"
                f"**{question}**\n\n"
                "Reply with one or two sentences. Mistakes are welcome."
            )

        try:
            await channel.send(content, allowed_mentions=discord.AllowedMentions.none())
            if not force:
                await self._repo.kv_set(guild_id, kv_key, date_key)
            log.info(
                "ChatJerry: posted daily question guild=%s channel=%s date=%s force=%s",
                guild_id,
                channel_id,
                date_key,
                force,
            )
        except Exception:
            log.exception("ChatJerry: failed to post daily question channel=%s", channel_id)


class ChatJerryCog(commands.Cog):
    def __init__(self, bot: commands.Bot, repo: Any, publisher: ChatJerryPublisher) -> None:
        self.bot = bot
        self.repo = repo
        self.publisher = publisher

    async def handle_message(self, message: discord.Message) -> None:
        if message.author.bot or message.channel.id != CHAT_WITH_JERRY_CHANNEL_ID:
            return

        text = (message.content or "").strip()
        if not text or text.startswith("/"):
            return

        now = time.time()

        try:
            if message.guild:
                await self.repo.command_usage_record(message.guild.id, message.author.id, "chatjerry_message", int(now))
        except Exception:
            log.exception("ChatJerry: failed to record message usage")

        reply = _plain_reply_for_text(text, message.author.display_name)
        try:
            async with message.channel.typing():
                await asyncio.sleep(_typing_delay_seconds(text))
            await message.reply(reply, mention_author=False)
        except Exception:
            log.exception("ChatJerry: failed to reply to message")

    @app_commands.command(name="chat", description="Start a small guided conversation with Jerry.")
    async def chat(self, interaction: discord.Interaction) -> None:
        if interaction.channel_id != CHAT_WITH_JERRY_CHANNEL_ID:
            await interaction.response.send_message(
                f"Use this in <#{CHAT_WITH_JERRY_CHANNEL_ID}> so the conversation stays in one place.",
                ephemeral=True,
            )
            return
        prompt = _pick_question(interaction.user.id + int(time.time()))
        await interaction.response.send_message(prompt)


async def setup(bot: commands.Bot, repo: Any, *, guild_id: int) -> ChatJerryPublisher:
    publisher = ChatJerryPublisher(bot=bot, repo=repo)
    await bot.add_cog(ChatJerryCog(bot, repo, publisher))
    bot.add_view(ChatJerryHubView(publisher=None))
    log.info("ChatJerryCog loaded.")
    return publisher
