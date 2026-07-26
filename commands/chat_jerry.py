from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import random
import re
import string
import time
from collections import deque
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
MIN_KEYWORD_RULE_SCORE = 1
CONTEXT_TTL_SECONDS = 20 * 60
CONTEXT_MAX_MESSAGES = 6

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


def _rule_by_id(rule_id: str | None) -> dict[str, Any] | None:
    if not rule_id:
        return None
    for rule in _reply_rules().get("intents", []):
        if isinstance(rule, dict) and rule.get("id") == rule_id:
            return rule
    return None


def _estimate_level(text: str) -> str:
    cleaned = _clean_text(text)
    words = cleaned.split()
    if not words:
        return "easy"

    word_count = len(words)
    long_words = sum(1 for word in words if len(word) >= 8)
    connectors = {
        "because",
        "although",
        "however",
        "while",
        "before",
        "after",
        "usually",
        "sometimes",
        "probably",
        "actually",
    }
    connector_count = sum(1 for word in words if word in connectors)

    if word_count <= 4:
        return "starter"
    if word_count <= 10 and connector_count == 0 and long_words <= 1:
        return "easy"
    if word_count >= 18 or connector_count >= 2 or long_words >= 3:
        return "strong"
    return "growing"


def _topic_pack(topic_id: str | None) -> dict[str, list[str]]:
    if topic_id and topic_id in TOPIC_PACKS:
        return TOPIC_PACKS[topic_id]
    return TOPIC_PACKS["default"]


def _choose_from_pack(
    topic_id: str | None,
    key: str,
    *,
    text: str,
    display_name: str,
    level: str,
) -> str:
    pack = _topic_pack(topic_id)
    if key == "questions" and level in {"starter", "easy"}:
        items = pack.get("easy_questions") or pack.get("questions", [])
    else:
        items = pack.get(key, [])
    return _render_template(
        _choose(items, text=text, display_name=display_name),
        display_name=display_name,
    )


def _recent_topic_id(recent: list[dict[str, Any]] | None) -> str | None:
    if not recent:
        return None
    for item in reversed(recent):
        topic_id = item.get("topic_id")
        if isinstance(topic_id, str) and topic_id:
            return topic_id
    return None


def _context_hint(recent: list[dict[str, Any]] | None, topic_id: str | None) -> str:
    if not recent or not topic_id:
        return ""
    last_topic = _recent_topic_id(recent)
    if last_topic != topic_id:
        return ""
    if len(recent) < 2:
        return ""
    return "Still on this topic."


def _level_hint(level: str) -> str:
    if level == "starter":
        return "Try one full sentence."
    if level == "easy":
        return "You can keep it simple."
    if level == "strong":
        return "Nice detail."
    return ""


def _format_reply(
    *,
    base_reply: str,
    topic_id: str | None,
    level: str,
    recent: list[dict[str, Any]] | None,
) -> str:
    parts = [base_reply]
    hint = _context_hint(recent, topic_id)
    if hint:
        parts.append(hint)
    if topic_id in {"greeting", "thanks", "goodbye", "topic_request"}:
        level_hint = ""
    else:
        level_hint = _level_hint(level)
    if level_hint:
        parts.append(level_hint)
    return " ".join(part for part in parts if part).strip()


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
    rules = _reply_rules()
    fallback_replies = rules.get("fallback_replies", [])
    fallback_follow_ups = rules.get("fallback_follow_ups", [])
    if isinstance(fallback_replies, list) and fallback_replies:
        reply = _render_template(
            _choose(fallback_replies, text=text, display_name=display_name),
            display_name=display_name,
        )
        follow_up = _render_template(
            _choose(fallback_follow_ups, text=text, display_name=display_name),
            display_name=display_name,
        )
        return " ".join(part for part in (reply, follow_up) if part)

    suggestions = _fallback_suggestions(text, display_name)
    topic = suggestions[0] if suggestions else "your day"
    return f"I'm not sure what to say to that yet. Try asking about {topic}."


def _reply_payload_for_text(
    text: str,
    display_name: str,
    *,
    recent: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    lower = text.lower().strip()
    rule = _matched_reply_rule(text)
    recent_topic_id = _recent_topic_id(recent)
    if rule is None and recent_topic_id in CONTEXTUAL_TOPIC_IDS:
        rule = _rule_by_id(recent_topic_id)

    level = _estimate_level(text)
    if rule is not None:
        topic_id = str(rule.get("id", ""))
    elif recent_topic_id in CONTEXTUAL_TOPIC_IDS:
        topic_id = recent_topic_id
    else:
        topic_id = None

    if rule is not None:
        reply = _plain_reply_from_rule(rule, text, display_name)
        return {
            "content": _format_reply(
                base_reply=reply,
                topic_id=topic_id,
                level=level,
                recent=recent,
            ),
            "topic_id": topic_id,
            "level": level,
        }
    if any(word in lower for word in NERVOUS_WORDS):
        return {
            "content": "That feeling is normal. Start tiny: one sentence is enough.",
            "topic_id": "nervous_shy",
            "level": level,
        }
    if any(word in lower for word in HELP_WORDS):
        return {
            "content": "Tell me one small idea, and I will help you make it clearer.",
            "topic_id": "help",
            "level": level,
        }
    if any(word in lower for word in THANKS_WORDS):
        return {
            "content": "You are welcome. Want to keep going?",
            "topic_id": "thanks",
            "level": level,
        }
    return {
        "content": _format_reply(
            base_reply=_fallback_plain_reply(text, display_name),
            topic_id=topic_id,
            level=level,
            recent=recent,
        ),
        "topic_id": topic_id or "default",
        "level": level,
    }


def _plain_reply_for_text(text: str, display_name: str) -> str:
    return str(_reply_payload_for_text(text, display_name).get("content", ""))


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


class ChatJerryReplyView(discord.ui.View):
    def __init__(
        self,
        *,
        topic_id: str | None,
        level: str,
        seed_text: str,
        display_name: str,
    ) -> None:
        super().__init__(timeout=10 * 60)
        self.topic_id = topic_id or "default"
        self.level = level
        self.seed_text = seed_text
        self.display_name = display_name

    async def _send_pack_item(
        self,
        interaction: discord.Interaction,
        *,
        key: str,
        prefix: str = "",
        ephemeral: bool = False,
        level: str | None = None,
    ) -> None:
        value = _choose_from_pack(
            self.topic_id,
            key,
            text=f"{interaction.user.id}:{self.seed_text}:{key}",
            display_name=getattr(interaction.user, "display_name", self.display_name),
            level=level or self.level,
        )
        content = f"{prefix}{value}" if prefix else value
        await interaction.response.send_message(content, ephemeral=ephemeral)

    @discord.ui.button(label="Another question", style=discord.ButtonStyle.primary)
    async def another_question(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self._send_pack_item(interaction, key="questions")

    @discord.ui.button(label="Make it easier", style=discord.ButtonStyle.secondary)
    async def make_easier(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self._send_pack_item(
            interaction,
            key="questions",
            prefix="Easy question: ",
            level="easy",
        )

    @discord.ui.button(label="Useful words", style=discord.ButtonStyle.secondary)
    async def useful_words(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        words = _topic_pack(self.topic_id).get("words", TOPIC_PACKS["default"]["words"])
        content = "Useful words: " + ", ".join(words[:5])
        await interaction.response.send_message(content, ephemeral=True)

    @discord.ui.button(label="Example answer", style=discord.ButtonStyle.secondary)
    async def example_answer(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self._send_pack_item(
            interaction,
            key="examples",
            prefix="Example: ",
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
        self._recent_by_user: dict[int, deque[dict[str, Any]]] = {}

    def _recent_context(self, user_id: int) -> list[dict[str, Any]]:
        now = time.time()
        recent = self._recent_by_user.get(user_id)
        if recent is None:
            return []

        while recent and now - float(recent[0].get("ts", 0)) > CONTEXT_TTL_SECONDS:
            recent.popleft()
        if not recent:
            self._recent_by_user.pop(user_id, None)
            return []
        return list(recent)

    def _remember_context(
        self,
        *,
        user_id: int,
        text: str,
        topic_id: str | None,
        level: str,
    ) -> None:
        recent = self._recent_by_user.setdefault(
            user_id,
            deque(maxlen=CONTEXT_MAX_MESSAGES),
        )
        recent.append(
            {
                "ts": time.time(),
                "text": text,
                "topic_id": topic_id or "default",
                "level": level,
            }
        )

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

        recent = self._recent_context(message.author.id)
        payload = _reply_payload_for_text(
            text,
            message.author.display_name,
            recent=recent,
        )
        reply = str(payload.get("content", "")).strip()
        topic_id = str(payload.get("topic_id", "default") or "default")
        level = str(payload.get("level", "easy") or "easy")
        self._remember_context(
            user_id=message.author.id,
            text=text,
            topic_id=topic_id,
            level=level,
        )

        try:
            async with message.channel.typing():
                await asyncio.sleep(_typing_delay_seconds(text))
            await message.reply(
                reply,
                mention_author=False,
                view=ChatJerryReplyView(
                    topic_id=topic_id,
                    level=level,
                    seed_text=text,
                    display_name=message.author.display_name,
                ),
            )
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
