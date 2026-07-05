from __future__ import annotations

import datetime as dt
import logging
import random
import string
import time
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("commands.chat_jerry")

CHAT_WITH_JERRY_CHANNEL_ID = 1523060567621763163
KV_CHAT_JERRY_HUB_MSG = "chat_jerry_hub_message_id_v1"
KV_CHAT_JERRY_DAILY_DATE = "chat_jerry_daily_question_date_v1"

QUESTION_SETS = [
    {
        "question": "What is one small thing you did today?",
        "easier": "Start with: Today I...",
        "sample": "Today I had coffee and answered a few messages. It was a quiet start.",
        "words": "small thing, quiet start, a few messages, after that, later today",
    },
    {
        "question": "What is something you want to get better at this month?",
        "easier": "Start with: This month, I want to improve...",
        "sample": "This month, I want to improve my speaking confidence. I want to speak even when my sentence is not perfect.",
        "words": "improve, confidence, practice, a little more, not perfect yet",
    },
    {
        "question": "What is a place you would like to visit, and why?",
        "easier": "Start with: I would like to visit... because...",
        "sample": "I would like to visit Japan because I like the food, the cities, and the calm gardens.",
        "words": "visit, because, culture, food, peaceful, exciting, one day",
    },
    {
        "question": "What helps you feel calm when English feels difficult?",
        "easier": "Start with: It helps me when...",
        "sample": "It helps me when people speak slowly and give me time to think. Then I feel less pressure.",
        "words": "calm, slowly, time to think, less pressure, try again",
    },
    {
        "question": "What is one thing you can explain well in English?",
        "easier": "Start with: I can explain...",
        "sample": "I can explain my job quite well because I use the same words often.",
        "words": "explain, quite well, because, often, step by step",
    },
    {
        "question": "What kind of conversations do you enjoy most?",
        "easier": "Start with: I enjoy conversations about...",
        "sample": "I enjoy conversations about travel and daily life because they feel natural to me.",
        "words": "daily life, natural, interesting, easy to talk about, personal",
    },
]

NERVOUS_WORDS = {"nervous", "scared", "shy", "afraid", "embarrassed", "anxious", "stress", "worried"}
HELP_WORDS = {"help", "stuck", "confused", "hard", "difficult", "don't know", "dont know"}
GREETING_WORDS = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
THANKS_WORDS = {"thanks", "thank you", "thx"}


def _pick_question(seed: int | None = None) -> dict[str, str]:
    if seed is None:
        return random.choice(QUESTION_SETS)
    return QUESTION_SETS[seed % len(QUESTION_SETS)]


def _today_key() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%d")


def _word_count(text: str) -> int:
    return len([part for part in text.replace("\n", " ").split(" ") if part.strip()])


def _clean_for_greeting(text: str) -> str:
    cleaned = text.lower().strip()
    cleaned = cleaned.strip(string.whitespace + string.punctuation)
    return " ".join(cleaned.split())


def _is_greeting(text: str) -> bool:
    cleaned = _clean_for_greeting(text)
    if cleaned in GREETING_WORDS:
        return True
    return any(cleaned.startswith(greeting + " ") for greeting in GREETING_WORDS)


def build_hub_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Chat with Jerry",
        description=(
            "A calm place to practise tiny English conversations.\n\n"
            "If you are new, just type `hi`, `hey`, or `hello`. Jerry will explain how this channel works "
            "and help you choose a first sentence.\n\n"
            "You can also type a sentence, answer a question, or use the buttons below. "
            "This is practice, not a test. Short answers are welcome."
        ),
    )
    embed.add_field(
        name="Good ways to start",
        value=(
            "`Hi, I want to practise speaking.`\n"
            "`Today I...`\n"
            "`I think... because...`\n"
            "`I want to practise talking about...`"
        ),
        inline=False,
    )
    embed.set_footer(text="chat-with-jerry:hub:v1")
    return embed


def build_prompt_embed(prompt: dict[str, str], *, title: str = "Small speaking question") -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=f"**{prompt['question']}**",
    )
    embed.add_field(name="Make it easier", value=prompt["easier"], inline=False)
    embed.set_footer(text="Reply in the channel, or press a button for help.")
    return embed


def _reply_embed_for_text(text: str, display_name: str) -> discord.Embed:
    lower = text.lower().strip()
    words = _word_count(text)

    if any(word in lower for word in NERVOUS_WORDS):
        title = "That feeling is normal"
        desc = (
            f"Thanks for saying that, {display_name}. Feeling nervous does not mean your English is bad. "
            "It usually means the moment matters to you. Start with one short sentence and let it be enough."
        )
    elif any(word in lower for word in HELP_WORDS):
        title = "Let's make it smaller"
        desc = (
            "When English feels too big, reduce the task. Say one idea, then add one reason.\n\n"
            "Try: `I think ___ because ___.`"
        )
    elif _is_greeting(text):
        title = "Hi, welcome to Chat with Jerry"
        desc = (
            f"Good to see you, {display_name}. This channel is for easy English practice in small steps.\n\n"
            "You can do one of three things:\n"
            "1. Press **Give me a question** for a simple topic.\n"
            "2. Press **Useful phrases** if you need words first.\n"
            "3. Type one short sentence, for example: `Today I feel okay because...`\n\n"
            "No perfect English needed here. One small message is enough to start."
        )
    elif any(word in lower for word in THANKS_WORDS):
        title = "You're welcome"
        desc = "Keep going. One small message is still real practice."
    elif "?" in text:
        title = "Good question"
        desc = (
            "I can help with basic speaking practice here. For a quick answer, keep your question short. "
            "If it is about grammar or vocabulary, try `/d` or Ask Jerry too."
        )
    elif words <= 3:
        title = "Good start"
        desc = (
            "Now make it one step bigger. Add **because** and one reason.\n\n"
            f"Example: `{text.strip()} because...`"
        )
    else:
        title = "Nice, that works"
        desc = (
            "You gave me a real sentence to work with. To make it more conversational, add one detail "
            "or ask the other person a follow-up question."
        )

    embed = discord.Embed(title=title, description=desc)
    embed.set_footer(text="Use the buttons for a next step.")
    return embed


def _feedback_for_text(text: str) -> str:
    words = _word_count(text)
    if _is_greeting(text):
        return (
            "A greeting is a good start. Now add what you want to practise.\n\n"
            "Try: `Hi, I want to practise speaking about my day.`\n"
            "Or: `Hello, can I answer a simple question?`"
        )
    if words <= 3:
        return (
            "Try making it a full sentence with **because**.\n\n"
            f"Your start: `{text.strip()}`\n"
            f"Next version: `{text.strip()} because ...`"
        )
    if "because" not in text.lower():
        return "Good. To make it stronger, add a reason with **because**."
    return "Good sentence. Next step: add one extra detail, then ask a follow-up question."


class ChatJerryHubView(discord.ui.View):
    def __init__(self, *, publisher: "ChatJerryPublisher | None" = None) -> None:
        super().__init__(timeout=None)
        self._publisher = publisher

    def _publisher_for(self, interaction: discord.Interaction) -> "ChatJerryPublisher | None":
        if self._publisher is not None:
            return self._publisher
        repo = getattr(interaction.client, "repo", None)
        if repo is None:
            return None
        return ChatJerryPublisher(bot=interaction.client, repo=repo)

    @discord.ui.button(label="Ask me a question", style=discord.ButtonStyle.primary, custom_id="chatjerry:question:v1")
    async def ask_question(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        publisher = self._publisher_for(interaction)
        if publisher is None:
            await interaction.response.send_message("Jerry is still waking up. Try again in a moment.", ephemeral=True)
            return
        prompt = _pick_question(interaction.user.id + int(time.time() // 3600))
        await interaction.response.send_message(embed=build_prompt_embed(prompt), view=ChatPromptView(prompt))

    @discord.ui.button(label="Useful words", style=discord.ButtonStyle.secondary, custom_id="chatjerry:words:v1")
    async def useful_words(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="Useful speaking phrases",
            description=(
                "Use one of these when you get stuck:\n\n"
                "`Give me a second.`\n"
                "`How do I say this?`\n"
                "`I think the word is...`\n"
                "`What I mean is...`\n"
                "`Can I try again?`"
            ),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="I feel nervous", style=discord.ButtonStyle.secondary, custom_id="chatjerry:nervous:v1")
    async def nervous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="Start smaller",
            description=(
                "You do not need a perfect answer. Try one of these:\n\n"
                "`Today I feel...`\n"
                "`I want to practise...`\n"
                "`One thing about me is...`\n\n"
                "One sentence is enough for a first step."
            ),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ChatPromptView(discord.ui.View):
    def __init__(self, prompt: dict[str, str]) -> None:
        super().__init__(timeout=900)
        self.prompt = prompt

    @discord.ui.button(label="Sample answer", style=discord.ButtonStyle.secondary)
    async def sample(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(self.prompt["sample"], ephemeral=True)

    @discord.ui.button(label="Useful words", style=discord.ButtonStyle.secondary)
    async def words(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(self.prompt["words"], ephemeral=True)

    @discord.ui.button(label="Another question", style=discord.ButtonStyle.primary)
    async def another(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        prompt = _pick_question(interaction.user.id + int(time.time()))
        await interaction.response.send_message(embed=build_prompt_embed(prompt), view=ChatPromptView(prompt))


class ChatReplyView(discord.ui.View):
    def __init__(self, *, original_text: str) -> None:
        super().__init__(timeout=600)
        self.original_text = original_text

    @discord.ui.button(label="Make it better", style=discord.ButtonStyle.secondary)
    async def improve(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(_feedback_for_text(self.original_text), ephemeral=True)

    @discord.ui.button(label="Give me a question", style=discord.ButtonStyle.primary)
    async def question(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        prompt = _pick_question(interaction.user.id + int(time.time()))
        await interaction.response.send_message(embed=build_prompt_embed(prompt), view=ChatPromptView(prompt), ephemeral=True)

    @discord.ui.button(label="Useful phrases", style=discord.ButtonStyle.secondary)
    async def phrases(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            "Try: `I think...`, `In my opinion...`, `For example...`, `What about you?`",
            ephemeral=True,
        )


class ChatJerryPublisher:
    def __init__(self, *, bot: discord.Client, repo: Any) -> None:
        self._bot = bot
        self._repo = repo

    async def publish(self, guild_id: int) -> None:
        channel = self._bot.get_channel(CHAT_WITH_JERRY_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self._bot.fetch_channel(CHAT_WITH_JERRY_CHANNEL_ID)
            except Exception:
                log.warning("ChatJerry: could not fetch channel %s", CHAT_WITH_JERRY_CHANNEL_ID)
                return
        if not isinstance(channel, discord.TextChannel):
            return

        embed = build_hub_embed()
        view = ChatJerryHubView(publisher=self)
        existing_id_raw = await self._repo.kv_get(guild_id, KV_CHAT_JERRY_HUB_MSG)
        if existing_id_raw:
            try:
                msg = await channel.fetch_message(int(existing_id_raw))
                await msg.edit(embed=embed, view=view)
                log.info("ChatJerry: updated hub message %s", existing_id_raw)
                return
            except Exception:
                log.warning("ChatJerry: could not edit hub message, recreating")

        try:
            sent = await channel.send(embed=embed, view=view)
            await self._repo.kv_set(guild_id, KV_CHAT_JERRY_HUB_MSG, str(sent.id))
            log.info("ChatJerry: posted hub message %s", sent.id)
            try:
                await sent.pin()
            except discord.Forbidden:
                log.warning("ChatJerry: missing pin permission channel=%s", CHAT_WITH_JERRY_CHANNEL_ID)
        except Exception:
            log.exception("ChatJerry: failed to post hub")

    async def publish_daily_question(self, guild_id: int, *, force: bool = False) -> None:
        today = _today_key()
        if not force:
            previous = await self._repo.kv_get(guild_id, KV_CHAT_JERRY_DAILY_DATE)
            if previous == today:
                return

        channel = self._bot.get_channel(CHAT_WITH_JERRY_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self._bot.fetch_channel(CHAT_WITH_JERRY_CHANNEL_ID)
            except Exception:
                log.warning("ChatJerry: could not fetch daily question channel")
                return
        if not isinstance(channel, discord.TextChannel):
            return

        prompt = _pick_question(sum(ord(ch) for ch in today))
        try:
            await channel.send(embed=build_prompt_embed(prompt, title="Today's small speaking question"), view=ChatPromptView(prompt))
            await self._repo.kv_set(guild_id, KV_CHAT_JERRY_DAILY_DATE, today)
            log.info("ChatJerry: posted daily question for %s", today)
        except Exception:
            log.exception("ChatJerry: failed to post daily question")


class ChatJerryCog(commands.Cog):
    def __init__(self, bot: commands.Bot, repo: Any, publisher: ChatJerryPublisher) -> None:
        self.bot = bot
        self.repo = repo
        self.publisher = publisher
        self._last_reply_at: dict[int, float] = {}

    async def handle_message(self, message: discord.Message) -> None:
        if message.author.bot or message.channel.id != CHAT_WITH_JERRY_CHANNEL_ID:
            return
        text = (message.content or "").strip()
        if not text or text.startswith("/"):
            return

        now = time.time()
        last = self._last_reply_at.get(message.author.id, 0.0)
        if now - last < 8:
            return
        self._last_reply_at[message.author.id] = now

        try:
            if message.guild:
                await self.repo.command_usage_record(message.guild.id, message.author.id, "chatjerry_message", int(now))
        except Exception:
            log.exception("ChatJerry: failed to record message usage")

        embed = _reply_embed_for_text(text, message.author.display_name)
        try:
            await message.reply(embed=embed, view=ChatReplyView(original_text=text), mention_author=False)
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
        await interaction.response.send_message(embed=build_prompt_embed(prompt), view=ChatPromptView(prompt))


async def setup(bot: commands.Bot, repo: Any, *, guild_id: int) -> ChatJerryPublisher:
    publisher = ChatJerryPublisher(bot=bot, repo=repo)
    await bot.add_cog(ChatJerryCog(bot, repo, publisher))
    bot.add_view(ChatJerryHubView(publisher=None))
    log.info("ChatJerryCog loaded.")
    return publisher
