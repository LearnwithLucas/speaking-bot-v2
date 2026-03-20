from __future__ import annotations

# commands/dictionary.py
import logging
import aiohttp

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("commands.dictionary")

EN_VOCAB_CHANNEL_ID = 1484159272299401337   # 🔤┃vocabulary
NL_VOCAB_CHANNEL_ID = 1484159374187434014   # 🔤┃woordenboek

DICT_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
NL_FALLBACK_URL = "https://www.woorden.org/woord/{word}"

KV_EN_VOCAB_MSG = "vocab_channel_en_message_id"
KV_NL_VOCAB_MSG = "vocab_channel_nl_message_id_v2"


# =====================
# API CALL
# =====================

async def fetch_definition(word: str) -> dict | None:
    url = DICT_API_URL.format(word=word.strip().lower())
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and data:
                        return data[0]
                return None
    except Exception:
        log.exception("Dictionary API request failed for word=%s", word)
        return None


def build_result_embed(word: str, data: dict) -> discord.Embed:
    phonetic = ""
    for p in data.get("phonetics", []):
        if p.get("text"):
            phonetic = p["text"]
            break

    title = word.lower()
    if phonetic:
        title += f"  {phonetic}"

    embed = discord.Embed(title=title)

    meanings = data.get("meanings", [])
    shown = 0

    for meaning in meanings:
        if shown >= 3:
            break

        part = meaning.get("partOfSpeech", "")
        defs = meaning.get("definitions", [])
        if not defs:
            continue

        d = defs[0]
        definition = d.get("definition", "")
        example = d.get("example", "")
        synonyms = meaning.get("synonyms", [])[:4]

        value = definition
        if example:
            value += f"\n*\"{example}\"*"
        if synonyms:
            value += f"\nSimilar: {', '.join(synonyms)}"

        embed.add_field(
            name=part,
            value=value,
            inline=False,
        )
        shown += 1

    source = data.get("sourceUrls", [""])[0]
    if source:
        embed.set_footer(text=f"dictionaryapi.dev")
    else:
        embed.set_footer(text="dictionaryapi.dev")

    return embed


def build_not_found_embed(word: str) -> discord.Embed:
    embed = discord.Embed(
        title=f'No result for "{word}"',
        description=(
            f"This word wasn't found in the dictionary.\n\n"
            f"Check the spelling and try again, or search online: "
            f"[Merriam-Webster](https://www.merriam-webster.com/dictionary/{word})"
        ),
    )
    return embed


def build_nl_embed(word: str) -> discord.Embed:
    url = NL_FALLBACK_URL.format(word=word.strip().lower())
    embed = discord.Embed(
        title=f"{word.lower()}",
        description=(
            f"Dutch dictionary lookup is not available via API yet.\n\n"
            f"[Open in woorden.org]({url})\n"
            f"[Open in Van Dale](https://www.vandale.nl/gratis-woordenboek/nederlands/betekenis/{word.strip().lower()})"
        ),
    )
    embed.set_footer(text="woorden.org / Van Dale")
    return embed


# =====================
# CHANNEL EXPLANATION EMBEDS
# =====================

def build_en_channel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🔤 Vocabulary lookup",
        description=(
            "Use `/d` followed by any English word to look it up right here.\n\n"
            "**What you get:**\n"
            "The definition, the part of speech, a usage example, and similar words.\n\n"
            "**How to use it:**\n"
            "`/d word: curious`\n"
            "`/d word: resilient`\n"
            "`/d word: figure out`\n\n"
            "Works anywhere in the server. Results post here so everyone can see them.\n\n"
            "Looking for conversation topics? Try `/topics`."
        ),
    )
    embed.set_footer(text="vocabulary:en:v1")
    return embed


def build_nl_channel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🔤 Woorden opzoeken",
        description=(
            "Gebruik `/d word: [woord]` overal in de server om een woord op te zoeken.\n\n"
            "**Wat je krijgt:**\n"
            "De bot zoekt eerst in het Engels woordenboek. Als het woord daar niet in staat, "
            "krijg je directe links naar woorden.org en Van Dale.\n\n"
            "**Hoe gebruik je het:**\n"
            "`/d word: nieuwsgierig`\n"
            "`/d word: zelfvertrouwen`\n"
            "`/d word: curious`\n\n"
            "Werkt overal in de server. Resultaten worden hier gepost zodat iedereen ze kan zien.\n\n"
            "Op zoek naar gespreksonderwerpen? Probeer `/onderwerpen`."
        ),
    )
    embed.set_footer(text="vocabulary:nl:v2")
    return embed


# =====================
# PUBLISHER
# =====================

class VocabPublisher:
    def __init__(self, *, bot: discord.Client, repo) -> None:
        self._bot = bot
        self._repo = repo

    async def publish_english(self) -> None:
        await self._publish(
            channel_id=EN_VOCAB_CHANNEL_ID,
            embed=build_en_channel_embed(),
            kv_key=KV_EN_VOCAB_MSG,
        )

    async def publish_dutch(self) -> None:
        await self._publish(
            channel_id=NL_VOCAB_CHANNEL_ID,
            embed=build_nl_channel_embed(),
            kv_key=KV_NL_VOCAB_MSG,
        )

    async def _publish(self, *, channel_id: int, embed: discord.Embed, kv_key: str) -> None:
        channel = self._bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self._bot.fetch_channel(channel_id)
            except Exception:
                log.warning("VocabPublisher: could not fetch channel %s", channel_id)
                return

        if not isinstance(channel, discord.TextChannel):
            return

        existing_id_raw = await self._repo.kv_get(channel.guild.id, kv_key)
        if existing_id_raw:
            try:
                msg = await channel.fetch_message(int(existing_id_raw))
                await msg.edit(embed=embed)
                log.info("VocabPublisher: updated message in channel %s", channel_id)
                return
            except Exception:
                log.warning("VocabPublisher: could not edit, recreating in channel %s", channel_id)

        try:
            sent = await channel.send(embed=embed)
            await self._repo.kv_set(channel.guild.id, kv_key, str(sent.id))
            log.info("VocabPublisher: posted message %s in channel %s", sent.id, channel_id)
            try:
                await sent.pin()
            except discord.Forbidden:
                log.warning("VocabPublisher: missing pin permission in channel %s", channel_id)
            except Exception:
                log.warning("VocabPublisher: could not pin in channel %s", channel_id)
        except Exception:
            log.exception("VocabPublisher: failed to post in channel %s", channel_id)


# =====================
# COG
# =====================

class DictionaryCog(commands.Cog):
    def __init__(self, bot: commands.Bot, repo) -> None:
        self.bot = bot
        self.repo = repo

    @app_commands.command(
        name="d",
        description="Look up an English word: definition, example, and synonyms.",
    )
    @app_commands.describe(word="The word you want to look up")
    async def d(self, interaction: discord.Interaction, word: str) -> None:
        await interaction.response.defer()

        guild = interaction.guild
        is_nl = (
            guild is not None
            and hasattr(self.bot, "dutch_guild_id")
            and getattr(self.bot, "dutch_guild_id", None) == guild.id
        )

        data = await fetch_definition(word)

        if data:
            embed = build_result_embed(word, data)
        elif is_nl:
            # API had no result — fall back to Dutch dictionary links
            embed = build_nl_embed(word)
        else:
            embed = build_not_found_embed(word)

        vocab_channel_id = NL_VOCAB_CHANNEL_ID if is_nl else EN_VOCAB_CHANNEL_ID

        if interaction.channel_id == vocab_channel_id:
            await interaction.followup.send(embed=embed)
        else:
            vocab_mention = f"<#{vocab_channel_id}>"
            await interaction.followup.send(
                embed=embed,
                content=f"Result posted. You can also use `/d` directly in {vocab_mention}.",
            )


async def setup(bot: commands.Bot, repo, *, guild_id: int, dutch_guild_id: int | None = None) -> None:
    cog = DictionaryCog(bot, repo)
    await bot.add_cog(cog)

    # Always set dutch_guild_id on bot for guild detection in commands
    if dutch_guild_id:
        bot.dutch_guild_id = dutch_guild_id  # type: ignore[attr-defined]

    log.info("DictionaryCog loaded.")