from __future__ import annotations

import datetime as dt
import json
import logging
import re
import string
import time
from collections import deque
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

log = logging.getLogger("commands.chat_jerry")

EN_DAILY_CHAT_CHANNEL_ID = 1181652390835916814
NL_DAILY_CHAT_CHANNEL_ID = 1336419902155919410
KV_CHAT_JERRY_DAILY_EN_DATE = "chat_jerry_daily_check_in_en_date_v1"
KV_CHAT_JERRY_DAILY_NL_DATE = "chat_jerry_daily_check_in_nl_date_v1"
KV_CHAT_JERRY_DAILY_EN_TOPIC = "chat_jerry_daily_check_in_en_topic_v1"
KV_CHAT_JERRY_DAILY_NL_TOPIC = "chat_jerry_daily_check_in_nl_topic_v1"
REPLY_RULES_PATH = Path(__file__).with_name("chat_jerry_replies.json")


GREETING_WORDS = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
MIN_KEYWORD_RULE_SCORE = 1

TOPIC_PACKS: dict[str, dict[str, list[str]]] = {
    "daily_life": {
        "questions": [
            "What was the best part of your day?",
            "What did you do first today?",
            "Was your day busy or quiet?",
            "What will you do later?",
        ],
        "easy_questions": [
            "What did you do today?",
            "Was today good?",
            "What will you do later?",
        ],
        "words": ["busy", "quiet", "later", "first", "after that"],
        "examples": [
            "Today was busy, but I finished my work.",
            "I stayed home and relaxed.",
            "This morning I went shopping.",
        ],
    },
    "work_study": {
        "questions": [
            "What was difficult at work or school today?",
            "What do you need to explain in English?",
            "Was your meeting or class easy to follow?",
            "What is one useful sentence for your work?",
        ],
        "easy_questions": [
            "Do you work or study?",
            "Was it busy today?",
            "What is your job or class?",
        ],
        "words": ["deadline", "meeting", "task", "explain", "busy"],
        "examples": [
            "I had a busy meeting today.",
            "I need to explain my project clearly.",
            "My homework was difficult but useful.",
        ],
    },
    "food": {
        "questions": [
            "What food do you like most?",
            "Do you prefer cooking at home or eating out?",
            "What meal did you eat today?",
            "Is there a food you want to try?",
        ],
        "easy_questions": [
            "What food do you like?",
            "Did you eat breakfast?",
            "Do you cook?",
        ],
        "words": ["spicy", "sweet", "salty", "fresh", "homemade"],
        "examples": [
            "I like spicy food because it has a strong taste.",
            "I cooked rice and chicken for dinner.",
            "My favourite drink is coffee.",
        ],
    },
    "travel": {
        "questions": [
            "Where would you like to travel next?",
            "What would you do first in that place?",
            "Do you prefer cities, beaches, or nature?",
            "Who would you travel with?",
        ],
        "easy_questions": [
            "Where do you want to go?",
            "Do you like travel?",
            "City or beach?",
        ],
        "words": ["trip", "flight", "hotel", "visit", "recommend"],
        "examples": [
            "I would like to visit Japan because the food looks amazing.",
            "I prefer quiet places near nature.",
            "First, I would walk around the city.",
        ],
    },
    "hobbies": {
        "questions": [
            "What do you like doing in your free time?",
            "How often do you do that hobby?",
            "Did you start recently or a long time ago?",
            "What makes that hobby fun?",
        ],
        "easy_questions": [
            "What is your hobby?",
            "Do you like games or sports?",
            "Is it fun?",
        ],
        "words": ["free time", "relaxing", "creative", "improve", "often"],
        "examples": [
            "In my free time, I like reading books.",
            "I go to the gym because it gives me energy.",
            "I started this hobby last year.",
        ],
    },
    "movies_music": {
        "questions": [
            "What did you watch or listen to recently?",
            "Would you recommend it?",
            "What kind of movies or music do you usually like?",
            "Can you explain the story or song simply?",
        ],
        "easy_questions": [
            "Do you like music?",
            "What did you watch?",
            "Was it good?",
        ],
        "words": ["recommend", "episode", "actor", "singer", "story"],
        "examples": [
            "I watched a series on Netflix yesterday.",
            "I like calm music when I work.",
            "The movie was funny but a little long.",
        ],
    },
    "family_friends": {
        "questions": [
            "Who did you talk to recently?",
            "What do you usually do together?",
            "How would you describe that person?",
            "Do you see your family or friends often?",
        ],
        "easy_questions": [
            "Do you have siblings?",
            "Who is your friend?",
            "Do you see them often?",
        ],
        "words": ["kind", "supportive", "funny", "close", "often"],
        "examples": [
            "My friend is funny and easy to talk to.",
            "I visited my family last weekend.",
            "My brother helps me when I am busy.",
        ],
    },
    "goals_learning": {
        "questions": [
            "What is one small goal for this week?",
            "Why is that goal important to you?",
            "What makes learning English difficult right now?",
            "How can you practise today?",
        ],
        "easy_questions": [
            "What do you want to learn?",
            "What is your goal?",
            "Can you practise today?",
        ],
        "words": ["goal", "habit", "progress", "improve", "small step"],
        "examples": [
            "My goal is to speak more confidently.",
            "I want to practise for ten minutes every day.",
            "A small step is better than doing nothing.",
        ],
    },
    "weather": {
        "questions": [
            "What is the weather like where you are?",
            "Do you like that kind of weather?",
            "Does the weather change your mood?",
            "What season do you like most?",
        ],
        "easy_questions": [
            "Is it hot or cold?",
            "Is it raining?",
            "Do you like the weather?",
        ],
        "words": ["sunny", "cloudy", "windy", "warm", "cold"],
        "examples": [
            "It is cloudy today, but it is not cold.",
            "I like sunny weather because I can walk outside.",
            "Rainy days make me feel sleepy.",
        ],
    },
    "default": {
        "questions": [
            "Can you tell me one more detail?",
            "Why is that important to you?",
            "How did you feel about it?",
            "What happened next?",
        ],
        "easy_questions": [
            "Can you say more?",
            "Was it good?",
            "What happened?",
        ],
        "words": ["because", "usually", "sometimes", "today", "next"],
        "examples": [
            "I think it is useful because I can practise real English.",
            "Today I want to speak a little more.",
            "I am not sure, but I want to try.",
        ],
    },
}
CONTEXTUAL_TOPIC_IDS = set(TOPIC_PACKS) - {"default"}
RELATED_TOPIC_MAP = {
    "english_practice": "goals_learning",
    "correction_request": "goals_learning",
    "interview_exam": "work_study",
    "health": "daily_life",
    "money_shopping": "daily_life",
    "opinions": "goals_learning",
    "short_answer": "daily_life",
    "topic_request": "goals_learning",
}


EN_DAILY_QUESTIONS: list[str] = [
    "What is one sentence you want to practise today?",
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
    "Someone answers your question. What can you ask next?",
    "What is a simple opinion you can explain with one reason?",
    "What is something you do when you do not know the right word?",
    "What is a topic you can talk about for one minute?",
    "What is one thing you want to ask the community today?",
]

NL_DAILY_QUESTIONS: list[str] = [
    "Welke zin wil je vandaag oefenen?",
    "Wat was een goed moment van gisteren?",
    "Waar kijk je deze week naar uit?",
    "Welke gewoonte helpt jou om een taal te leren?",
    "Wat kun je uitleggen in twee simpele zinnen?",
    "Wat vond je laatst moeilijk, en wat deed je toen?",
    "Welk advies zou je geven aan iemand die zenuwachtig is om te spreken?",
    "Welke zin gebruik je vaak in het dagelijks leven?",
    "Wat heb je deze week geleerd?",
    "Welke plek ken je goed, en waarom vind je die plek fijn?",
    "Welke vraag kun je stellen om een gesprek te beginnen?",
    "Wat zou je vaker willen doen?",
    "Waar ben je trots op?",
    "Welk klein doel kun je vandaag afmaken?",
    "Wat doe je meestal in de ochtend?",
    "Welk woord of welke zin wil je makkelijker kunnen zeggen?",
    "Wat maakt een gesprek makkelijker voor jou?",
    "Welke fout heeft jou iets nuttigs geleerd?",
    "Wat kun je beschrijven zonder eerst te vertalen?",
    "Iemand geeft antwoord. Welke vraag kun je dan terug stellen?",
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


def _daily_question_for_date(date_key: str, *, is_nl: bool = False) -> str:
    seed = sum(ord(ch) for ch in date_key)
    questions = NL_DAILY_QUESTIONS if is_nl else EN_DAILY_QUESTIONS
    return questions[seed % len(questions)]


def _contextual_topic_id(topic_id: str | None) -> str | None:
    if not topic_id:
        return None
    if topic_id in CONTEXTUAL_TOPIC_IDS:
        return topic_id
    mapped = RELATED_TOPIC_MAP.get(topic_id)
    if mapped in CONTEXTUAL_TOPIC_IDS:
        return mapped
    return None


def _topic_id_for_text(text: str) -> str | None:
    rule = _matched_reply_rule(text)
    if rule is None:
        return None
    return _contextual_topic_id(str(rule.get("id", "")))


def _topic_id_for_daily_question(question: str) -> str:
    lower = question.lower()
    if any(word in lower for word in ("place", "travel", "country", "plek", "reizen", "land")):
        return "travel"
    if any(word in lower for word in ("morning", "yesterday", "today", "daily life", "ochtend", "gisteren", "vandaag")):
        return "daily_life"
    if any(word in lower for word in ("work", "school", "job", "werk", "baan")):
        return "work_study"
    if any(word in lower for word in ("food", "meal", "eat", "eten", "maaltijd")):
        return "food"
    if any(word in lower for word in ("friend", "family", "community", "vriend", "familie", "gemeenschap")):
        return "family_friends"
    inferred = _topic_id_for_text(question)
    return inferred or "goals_learning"


def _daily_question_meta(date_key: str, *, is_nl: bool) -> dict[str, str]:
    question = _daily_question_for_date(date_key, is_nl=is_nl)
    return {
        "date": date_key,
        "question": question,
        "topic_id": _topic_id_for_daily_question(question),
    }


def _clean_text(text: str) -> str:
    cleaned = text.lower().strip()
    cleaned = cleaned.strip(string.whitespace + string.punctuation)
    return " ".join(cleaned.split())


def _is_greeting(text: str) -> bool:
    cleaned = _clean_text(text)
    if cleaned in GREETING_WORDS:
        return True
    return any(cleaned.startswith(greeting + " ") for greeting in GREETING_WORDS)


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


def _keyword_score(keyword: str, *, lower: str, cleaned: str) -> int:
    keyword = keyword.lower().strip()
    if not keyword:
        return 0
    if " " in keyword or "'" in keyword:
        return 4 if keyword in lower else 0
    return 2 if re.search(rf"\b{re.escape(keyword)}\b", cleaned) else 0


def _rule_score(rule: dict[str, Any], text: str) -> int:
    lower = text.lower().strip()
    cleaned = _clean_text(text)
    keywords = [str(k) for k in rule.get("keywords", [])]
    topics = [str(k) for k in rule.get("topics", [])]
    match_type = str(rule.get("match", "contains"))

    if match_type == "greeting":
        return 100 if _is_greeting(text) else 0
    if match_type == "exact":
        return 100 if cleaned in {keyword.lower().strip() for keyword in keywords} else 0

    score = sum(_keyword_score(keyword, lower=lower, cleaned=cleaned) for keyword in keywords)
    score += sum(_keyword_score(topic, lower=lower, cleaned=cleaned) for topic in topics)

    if score <= 0:
        return 0

    try:
        priority = int(rule.get("priority", 0))
    except Exception:
        priority = 0
    return score + priority


def _matched_reply_rule(text: str) -> dict[str, Any] | None:
    best_rule: dict[str, Any] | None = None
    best_score = 0
    for rule in _reply_rules().get("intents", []):
        if not isinstance(rule, dict):
            continue
        score = _rule_score(rule, text)
        if score > best_score:
            best_rule = rule
            best_score = score
    if best_score >= MIN_KEYWORD_RULE_SCORE:
        return best_rule
    return None


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
        topic_kv_key = KV_CHAT_JERRY_DAILY_NL_TOPIC if is_nl else KV_CHAT_JERRY_DAILY_EN_TOPIC

        if not force:
            last_posted = await self._repo.kv_get(guild_id, kv_key)
            if last_posted == date_key:
                return

        channel = await self._get_text_channel(channel_id)
        if channel is None:
            return

        daily_meta = _daily_question_meta(date_key, is_nl=is_nl)
        question = daily_meta["question"]
        if is_nl:
            content = (
                "Goedemorgen. De vraag van vandaag:\n\n"
                f"**{question}**\n\n"
                "Antwoord met een of twee zinnen. Fouten zijn welkom."
            )
        else:
            content = (
                "Good morning. Today's question:\n\n"
                f"**{question}**\n\n"
                "Reply with one or two sentences. Mistakes are welcome."
            )

        try:
            await channel.send(content, allowed_mentions=discord.AllowedMentions.none())
            await self._repo.kv_set(guild_id, topic_kv_key, json.dumps(daily_meta, sort_keys=True))
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
        self._recent_by_user: dict[int, deque[dict[str, Any]]] = {}


    async def _handle_daily_chat_message(self, message: discord.Message) -> None:
        if message.guild is None:
            return

        text = (message.content or "").strip()
        if not text or text.startswith("/"):
            return

        now = int(time.time())

        try:
            await self.repo.command_usage_record(
                message.guild.id,
                message.author.id,
                "daily_question_reply",
                now,
            )
        except Exception:
            log.exception("ChatJerry: failed to record daily question reply usage")

    async def handle_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if message.channel.id in {EN_DAILY_CHAT_CHANNEL_ID, NL_DAILY_CHAT_CHANNEL_ID}:
            await self._handle_daily_chat_message(message)
            return


async def setup(bot: commands.Bot, repo: Any, *, guild_id: int) -> ChatJerryPublisher:
    publisher = ChatJerryPublisher(bot=bot, repo=repo)
    await bot.add_cog(ChatJerryCog(bot, repo, publisher))
    log.info("ChatJerryCog loaded.")
    return publisher
