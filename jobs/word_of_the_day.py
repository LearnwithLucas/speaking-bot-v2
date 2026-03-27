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
KV_NL_WOTD_DATE = "wotd_nl_last_date_v2"

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
    embed.set_footer(text=date_str)
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

    async def post_nl_now(self) -> None:
        """Post today's Dutch word immediately, regardless of time. Used by /woordvandedag."""
        now = self._now()
        date_str = now.date().isoformat()
        await self._post_dutch(date_str)
        log.info("WOTD: manual NL post triggered for %s", date_str)

    async def post_en_now(self) -> None:
        """Post today's English word immediately, regardless of time. Used by /wordoftheday."""
        now = self._now()
        date_str = now.date().isoformat()
        await self._post_english(date_str)
        log.info("WOTD: manual EN post triggered for %s", date_str)

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
        entry = _pick_nl_word(date_str)
        embed = build_nl_embed_v2(entry, date_str)

        ch = await self._get_channel(NL_WOTD_CHANNEL_ID)
        if not ch:
            return
        try:
            await ch.send(embed=embed)
            log.info("WOTD: posted Dutch word '%s' for %s", entry[0], date_str)
        except Exception:
            log.exception("WOTD: failed to post Dutch word")


# =======================================================
# DUTCH WORD LIST
# 200 entries: (dutch_word, part_of_speech, dutch_definition, english_translation, example_sentence)
# B1/B2 level — practical, conversational, useful for speaking
# =======================================================

NL_WORD_LIST: list[tuple[str, str, str, str, str]] = [
    # A
    ("aanpassen", "werkwoord", "iets veranderen zodat het beter past bij een situatie", "to adjust / to adapt", "Ze paste haar schema aan om eerder te beginnen."),
    ("aarzelen", "werkwoord", "even wachten voordat je iets doet of zegt, omdat je niet zeker bent", "to hesitate", "Hij aarzelde voordat hij antwoord gaf."),
    ("afhangen", "werkwoord", "bepaald worden door iets anders — 'het hangt af van...'", "to depend on", "Of we gaan hangt af van het weer."),
    ("afleiding", "zelfstandig naamwoord", "iets wat je aandacht wegtrekt van wat je eigenlijk doet", "distraction", "Zijn telefoon was een grote afleiding tijdens de les."),
    ("afsluiten", "werkwoord", "iets beëindigen of afsluiten, zoals een gesprek of een rekening", "to close / to conclude", "Ze sloot het gesprek af met een duidelijke conclusie."),
    ("aanmoedigen", "werkwoord", "iemand motiveren om iets te blijven doen", "to encourage", "Hij moedigde haar aan om door te gaan met haar studie."),
    ("afspreken", "werkwoord", "met iemand een tijd en plaats bepalen om elkaar te ontmoeten", "to arrange / to agree", "Ze spraken af om op vrijdag samen te oefenen."),
    ("antwoorden", "werkwoord", "reageren op een vraag of opmerking", "to answer / to reply", "Ze antwoordde rustig op de moeilijke vraag."),
    ("aandacht", "zelfstandig naamwoord", "de focus die je geeft aan iets of iemand", "attention", "Ze gaf al haar aandacht aan de spreker."),
    ("aanpakken", "werkwoord", "een probleem of taak actief aanvatten en oplossen", "to tackle / to address", "Hij pakte het probleem direct aan."),

    # B
    ("bedoelen", "werkwoord", "willen zeggen — wat je bedoelt is je eigenlijke bedoeling", "to mean", "Wat bedoel je precies met dat woord?"),
    ("begrijpen", "werkwoord", "de betekenis of inhoud van iets snappen", "to understand", "Ze begreep de uitleg pas na het tweede voorbeeld."),
    ("behoefte", "zelfstandig naamwoord", "iets wat je nodig hebt of sterk wilt", "need", "Hij had behoefte aan rust na de lange dag."),
    ("beleefd", "bijvoeglijk naamwoord", "vriendelijk en respectvol in omgang met anderen", "polite", "Ze was altijd beleefd, ook als ze het er niet mee eens was."),
    ("beperken", "werkwoord", "iets kleiner of minder maken, grenzen stellen", "to limit / to restrict", "Ze probeerde haar schermtijd te beperken."),
    ("bereiken", "werkwoord", "een doel halen of op een plek aankomen", "to reach / to achieve", "Na maanden oefenen bereikten ze hun doel."),
    ("beslissen", "werkwoord", "een keuze maken na het overwegen van opties", "to decide", "Ze besliste om een privéles te boeken."),
    ("bevestigen", "werkwoord", "laten weten dat iets klopt of dat je aanwezig zult zijn", "to confirm", "Hij bevestigde de afspraak via e-mail."),
    ("bewijs", "zelfstandig naamwoord", "iets wat laat zien dat iets waar is", "proof / evidence", "Er was geen bewijs dat hij de fout had gemaakt."),
    ("bijdragen", "werkwoord", "iets toevoegen aan een gesprek, project of groep", "to contribute", "Iedereen droeg iets bij aan de discussie."),

    # C
    ("consistent", "bijvoeglijk naamwoord", "steeds hetzelfde doen zonder grote veranderingen", "consistent", "Wees consistent in je dagelijkse oefeningen."),
    ("context", "zelfstandig naamwoord", "de situatie of omgeving die iets helpt te begrijpen", "context", "Zonder context is de zin moeilijk te begrijpen."),

    # D
    ("dankbaar", "bijvoeglijk naamwoord", "blij zijn met wat je hebt ontvangen en dat laten merken", "grateful", "Ze was dankbaar voor de hulp die ze had gekregen."),
    ("doel", "zelfstandig naamwoord", "iets wat je wilt bereiken", "goal / aim", "Haar doel was om vloeiend Nederlands te spreken."),
    ("doorzetten", "werkwoord", "blijven proberen ook als het moeilijk is", "to persevere / to keep going", "Hij zette door, ook als hij fouten maakte."),
    ("duidelijk", "bijvoeglijk naamwoord", "makkelijk te begrijpen, niet verwarrend", "clear", "Haar uitleg was duidelijk en goed gestructureerd."),
    ("duur", "bijvoeglijk naamwoord", "veel geld kost", "expensive", "De privéles was duur maar erg nuttig."),
    ("druk", "bijvoeglijk naamwoord", "veel te doen hebben, weinig tijd", "busy / pressured", "Ze had een drukke week maar oefende toch elke dag."),

    # E
    ("eerlijk", "bijvoeglijk naamwoord", "de waarheid zeggen en rechtvaardig zijn", "honest / fair", "Ze was eerlijk over haar twijfels."),
    ("eenvoudig", "bijvoeglijk naamwoord", "niet moeilijk, makkelijk te doen of te begrijpen", "simple / easy", "Begin met eenvoudige zinnen en bouw dat langzaam op."),
    ("ervaring", "zelfstandig naamwoord", "kennis of vaardigheid die je opdoet door iets te doen", "experience", "Ze had veel ervaring in het werken met kinderen."),
    ("erkennen", "werkwoord", "toegeven dat iets waar is of dat iemand gelijk heeft", "to acknowledge / to admit", "Hij erkende dat hij een fout had gemaakt."),
    ("even", "bijwoord", "een korte tijd, of als verzachting van een verzoek", "just / a moment", "Wacht even, ik denk na."),

    # F
    ("fout", "zelfstandig naamwoord", "een vergissing, iets wat niet klopt", "mistake / error", "Elke fout is een kans om iets te leren."),
    ("flexibel", "bijvoeglijk naamwoord", "makkelijk aanpassen aan nieuwe situaties", "flexible", "Hij is flexibel als het gaat om werktijden."),
    ("frustratie", "zelfstandig naamwoord", "het gevoel als iets niet lukt zoals je wilt", "frustration", "De frustratie nam toe toen ze hetzelfde patroon bleef herhalen."),

    # G
    ("geduld", "zelfstandig naamwoord", "rustig kunnen wachten zonder boos of ongeduldig te worden", "patience", "Geduld is een van de belangrijkste eigenschappen bij het leren."),
    ("gewoonte", "zelfstandig naamwoord", "iets wat je regelmatig doet zonder er veel bij na te denken", "habit", "Dagelijks oefenen werd een gewoonte."),
    ("gewend", "bijvoeglijk naamwoord", "iets als normaal ervaren omdat je het veel gedaan hebt", "used to / accustomed", "Ze was gewend aan de snelle spreektaal van Nederlanders."),
    ("gezellig", "bijvoeglijk naamwoord", "aangenaam samen zijn, een warme sfeer", "cozy / sociable / nice", "De sessie was gezellig en iedereen deed mee."),
    ("grens", "zelfstandig naamwoord", "de limiet van wat je accepteert of kunt", "boundary / limit", "Het is belangrijk om grenzen te stellen."),
    ("gevolg", "zelfstandig naamwoord", "wat er gebeurt als resultaat van iets anders", "consequence / result", "Elke keuze heeft een gevolg."),

    # H
    ("herkennen", "werkwoord", "iets of iemand kennen van eerder, of een patroon zien", "to recognize", "Hij herkende het patroon in zijn eigen fouten."),
    ("herhalen", "werkwoord", "iets nog een keer zeggen of doen", "to repeat / to review", "Ze herhaalde de nieuwe woorden elke avond."),
    ("helpen", "werkwoord", "iemand ondersteunen bij iets", "to help", "Hij hielp haar met het voorbereiden van het gesprek."),
    ("hoofd", "zelfstandig naamwoord", "het deel van je lichaam boven je nek, of de leider van een groep", "head", "In haar hoofd wist ze het antwoord, maar ze kon het niet zeggen."),
    ("horen", "werkwoord", "geluid waarnemen met je oren", "to hear", "Ze hoorde hem maar begreep niet alles."),

    # I
    ("inspanning", "zelfstandig naamwoord", "energie en moeite die je ergens in stopt", "effort", "Je merkt de inspanning die ze in haar studie steekt."),
    ("invloed", "zelfstandig naamwoord", "de kracht om iets of iemand te veranderen", "influence", "Muziek heeft veel invloed op hoe je je voelt."),

    # K
    ("kiezen", "werkwoord", "een beslissing nemen uit verschillende opties", "to choose", "Ze koos voor de maandag sessie omdat die beter paste."),
    ("klagen", "werkwoord", "zeggen dat je ergens ontevreden over bent", "to complain", "Hij klaagde niet, maar zocht meteen naar een oplossing."),
    ("contact", "zelfstandig naamwoord", "verbinding met iemand, persoonlijk of via communicatie", "contact", "Ze hielden contact via een WhatsApp-groep."),
    ("kritiek", "zelfstandig naamwoord", "een oordeel over iets, vaak om te verbeteren", "criticism / critique", "Constructieve kritiek helpt je groeien."),

    # L
    ("leren", "werkwoord", "kennis of vaardigheden opdoen door studie of ervaring", "to learn", "Ze leerde elke dag een nieuw woord."),
    ("luisteren", "werkwoord", "actief aandacht geven aan wat iemand zegt", "to listen", "Goed luisteren is de basis van een goed gesprek."),
    ("lastig", "bijvoeglijk naamwoord", "moeilijk of vervelend", "difficult / tricky", "Het was lastig om de juiste woorden te vinden."),

    # M
    ("missen", "werkwoord", "iets of iemand niet hebben die je wilt, of iemand erg missen", "to miss / to lack", "Ze miste de kans om te spreken tijdens de sessie."),
    ("moeite", "zelfstandig naamwoord", "inspanning die nodig is, of iets wat moeilijk gaat", "effort / difficulty", "Ze had moeite met de uitspraak van lange woorden."),
    ("motivatie", "zelfstandig naamwoord", "de reden of het gevoel dat je aanzet om iets te doen", "motivation", "Haar motivatie om Nederlands te leren was haar werk."),
    ("mogelijk", "bijvoeglijk naamwoord", "dat kan of mag gebeuren", "possible", "Het is mogelijk om in een jaar vloeiend te worden."),

    # N
    ("nadenken", "werkwoord", "rustig je gedachten ordenen over een onderwerp", "to think / to reflect", "Ze nam de tijd om na te denken over de vraag."),
    ("nodig", "bijvoeglijk naamwoord", "iets wat je moet hebben of doen", "necessary / needed", "Oefening is nodig om een taal te leren."),
    ("neiging", "zelfstandig naamwoord", "de tendens om op een bepaalde manier te reageren", "tendency", "Ze had de neiging om te snel te praten als ze nerveus was."),

    # O
    ("omgaan", "werkwoord", "met iets of iemand in een bepaalde manier handelen", "to deal with / to handle", "Ze leerde omgaan met de stress van spreken in groepen."),
    ("ongemakkelijk", "bijvoeglijk naamwoord", "niet op je gemak, een onaangenaam gevoel", "uncomfortable", "Hij voelde zich ongemakkelijk bij het onderwerp."),
    ("ontspannen", "werkwoord/bijvoeglijk naamwoord", "rustig worden of zijn, spanning loslaten", "to relax / relaxed", "Ze probeerde ontspannen te blijven tijdens het gesprek."),
    ("oprecht", "bijvoeglijk naamwoord", "echt gemeend, niet nep", "sincere / genuine", "Haar interesse in zijn verhaal was oprecht."),
    ("oefenen", "werkwoord", "iets steeds herhalen om beter te worden", "to practice", "Ze oefende elke dag tien minuten Nederlands."),
    ("oplossen", "werkwoord", "een probleem tot een goed einde brengen", "to solve", "Ze zocht een praktische oplossing voor het probleem."),
    ("opvallen", "werkwoord", "opgemerkt worden, uit de groep springen", "to stand out / to notice", "Het viel op dat ze veel beter sprak dan een maand geleden."),
    ("overtuigen", "werkwoord", "iemand laten geloven in jouw idee of mening", "to convince / to persuade", "Het kostte moeite om hem te overtuigen."),
    ("overwinnen", "werkwoord", "een hindernis of angst te boven komen", "to overcome", "Hij overwon zijn angst voor spreken in het openbaar."),

    # P
    ("passen", "werkwoord", "goed zijn voor een situatie of goed zitten", "to fit / to suit", "De maandagsessie paste beter bij haar schema."),
    ("perspectief", "zelfstandig naamwoord", "de manier waarop je iets bekijkt", "perspective", "Vanuit een ander perspectief ziet de situatie er anders uit."),
    ("prettig", "bijvoeglijk naamwoord", "aangenaam, fijn", "pleasant / nice", "De sfeer tijdens de les was prettig en rustig."),
    ("plannen", "werkwoord", "van tevoren bedenken hoe je iets gaat aanpakken", "to plan", "Ze planden hun oefensessies voor de hele week."),
    ("proberen", "werkwoord", "iets doen om te zien of het lukt", "to try", "Hij probeerde de nieuwe zinnen in een gesprek te gebruiken."),

    # R
    ("reageren", "werkwoord", "antwoorden op of handelen naar aanleiding van iets", "to react / to respond", "Ze reageerde kalm op het onverwachte nieuws."),
    ("rekening houden", "werkwoord", "iets meenemen in je overwegingen", "to take into account", "Hij hield rekening met haar niveau bij het geven van uitleg."),
    ("routine", "zelfstandig naamwoord", "een vaste reeks handelingen die je regelmatig doet", "routine", "Een dagelijkse routine helpt je consistent te blijven."),
    ("rustig", "bijvoeglijk naamwoord", "kalm, zonder stress of lawaai", "calm / quiet", "Ze bleef rustig, ook als ze een fout maakte."),

    # S
    ("sfeer", "zelfstandig naamwoord", "de algemene stemming of het gevoel op een plek", "atmosphere / vibe", "De sfeer in de sessie was ontspannen en vriendelijk."),
    ("slagen", "werkwoord", "iets met succes doen, een doel bereiken", "to succeed / to pass", "Ze slaagde voor haar taalexamen na maanden oefenen."),
    ("situatie", "zelfstandig naamwoord", "de omstandigheden op een bepaald moment", "situation", "In deze situatie is het beter om rustig te blijven."),
    ("spreken", "werkwoord", "woorden zeggen, communiceren via taal", "to speak", "Ze sprak voor het eerst Nederlands in een echte situatie."),
    ("steun", "zelfstandig naamwoord", "hulp of aanmoediging van anderen", "support", "De steun van haar groep hielp haar door moeilijke momenten."),
    ("stellen", "werkwoord", "een vraag stellen of een grens stellen", "to ask / to set", "Ze stelde een vraag die niemand anders durfde te stellen."),

    # T
    ("twijfelen", "werkwoord", "niet zeker zijn over iets", "to doubt / to hesitate", "Ze twijfelde of ze de juiste keuze had gemaakt."),
    ("teleurstelling", "zelfstandig naamwoord", "het gevoel als iets niet is zoals je had gehoopt", "disappointment", "Het was een teleurstelling dat de sessie werd geannuleerd."),
    ("terughoudend", "bijvoeglijk naamwoord", "voorzichtig en niet snel iets zeggen of doen", "reserved / reluctant", "Ze was terughoudend om het onderwerp aan te snijden."),
    ("toegewijd", "bijvoeglijk naamwoord", "volledig inzetten voor iets", "dedicated / committed", "Ze is toegewijd aan haar studie en mist nooit een sessie."),
    ("trots", "bijvoeglijk naamwoord", "een goed gevoel over iets wat je zelf of iemand anders heeft bereikt", "proud", "Ze was trots op haar vooruitgang na zes weken."),

    # U
    ("uitdrukken", "werkwoord", "gevoelens of gedachten in woorden overbrengen", "to express", "Het is moeilijk om gevoelens in een andere taal uit te drukken."),
    ("uitdaging", "zelfstandig naamwoord", "iets wat inspanning vraagt maar ook voldoening geeft", "challenge", "Nieuwe talen leren is een uitdaging maar ook heel waardevol."),
    ("uitgeput", "bijvoeglijk naamwoord", "erg moe, geen energie meer hebben", "exhausted", "Na het lange gesprek was hij uitgeput maar tevreden."),
    ("uitlegen", "werkwoord", "iets zo vertellen dat een ander het begrijpt", "to explain", "Ze legde de regel uit met een duidelijk voorbeeld."),

    # V
    ("vaardigheid", "zelfstandig naamwoord", "iets wat je goed kunt doen na oefening", "skill", "Spreken is een vaardigheid die je kunt oefenen."),
    ("verbeteren", "werkwoord", "beter worden of iets beter maken", "to improve", "Elke oefensessie helpt je te verbeteren."),
    ("vergelijken", "werkwoord", "de gelijkenissen en verschillen bekijken tussen twee dingen", "to compare", "Ze vergeleek haar niveau van nu met dat van een maand geleden."),
    ("verlegen", "bijvoeglijk naamwoord", "een ongemakkelijk gevoel in sociale situaties", "shy / embarrassed", "Ze voelde zich verlegen toen ze de verkeerde naam zei."),
    ("vertrouwen", "zelfstandig naamwoord / werkwoord", "geloven dat iemand of iets betrouwbaar is", "trust / to trust", "Vertrouwen opbouwen kost tijd maar is essentieel."),
    ("verwachting", "zelfstandig naamwoord", "wat je denkt dat er gaat gebeuren", "expectation", "De verwachtingen waren hoog maar realistisch."),
    ("vooruitgang", "zelfstandig naamwoord", "de stappen die je maakt richting je doel", "progress", "Ze zag duidelijk haar vooruitgang na een maand oefenen."),
    ("vraag", "zelfstandig naamwoord", "een zin waarmee je informatie vraagt", "question", "Ze stelde een goede vraag over de uitspraak."),

    # W
    ("waardevol", "bijvoeglijk naamwoord", "iets wat belangrijk of nuttig is", "valuable", "Elke oefensessie is waardevol, hoe kort ook."),
    ("waarnemen", "werkwoord", "iets opmerken via je zintuigen of aandacht", "to observe / to notice", "Ze nam de situatie rustig waar voordat ze sprak."),
    ("wennen", "werkwoord", "geleidelijk vertrouwd raken met iets nieuws", "to get used to", "Het duurde even voor ze gewend was aan het tempo van de les."),

    # Z
    ("zelfstandig", "bijvoeglijk naamwoord", "iets zonder hulp kunnen doen", "independent / on your own", "Ze werkte steeds meer zelfstandig aan haar uitspraak."),
    ("zelfvertrouwen", "zelfstandig naamwoord", "geloven in je eigen kunnen", "self-confidence", "Meer oefenen gaf haar meer zelfvertrouwen."),
    ("zenuwachtig", "bijvoeglijk naamwoord", "gespannen gevoel, vaak voor iets wat je spannend vindt", "nervous", "Hij was zenuwachtig voor zijn eerste gesprek in het Nederlands."),
    ("zorgen", "zelfstandig naamwoord (meervoud)", "ongerustheid over iets wat kan gebeuren", "worries / concerns", "Ze had zorgen over haar examen maar bleef oefenen."),

    # Extra practical words
    ("afwisselen", "werkwoord", "afwisseling brengen, steeds iets anders doen", "to alternate / to vary", "Ze wisselde af tussen lezen en spreken om niet te vervelen."),
    ("begeleiding", "zelfstandig naamwoord", "ondersteuning van iemand die je helpt", "guidance / coaching", "Met de juiste begeleiding ging ze snel vooruit."),
    ("beschikbaar", "bijvoeglijk naamwoord", "klaar om gebruikt of bereikt te worden", "available", "Ze was elke vrijdag beschikbaar voor de sessie."),
    ("bewust", "bijvoeglijk naamwoord", "je ergens van bewust zijn, het weten en er aandacht aan geven", "aware / conscious", "Ze was zich bewust van haar neiging om te snel te praten."),
    ("dagelijks", "bijvoeglijk naamwoord / bijwoord", "elke dag, of behorend bij iedere dag", "daily / every day", "Dagelijks oefenen maakt het verschil."),
    ("deelnemen", "werkwoord", "meedoen aan iets", "to participate", "Ze nam deel aan de wekelijkse sessie."),
    ("direct", "bijvoeglijk naamwoord / bijwoord", "zonder omwegen, meteen", "direct / immediately", "Ze gaf een directe maar vriendelijke reactie."),
    ("fijn", "bijvoeglijk naamwoord", "aangenaam, prettig", "nice / fine / pleasant", "Het was fijn om in een kleine groep te oefenen."),
    ("gelukkig", "bijvoeglijk naamwoord / bijwoord", "blij van binnen, of gelukkig dat iets zo is", "happy / fortunately", "Gelukkig had ze genoeg tijd om te oefenen voor de sessie."),
    ("gesprek", "zelfstandig naamwoord", "een uitwisseling van woorden tussen twee of meer mensen", "conversation", "Ze had haar eerste echte gesprek in het Nederlands."),
    ("gewoon", "bijvoeglijk naamwoord / bijwoord", "normaal, of simpelweg", "normal / just / simply", "Ze deed het gewoon, zonder er te lang over na te denken."),
    ("goed", "bijvoeglijk naamwoord", "van hoge kwaliteit of moreel correct", "good", "Ze deed het goed voor haar eerste keer."),
    ("hetzelfde", "voornaamwoord / bijvoeglijk naamwoord", "identiek, geen verschil", "the same", "Ze maakte hetzelfde type fout als de vorige keer."),
    ("inmiddels", "bijwoord", "op dit moment, na verloop van tijd", "by now / in the meantime", "Ze spreekt inmiddels veel vlotter dan zes maanden geleden."),
    ("juist", "bijvoeglijk naamwoord / bijwoord", "correct, of precies", "correct / exactly / precisely", "Ze koos juist dat moment om de vraag te stellen."),
    ("kans", "zelfstandig naamwoord", "een mogelijkheid om iets te doen of te bereiken", "opportunity / chance", "Ze greep elke kans aan om te spreken."),
    ("kennis", "zelfstandig naamwoord", "informatie of begrip van een onderwerp", "knowledge", "Ze bouwde haar kennis van de grammatica stap voor stap op."),
    ("klaar", "bijvoeglijk naamwoord", "af, gereed, of bereid", "ready / done / finished", "Ze was klaar voor haar eerste echte gesprek."),
    ("lang", "bijvoeglijk naamwoord", "grote afstand of grote tijdsduur", "long / tall", "Ze oefende al lang maar durfde nog niet te spreken."),
    ("makkelijk", "bijvoeglijk naamwoord", "niet moeilijk", "easy", "Korte zinnen zijn makkelijker om te beginnen."),
    ("meteen", "bijwoord", "direct, zonder vertraging", "immediately / right away", "Ze begon meteen na de les te oefenen."),
    ("mooi", "bijvoeglijk naamwoord", "visueel aantrekkelijk of aangenaam", "beautiful / nice", "Het was mooi om te zien hoe snel ze vorderde."),
    ("naast", "voorzetsel", "aan de zijde van, of in aanvulling op", "next to / besides", "Naast haar studie deed ze ook een taaldoofcursus."),
    ("net", "bijwoord", "zojuist, of precies", "just / exactly", "Ze had net haar eerste les afgerond."),
    ("nieuwsgierig", "bijvoeglijk naamwoord", "graag willen weten hoe iets zit", "curious", "Hij was nieuwsgierig naar haar achtergrond."),
    ("niveau", "zelfstandig naamwoord", "de graad van bekwaamheid op een bepaald gebied", "level", "Ze oefende op haar eigen niveau zonder zich te vergelijken."),
    ("normaal", "bijvoeglijk naamwoord", "gewoon, zoals het hoort", "normal", "Na een tijdje voelde spreken in groepen normaal."),
    ("nuttig", "bijvoeglijk naamwoord", "dat ergens goed voor is, praktisch van waarde", "useful", "De feedback was nuttig en direct toepasbaar."),
    ("ontmoeten", "werkwoord", "iemand voor het eerst of opnieuw zien", "to meet", "Ze ontmoette andere leerders tijdens de sessie."),
    ("opbouwen", "werkwoord", "geleidelijk groter of sterker maken", "to build up", "Ze bouwde haar zelfvertrouwen op door regelmatig te oefenen."),
    ("slim", "bijvoeglijk naamwoord", "intelligent of handig in het oplossen van problemen", "smart / clever", "Het was slim om fouten op te schrijven en te herhalen."),
    ("snel", "bijvoeglijk naamwoord / bijwoord", "in korte tijd, met hoge snelheid", "fast / quickly", "Ze leerde snel nieuwe woorden door ze meteen te gebruiken."),
    ("stap", "zelfstandig naamwoord", "een beweging vooruit, of een fase in een proces", "step", "Elke kleine stap telt bij het leren van een taal."),
    ("tevreden", "bijvoeglijk naamwoord", "blij met hoe dingen zijn", "satisfied / content", "Ze was tevreden over haar vooruitgang die maand."),
    ("thuis", "bijwoord / zelfstandig naamwoord", "op de plek waar je woont, of een vertrouwd gevoel", "home / at home", "Ze oefende thuis voor de spiegel."),
    ("tijd", "zelfstandig naamwoord", "de duur van iets, of het moment van de dag", "time", "Ze nam de tijd om elk woord goed uit te spreken."),
    ("toepassen", "werkwoord", "iets wat je hebt geleerd gebruiken in een echte situatie", "to apply", "Ze paste de nieuwe woorden direct toe in een gesprek."),
    ("vaak", "bijwoord", "vele keren, regelmatig", "often / frequently", "Ze maakte vaak dezelfde fout maar corrigeerde zichzelf."),
    ("veranderen", "werkwoord", "anders worden of iets anders maken", "to change", "Haar uitspraak veranderde merkbaar na weken oefenen."),
    ("vergeten", "werkwoord", "iets niet meer weten of niet meer aan iets denken", "to forget", "Ze vergat de nieuwe woorden als ze ze niet herhaalde."),
    ("verschil", "zelfstandig naamwoord", "wat twee dingen anders maakt", "difference", "Ze zag het verschil tussen haar eerste en haar twintigste les."),
    ("vertalen", "werkwoord", "woorden omzetten van de ene taal naar de andere", "to translate", "Ze probeerde niet te vertalen maar direct in het Nederlands te denken."),
    ("vlot", "bijvoeglijk naamwoord / bijwoord", "soepel en zonder veel moeite", "fluent / smooth", "Ze sprak vlotter dan een maand geleden."),
    ("wachten", "werkwoord", "de tijd nemen tot iets gebeurt", "to wait", "Ze wachtte rustig op haar beurt om te spreken."),
    ("waar", "bijvoeglijk naamwoord", "overeenkomend met de werkelijkheid", "true / real", "Dat is waar — oefening maakt de meester."),
    ("welkom", "bijvoeglijk naamwoord", "graag gezien, ontvangen als iemand die erbij hoort", "welcome", "Ze voelde zich welkom in de groep."),
    ("woord", "zelfstandig naamwoord", "een taaleenheid met een betekenis", "word", "Ze leerde elke dag een nieuw woord."),
    ("zinvol", "bijvoeglijk naamwoord", "een duidelijk doel of waarde hebben", "meaningful / worthwhile", "Een kort maar zinvol gesprek is meer waard dan een uur luisteren."),

    # Additional words to reach 200
    ("afmaken", "werkwoord", "iets tot het einde brengen, voltooien", "to finish / to complete", "Ze maakte de oefening af voor ze naar bed ging."),
    ("begrenzen", "werkwoord", "grenzen stellen aan iets", "to limit / to bound", "Ze leerde haar verwachtingen te begrenzen."),
    ("benoemen", "werkwoord", "iets of iemand een naam geven, of iets duidelijk aanwijzen", "to name / to identify", "Hij benoemde de fout zonder de ander te kwetsen."),
    ("beoordelen", "werkwoord", "een oordeel geven over iets of iemand", "to judge / to assess", "Ze beoordeelde haar eigen voortgang eerlijk."),
    ("betrouwbaar", "bijvoeglijk naamwoord", "te vertrouwen, doet wat het belooft", "reliable / trustworthy", "Ze was betrouwbaar en was nooit te laat."),
    ("bezighouden", "werkwoord", "je aandacht of tijd besteden aan iets", "to occupy / to keep busy", "Ze hield zich bezig met dagelijkse oefeningen."),
    ("bijhouden", "werkwoord", "ervoor zorgen dat je niet achterop raakt", "to keep up with / to track", "Ze hield haar nieuwe woorden bij in een notitieboekje."),
    ("concreet", "bijvoeglijk naamwoord", "duidelijk en specifiek, niet vaag", "concrete / specific", "Geef een concreet voorbeeld zodat iedereen het begrijpt."),
    ("duidelijkheid", "zelfstandig naamwoord", "de kwaliteit van helder en begrijpelijk zijn", "clarity", "Ze vroeg om duidelijkheid over de regels."),
    ("effectief", "bijvoeglijk naamwoord", "iets dat goed werkt en het gewenste resultaat geeft", "effective", "Spreken in echte situaties is de meest effectieve manier om te leren."),
    ("eigenlijk", "bijwoord", "in feite, als je er goed over nadenkt", "actually / in fact", "Ze wilde eigenlijk vragen maar durfde niet."),
    ("enthousiast", "bijvoeglijk naamwoord", "vol energie en positief gevoel over iets", "enthusiastic", "Ze was enthousiast over de nieuwe oefening."),
    ("formuleren", "werkwoord", "gedachten in woorden gieten", "to formulate / to phrase", "Ze formuleerde haar vraag voorzichtig maar duidelijk."),
    ("gevoel", "zelfstandig naamwoord", "een emotie of lichamelijke gewaarwording", "feeling / sense", "Ze had het gevoel dat ze vooruitging."),
    ("geweldig", "bijvoeglijk naamwoord", "heel erg goed, indrukwekkend", "great / fantastic", "Het was geweldig om voor het eerst een heel gesprek te voeren."),
    ("graag", "bijwoord", "met plezier, bereid om iets te doen", "gladly / with pleasure", "Ze deed graag mee aan de wekelijkse sessie."),
    ("hardop", "bijwoord", "met een hoorbare stem, niet in gedachten", "out loud / aloud", "Ze las de zinnen hardop voor om de uitspraak te oefenen."),
    ("herhaling", "zelfstandig naamwoord", "het opnieuw doen of zeggen van iets", "repetition / review", "Herhaling is de sleutel tot onthouden."),
    ("hersenen", "zelfstandig naamwoord (meervoud)", "het orgaan in je hoofd waarmee je denkt en leert", "brain", "Je hersenen leren beter als je iets in context gebruikt."),
    ("idee", "zelfstandig naamwoord", "een gedachte of plan", "idea", "Ze had een goed idee voor de volgende oefening."),
    ("inzicht", "zelfstandig naamwoord", "een helder begrip van iets, een moment van begrijpen", "insight / understanding", "Na de uitleg had ze een nieuw inzicht in de grammaticaregel."),
    ("keuze", "zelfstandig naamwoord", "een beslissing tussen twee of meer opties", "choice", "De keuze om dagelijks te oefenen maakte een groot verschil."),
    ("kracht", "zelfstandig naamwoord", "de energie of het vermogen om iets te doen", "strength / power", "Fouten maken kost kracht, maar het loont."),
    ("leuk", "bijvoeglijk naamwoord", "aangenaam, plezierig", "fun / nice", "Ze vond de sessie erg leuk en deed graag mee."),
    ("logisch", "bijvoeglijk naamwoord", "redelijk en begrijpelijk, volgt een patroon", "logical", "De regel werd logisch zodra ze een voorbeeld zag."),
    ("middel", "zelfstandig naamwoord", "een instrument of manier om iets te bereiken", "means / tool", "Spreken is het beste middel om een taal te leren."),
    ("oefening", "zelfstandig naamwoord", "een taak die je helpt te verbeteren", "exercise / practice", "Ze deed elke avond een korte oefening."),
    ("onthouden", "werkwoord", "iets in je geheugen bewaren", "to remember / to memorize", "Ze herhaalde nieuwe woorden om ze beter te onthouden."),
    ("patroon", "zelfstandig naamwoord", "een herhaalbare structuur of manier van doen", "pattern", "Ze herkende het patroon in haar eigen fouten."),
    ("persoonlijk", "bijvoeglijk naamwoord", "behorend bij of gericht op een individu", "personal", "Ze gaf persoonlijke feedback op zijn uitspraak."),
    ("positief", "bijvoeglijk naamwoord", "optimistisch, gunstig", "positive", "Ze bleef positief, ook als het niet meteen lukte."),
    ("punt", "zelfstandig naamwoord", "een specifiek onderdeel of een score", "point", "Ze maakte een goed punt over de uitspraak van lange klinkers."),
    ("regelmatig", "bijvoeglijk naamwoord / bijwoord", "op vaste tijden, met een patroon", "regular / regularly", "Regelmatig oefenen is effectiever dan af en toe intensief."),
    ("richting", "zelfstandig naamwoord", "een kant op, of het pad dat je volgt", "direction", "Ze wist niet zeker in welke richting ze moest gaan met haar studie."),
    ("simpel", "bijvoeglijk naamwoord", "niet ingewikkeld, makkelijk", "simple", "Begin met simpele zinnen en bouw van daaruit verder."),
    ("sterk", "bijvoeglijk naamwoord", "met veel kracht of vermogen", "strong", "Ze had een sterke motivatie om te slagen."),
    ("structuur", "zelfstandig naamwoord", "de manier waarop iets is opgebouwd", "structure", "Een duidelijke structuur helpt bij het begrijpen van lange teksten."),
    ("succes", "zelfstandig naamwoord", "het bereiken van een doel", "success", "Haar succes was het resultaat van maanden consistent oefenen."),
    ("tip", "zelfstandig naamwoord", "een kort en nuttig advies", "tip", "De beste tip die ze kreeg was om elke dag te spreken."),
    ("uitkomst", "zelfstandig naamwoord", "het resultaat of einde van een situatie", "outcome / result", "De uitkomst van de sessie was beter dan ze had verwacht."),
    ("verantwoordelijk", "bijvoeglijk naamwoord", "de verantwoording dragen voor iets", "responsible", "Hij nam verantwoordelijkheid voor zijn eigen fouten."),
    ("vervolgens", "bijwoord", "daarna, als volgende stap", "then / subsequently", "Ze luisterde eerst, vervolgens herhaalde ze de zin."),
]


def _pick_nl_word(date_str: str) -> tuple[str, str, str, str, str]:
    idx = hash(date_str) % len(NL_WORD_LIST)
    return NL_WORD_LIST[idx]


def build_nl_embed_v2(
    entry: tuple[str, str, str, str, str],
    date_str: str,
) -> discord.Embed:
    word, pos, definition, translation, example = entry

    embed = discord.Embed(
        title=f"Woord van de dag: **{word}**",
        description=(
            f"*{pos}*\n\n"
            f"{definition}\n\n"
            f"**Engels:** {translation}"
        ),
    )
    embed.add_field(
        name="Voorbeeldzin",
        value=f"*{example}*",
        inline=False,
    )
    embed.add_field(
        name="Gebruik het",
        value="Maak zelf een zin met dit woord en stuur hem hier. Zo onthoud je het beter.",
        inline=False,
    )
    embed.set_footer(text=date_str)
    return embed