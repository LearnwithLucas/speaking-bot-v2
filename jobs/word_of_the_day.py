from __future__ import annotations

# jobs/word_of_the_day.py
import logging
import random
import datetime as dt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import aiohttp
import discord
from discord.ext import tasks

from db.repo import Repo

log = logging.getLogger("jobs.word_of_the_day")

TZ_NAME = "Europe/Amsterdam"
POST_HOUR = 9
POST_MINUTE = 0

EN_WOTD_CHANNEL_ID = 1484164091202240652   # 🔤┃word-of-the-day
NL_WOTD_CHANNEL_ID = 1484164145610752151   # 🔤┃woord-van-de-dag

KV_EN_WOTD_DATE = "wotd_en_last_date"
KV_NL_WOTD_DATE = "wotd_nl_last_date"

DICT_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

# =====================
# WORD LIST
# Word pairs: (english, dutch_translation, dutch_example_sentence)
# B1/B2 level — practical, conversational, useful for speaking
# =====================

WORD_LIST: list[tuple[str, str, str]] = [
    ("acknowledge", "erkennen", "Hij erkende dat hij een fout had gemaakt."),
    ("adjust", "aanpassen", "Ze paste haar schema aan om eerder te beginnen."),
    ("assume", "aannemen", "Ik nam aan dat de vergadering om negen uur begon."),
    ("boundary", "grens", "Het is belangrijk om grenzen te stellen in relaties."),
    ("brief", "kort", "Ze gaf een korte uitleg van het plan."),
    ("capable", "in staat", "Ze is in staat om het probleem zelf op te lossen."),
    ("challenge", "uitdaging", "Nieuwe dingen leren is soms een uitdaging."),
    ("commit", "zich verbinden", "Hij verbond zich aan het project voor zes maanden."),
    ("confident", "zelfverzekerd", "Ze sprak zelfverzekerd voor de groep."),
    ("consequence", "gevolg", "Elke keuze heeft een gevolg."),
    ("consistent", "consequent", "Wees consequent in je oefeningen."),
    ("context", "context", "Zonder context is de zin moeilijk te begrijpen."),
    ("contribute", "bijdragen", "Iedereen droeg iets bij aan het gesprek."),
    ("convince", "overtuigen", "Het kostte moeite om hem te overtuigen."),
    ("cope", "omgaan met", "Ze leerde omgaan met stress op het werk."),
    ("criticism", "kritiek", "Constructieve kritiek helpt je groeien."),
    ("curious", "nieuwsgierig", "Hij was nieuwsgierig naar haar achtergrond."),
    ("deadline", "deadline", "De deadline voor het project is vrijdag."),
    ("decision", "beslissing", "Het was een moeilijke beslissing om te nemen."),
    ("dedicated", "toegewijd", "Ze is toegewijd aan haar studie."),
    ("depend", "afhangen van", "Of we gaan hangt af van het weer."),
    ("determine", "bepalen", "De uitkomst wordt bepaald door je inspanning."),
    ("disappointment", "teleurstelling", "Het was een teleurstelling dat de reis werd geannuleerd."),
    ("distraction", "afleiding", "Zijn telefoon was een grote afleiding."),
    ("effort", "inspanning", "Je merkt de inspanning die ze erin steekt."),
    ("embarrassed", "verlegen", "Ze voelde zich verlegen toen ze de verkeerde naam zei."),
    ("encourage", "aanmoedigen", "Hij moedigde haar aan om door te gaan."),
    ("engage", "betrekken", "Het was moeilijk om iedereen bij het gesprek te betrekken."),
    ("exhausted", "uitgeput", "Na het lange gesprek was hij uitgeput."),
    ("expectation", "verwachting", "De verwachtingen waren hoog maar realistisch."),
    ("experience", "ervaring", "Ze had veel ervaring in het werken met kinderen."),
    ("express", "uitdrukken", "Het is moeilijk om gevoelens in een andere taal uit te drukken."),
    ("failure", "mislukking", "Een mislukking is een kans om te leren."),
    ("familiar", "vertrouwd", "De situatie voelde vertrouwd voor haar."),
    ("flexible", "flexibel", "Hij is flexibel als het gaat om werktijden."),
    ("focus", "richten op", "Ze richtte zich op de positieve kanten."),
    ("frustrated", "gefrustreerd", "Hij raakte gefrustreerd door de miscommunicatie."),
    ("genuine", "oprecht", "Haar interesse in zijn verhaal was oprecht."),
    ("grateful", "dankbaar", "Ze was dankbaar voor de hulp die ze kreeg."),
    ("hesitate", "aarzelen", "Hij aarzelde voordat hij antwoord gaf."),
    ("honest", "eerlijk", "Ze was eerlijk over haar twijfels."),
    ("ignore", "negeren", "Hij negeerde de afleiding en bleef gefocust."),
    ("impact", "impact", "Haar woorden hadden een grote impact op hem."),
    ("impatient", "ongeduldig", "Ze werd ongeduldig toen het gesprek te lang duurde."),
    ("improve", "verbeteren", "Elke oefening helpt je te verbeteren."),
    ("influence", "invloed", "Muziek heeft veel invloed op hoe je je voelt."),
    ("interrupt", "onderbreken", "Hij onderbrak haar midden in haar zin."),
    ("involve", "betrekken", "Ze wilde iedereen betrekken bij de beslissing."),
    ("isolated", "geïsoleerd", "Hij voelde zich geïsoleerd in de nieuwe stad."),
    ("manage", "omgaan met", "Ze wist goed om te gaan met de druk."),
    ("mention", "noemen", "Hij noemde het probleem maar ging er niet verder op in."),
    ("motivated", "gemotiveerd", "Ze was gemotiveerd om elke dag te oefenen."),
    ("nervous", "zenuwachtig", "Hij was zenuwachtig voor zijn eerste gesprek."),
    ("observe", "waarnemen", "Ze nam de situatie rustig waar voordat ze sprak."),
    ("overcome", "overwinnen", "Hij overwon zijn angst om te spreken in het openbaar."),
    ("patience", "geduld", "Geduld is een van de belangrijkste eigenschappen bij het leren."),
    ("perspective", "perspectief", "Vanuit een ander perspectief ziet het er anders uit."),
    ("polite", "beleefd", "Ze was altijd beleefd, zelfs als ze het er niet mee eens was."),
    ("prepare", "voorbereiden", "Hij bereidde zich voor op de moeilijke vragen."),
    ("progress", "vooruitgang", "Ze zag duidelijk haar vooruitgang na een maand oefenen."),
    ("react", "reageren", "Ze reageerde kalm op het onverwachte nieuws."),
    ("realistic", "realistisch", "Stel realistische doelen voor jezelf."),
    ("recognize", "herkennen", "Hij herkende het patroon in zijn fouten."),
    ("reflect", "nadenken over", "Ze nam de tijd om na te denken over het gesprek."),
    ("relationship", "relatie", "Een goede relatie is gebaseerd op vertrouwen."),
    ("relevant", "relevant", "Zorg ervoor dat je woordenschat relevant is voor de situatie."),
    ("reluctant", "terughoudend", "Ze was terughoudend om het onderwerp aan te snijden."),
    ("responsible", "verantwoordelijk", "Hij nam verantwoordelijkheid voor zijn fout."),
    ("routine", "routine", "Een dagelijkse routine helpt je consistent te blijven."),
    ("sensitive", "gevoelig", "Ze was gevoelig voor de manier waarop hij de vraag stelde."),
    ("situation", "situatie", "In deze situatie is het beter om rustig te blijven."),
    ("skill", "vaardigheid", "Spreken is een vaardigheid die je kunt oefenen."),
    ("solution", "oplossing", "Ze zocht een praktische oplossing voor het probleem."),
    ("straightforward", "rechttoe rechtaan", "Zijn antwoord was rechttoe rechtaan en duidelijk."),
    ("struggle", "moeite hebben", "Ze had moeite met het vinden van de juiste woorden."),
    ("support", "steun", "De steun van haar vrienden hielp haar door de moeilijke tijd."),
    ("surprised", "verrast", "Hij was verrast door de positieve reactie."),
    ("tendency", "neiging", "Ze had de neiging om te snel te praten als ze nerveus was."),
    ("trust", "vertrouwen", "Vertrouwen opbouwen kost tijd."),
    ("uncomfortable", "ongemakkelijk", "Hij voelde zich ongemakkelijk bij het onderwerp."),
    ("unexpected", "onverwacht", "Het was een onverwachte vraag maar ze antwoordde goed."),
    ("unique", "uniek", "Elke leerder heeft een unieke manier van leren."),
    ("valuable", "waardevol", "Elke oefensessie is waardevol, hoe kort ook."),
    ("willing", "bereid", "Ze was bereid om fouten te maken om te leren."),
    ("withdraw", "zich terugtrekken", "Als hij nerveus was, trok hij zich terug uit het gesprek."),
    ("wonder", "zich afvragen", "Ze vroeg zich af hoe ze het gesprek moest beginnen."),
    ("worthwhile", "de moeite waard", "Elke inspanning die je levert is de moeite waard."),
]


def _get_tz() -> ZoneInfo | None:
    try:
        return ZoneInfo(TZ_NAME)
    except ZoneInfoNotFoundError:
        log.warning("Timezone '%s' not available. Falling back to UTC.", TZ_NAME)
        return None


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
        log.exception("WOTD: API request failed for word=%s", word)
        return None


def _pick_word(date_str: str) -> tuple[str, str, str]:
    """Pick a word deterministically by date so EN and NL get the same word."""
    idx = hash(date_str) % len(WORD_LIST)
    return WORD_LIST[idx]


def build_en_embed(word: str, data: dict | None, date_str: str) -> discord.Embed:
    embed = discord.Embed(title=f"Word of the day: {word.lower()}")

    if data:
        phonetic = next(
            (p["text"] for p in data.get("phonetics", []) if p.get("text")), ""
        )
        if phonetic:
            embed.description = phonetic

        meanings = data.get("meanings", [])
        shown = 0
        for meaning in meanings:
            if shown >= 2:
                break
            part = meaning.get("partOfSpeech", "")
            defs = meaning.get("definitions", [])
            if not defs:
                continue
            d = defs[0]
            definition = d.get("definition", "")
            example = d.get("example", "")
            synonyms = meaning.get("synonyms", [])[:3]

            value = definition
            if example:
                value += f"\n*\"{example}\"*"
            if synonyms:
                value += f"\nSimilar: {', '.join(synonyms)}"

            embed.add_field(name=part, value=value, inline=False)
            shown += 1
    else:
        embed.description = "No definition found for this word."

    embed.add_field(
        name="Try it",
        value="Use this word in a sentence in the chat.",
        inline=False,
    )
    embed.set_footer(text=f"{date_str} | dictionaryapi.dev")
    return embed


def build_nl_embed(
    word: str,
    translation: str,
    example: str,
    data: dict | None,
    date_str: str,
) -> discord.Embed:
    embed = discord.Embed(title=f"Woord van de dag: {word.lower()}")

    definition_en = ""
    if data:
        meanings = data.get("meanings", [])
        for meaning in meanings:
            defs = meaning.get("definitions", [])
            if defs:
                definition_en = defs[0].get("definition", "")
                break

    description = f"**Nederlands:** {translation}"
    if definition_en:
        description += f"\n**Engels:** {definition_en}"
    embed.description = description

    embed.add_field(
        name="Voorbeeldzin",
        value=f"*{example}*",
        inline=False,
    )
    embed.add_field(
        name="Probeer het",
        value="Gebruik dit woord in een zin in de chat.",
        inline=False,
    )
    embed.set_footer(text=f"{date_str} | dictionaryapi.dev")
    return embed


class WordOfTheDayJob:
    def __init__(
        self,
        *,
        bot: discord.Client,
        repo: Repo,
        guild_id: int,
        dutch_guild_id: int | None = None,
    ) -> None:
        self._bot = bot
        self._repo = repo
        self._guild_id = guild_id
        self._dutch_guild_id = dutch_guild_id
        self._tz = _get_tz()
        self._tick.start()

    def _now(self) -> dt.datetime:
        return dt.datetime.now(tz=self._tz or ZoneInfo("UTC"))

    async def _get_channel(self, channel_id: int) -> discord.TextChannel | None:
        ch = self._bot.get_channel(channel_id)
        if isinstance(ch, discord.TextChannel):
            return ch
        try:
            fetched = await self._bot.fetch_channel(channel_id)
            if isinstance(fetched, discord.TextChannel):
                return fetched
        except Exception:
            pass
        log.warning("WOTD: could not fetch channel %s", channel_id)
        return None

    @tasks.loop(minutes=1)
    async def _tick(self) -> None:
        now = self._now()
        if not (now.hour == POST_HOUR and now.minute == POST_MINUTE):
            return

        date_str = now.date().isoformat()

        # English
        last_en = await self._repo.kv_get(self._guild_id, KV_EN_WOTD_DATE)
        if last_en != date_str:
            await self._post_english(date_str)
            await self._repo.kv_set(self._guild_id, KV_EN_WOTD_DATE, date_str)

        # Dutch
        if self._dutch_guild_id:
            last_nl = await self._repo.kv_get(self._dutch_guild_id, KV_NL_WOTD_DATE)
            if last_nl != date_str:
                await self._post_dutch(date_str)
                await self._repo.kv_set(self._dutch_guild_id, KV_NL_WOTD_DATE, date_str)

    @_tick.before_loop
    async def _before(self) -> None:
        await self._bot.wait_until_ready()

    async def _post_english(self, date_str: str) -> None:
        word, translation, nl_example = _pick_word(date_str)
        data = await fetch_definition(word)
        embed = build_en_embed(word, data, date_str)

        ch = await self._get_channel(EN_WOTD_CHANNEL_ID)
        if not ch:
            return
        try:
            await ch.send(embed=embed)
            log.info("WOTD: posted English word '%s' for %s", word, date_str)
        except Exception:
            log.exception("WOTD: failed to post English word")

    async def _post_dutch(self, date_str: str) -> None:
        word, translation, nl_example = _pick_word(date_str)
        data = await fetch_definition(word)
        embed = build_nl_embed(word, translation, nl_example, data, date_str)

        ch = await self._get_channel(NL_WOTD_CHANNEL_ID)
        if not ch:
            return
        try:
            await ch.send(embed=embed)
            log.info("WOTD: posted Dutch word '%s' for %s", word, date_str)
        except Exception:
            log.exception("WOTD: failed to post Dutch word")
