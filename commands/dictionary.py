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

# =====================
# DUTCH WORD LIST
# Each entry: (dutch_word, explanation_in_dutch, example_sentence, english_translation)
# B1/B2 level — practical, conversational Dutch
# =====================

NL_WORD_LIST: list[tuple[str, str, str, str]] = [
    ("aarzelen", "Even wachten voordat je iets doet of zegt, omdat je niet zeker bent.", "Ze aarzelde voordat ze de vraag stelde.", "to hesitate"),
    ("aanmoedigen", "Iemand motiveren om iets te doen of door te gaan.", "Hij moedigde haar aan om door te gaan.", "to encourage"),
    ("aanpassen", "Iets veranderen zodat het beter past bij een situatie.", "Ze paste haar tempo aan tijdens het gesprek.", "to adjust"),
    ("begrijpen", "Iets goed snappen of de betekenis ervan kennen.", "Ik begrijp wat je bedoelt, maar ik zie het anders.", "to understand"),
    ("behoefte", "Iets wat je nodig hebt of heel graag wilt.", "Ze had behoefte aan rust na een drukke week.", "need"),
    ("beseffen", "Ineens begrijpen dat iets zo is.", "Hij besefte dat hij de verkeerde afslag had genomen.", "to realise"),
    ("beslissen", "Een keuze maken na erover nagedacht te hebben.", "Ze besliste om de cursus te volgen.", "to decide"),
    ("bijdragen", "Iets toevoegen wat het geheel beter maakt.", "Iedereen droeg iets bij aan het gesprek.", "to contribute"),
    ("benaderen", "Contact opnemen met iemand of ergens naartoe gaan.", "Ze benaderde het onderwerp voorzichtig.", "to approach"),
    ("boeiend", "Zo interessant dat je er niet mee wilt stoppen.", "Het gesprek was zo boeiend dat de tijd vloog.", "fascinating"),
    ("dankbaar", "Blij zijn met wat iemand voor je heeft gedaan.", "Ze was dankbaar voor de steun die ze kreeg.", "grateful"),
    ("doorzetten", "Doorgaan ook als het moeilijk is.", "Hij zette door, zelfs toen het zwaar was.", "to persevere"),
    ("drempel", "Iets wat het moeilijk maakt om ergens mee te beginnen.", "De drempel om te beginnen met spreken is groot.", "threshold"),
    ("eerlijk", "De waarheid vertellen, ook als dat moeilijk is.", "Ze was eerlijk over wat ze moeilijk vond.", "honest"),
    ("erkennen", "Toegeven dat iets zo is of iemands moeite zien.", "Hij erkende dat hij een fout had gemaakt.", "to acknowledge"),
    ("ervaring", "Iets wat je hebt meegemaakt en wat je iets heeft geleerd.", "Ze had veel ervaring met spreken voor groepen.", "experience"),
    ("flexibel", "Makkelijk kunnen veranderen of aanpassen.", "Hij is flexibel als het gaat om werktijden.", "flexible"),
    ("geduld", "Rustig kunnen wachten zonder gefrustreerd te raken.", "Geduld is belangrijk bij het leren van een taal.", "patience"),
    ("gewoonte", "Iets wat je zo vaak doet dat het vanzelf gaat.", "Dagelijks oefenen wordt snel een gewoonte.", "habit"),
    ("grens", "De lijn die aangeeft hoe ver je bereid bent te gaan.", "Het is goed om grenzen te stellen in gesprekken.", "boundary"),
    ("herkennen", "Zien dat je iets al eerder hebt gezien of gehoord.", "Ze herkende het patroon in haar eigen fouten.", "to recognise"),
    ("herhaling", "Iets nog een keer doen om het beter te leren.", "Door herhaling onthoud je nieuwe woorden beter.", "repetition"),
    ("inzet", "De moeite en energie die je ergens in stopt.", "Zijn inzet was duidelijk te zien aan het resultaat.", "effort / dedication"),
    ("luisteren", "Goed opletten op wat iemand zegt.", "Goed luisteren is net zo belangrijk als spreken.", "to listen"),
    ("mening", "Wat jij denkt over een onderwerp.", "Ze gaf haar mening zonder anderen te kwetsen.", "opinion"),
    ("mislukken", "Niet slagen in wat je wilde bereiken.", "Hij was niet bang om te mislukken.", "to fail"),
    ("misverstand", "Iets wat verkeerd begrepen is.", "Er was een misverstand over de afspraak.", "misunderstanding"),
    ("nadenken", "De tijd nemen om goed over iets na te denken.", "Ze nam even de tijd om na te denken voordat ze antwoordde.", "to think / reflect"),
    ("neiging", "De natuurlijke aandrang om iets op een bepaalde manier te doen.", "Ze had de neiging om snel te praten als ze nerveus was.", "tendency"),
    ("nieuwsgierig", "Veel interesse hebben in iets en er meer over willen weten.", "Hij was nieuwsgierig naar haar verhaal.", "curious"),
    ("omgaan met", "Weten hoe je met iets of iemand moet handelen.", "Ze leerde omgaan met kritiek op haar werk.", "to deal with / cope with"),
    ("ongemakkelijk", "Het gevoel dat iets niet prettig of niet goed voelt.", "Hij voelde zich ongemakkelijk in het gesprek.", "uncomfortable"),
    ("onthouden", "Iets bewaren in je geheugen.", "Het is makkelijker om woorden te onthouden als je ze gebruikt.", "to remember"),
    ("onverwacht", "Iets wat je niet had zien aankomen.", "Ze gaf een onverwacht eerlijk antwoord.", "unexpected"),
    ("oprecht", "Echt menen wat je zegt, zonder te doen alsof.", "Zijn compliment voelde oprecht aan.", "genuine / sincere"),
    ("oefenen", "Iets steeds opnieuw doen om er beter in te worden.", "Ze oefende elke dag een kwartier met spreken.", "to practise"),
    ("oplossing", "Een manier om een probleem op te lossen.", "Ze zochten samen naar een oplossing.", "solution"),
    ("overtuigen", "Iemand laten geloven dat jij gelijk hebt.", "Hij probeerde haar te overtuigen met voorbeelden.", "to convince"),
    ("pauzeren", "Even stoppen met praten of doen.", "Het is oké om te pauzeren voordat je antwoord geeft.", "to pause"),
    ("perspectief", "De manier waarop je naar iets kijkt.", "Vanuit een ander perspectief ziet het er anders uit.", "perspective"),
    ("reageren", "Iets zeggen of doen als reactie op iemand anders.", "Ze reageerde rustig op de kritiek.", "to respond / react"),
    ("relatie", "De verbinding die je met iemand hebt.", "Een goede relatie is gebaseerd op vertrouwen.", "relationship"),
    ("respect", "Iemand waarderen en serieus nemen.", "Ze behandelde iedereen met respect.", "respect"),
    ("routine", "Een vaste manier van doen die je elke dag herhaalt.", "Een goede oefenroutine helpt je vooruit.", "routine"),
    ("samenwerken", "Met anderen aan hetzelfde doel werken.", "Samenwerken maakt moeilijke taken makkelijker.", "to collaborate"),
    ("sfeer", "Het gevoel dat ergens hangt, zoals in een kamer of gesprek.", "De sfeer in het gesprek was ontspannen.", "atmosphere"),
    ("spreken", "Woorden hardop zeggen.", "Ze was bang om te spreken voor een groep.", "to speak"),
    ("starten", "Beginnen met iets.", "Het moeilijkste is om te starten.", "to start"),
    ("steun", "Hulp of aanmoediging van iemand anders.", "Ze voelde de steun van haar groepsleden.", "support"),
    ("twijfelen", "Niet zeker zijn over wat je moet denken of doen.", "Hij twijfelde of hij zijn mening zou delen.", "to doubt / hesitate"),
    ("uitdaging", "Iets wat moeilijk is maar je sterker maakt.", "Elke dag spreken is een uitdaging die de moeite waard is.", "challenge"),
    ("uitdrukken", "Laten zien of zeggen wat je denkt of voelt.", "Het is soms moeilijk om je gevoelens uit te drukken.", "to express"),
    ("uitleggen", "Iets duidelijk maken voor iemand anders.", "Ze legde rustig uit wat ze bedoelde.", "to explain"),
    ("uitstelgedrag", "Het steeds uitstellen van iets wat je moet doen.", "Uitstelgedrag maakt dingen niet makkelijker.", "procrastination"),
    ("vaardigheden", "Dingen die je kunt omdat je ze hebt geleerd of geoefend.", "Spreken is een vaardigheid die je kunt trainen.", "skills"),
    ("verbeteren", "Beter worden in iets.", "Ze verbeterde elke week een beetje.", "to improve"),
    ("verlegen", "Je onzeker of bang voelen in sociale situaties.", "Hij was verlegen toen hij voor het eerst meedeed.", "shy / embarrassed"),
    ("vertrouwen", "Geloven dat iemand of iets betrouwbaar is.", "Vertrouwen in jezelf groeit door te oefenen.", "trust / confidence"),
    ("verwachting", "Wat je denkt dat er gaat gebeuren.", "Ze had hoge verwachtingen van zichzelf.", "expectation"),
    ("vooruitgang", "Beter worden over tijd.", "Ze zag haar eigen vooruitgang na een maand oefenen.", "progress"),
    ("vraag stellen", "Om informatie vragen aan iemand.", "Een goede vraag stellen is een kunst.", "to ask a question"),
    ("waarderen", "Iets of iemand op waarde schatten.", "Ze waardeerde de eerlijke feedback.", "to appreciate"),
    ("waarnemen", "Iets opmerken met je zintuigen of aandacht.", "Hij nam de sfeer in de kamer rustig waar.", "to observe"),
    ("zelfstandig", "Dingen kunnen doen zonder hulp van anderen.", "Ze werkte graag zelfstandig aan haar oefeningen.", "independent"),
    ("zelfvertrouwen", "Het geloof in je eigen kunnen.", "Spreken voor anderen vraagt zelfvertrouwen.", "self-confidence"),
    ("zelfverzekerd", "Je sterk en zeker voelen over wie je bent of wat je doet.", "Ze sprak zelfverzekerd, ook al was ze nerveus.", "confident"),
    ("zenuwachtig", "Je onrustig voelen omdat iets je spanning geeft.", "Hij was zenuwachtig voor zijn eerste gesprek.", "nervous"),
    ("zich aanpassen", "Je gedrag veranderen zodat het past in een situatie.", "Ze paste zich snel aan in de nieuwe groep.", "to adapt"),
    ("zich concentreren", "Je aandacht volledig op iets richten.", "Het was moeilijk om je te concentreren met veel lawaai.", "to concentrate / focus"),
    ("zich vergissen", "Een fout maken doordat je iets verkeerd dacht.", "Ze vergiste zich in de datum maar lachte erom.", "to make a mistake / be mistaken"),
    ("zinvol", "Iets wat waarde of betekenis heeft.", "Zinvolle gesprekken voeren helpt je groeien.", "meaningful"),
    ("zorgen maken", "Piekeren over iets wat misschien fout gaat.", "Ze maakte zich zorgen over haar uitspraak.", "to worry"),
    ("aandacht", "Je geest richten op iets of iemand.", "Ze gaf haar volledige aandacht aan het gesprek.", "attention"),
    ("aanwezig", "Ergens fysiek zijn maar ook echt betrokken zijn.", "Aanwezig zijn in een gesprek betekent echt luisteren.", "present"),
    ("afleiding", "Iets wat je aandacht wegtrekt van waar je mee bezig bent.", "Zijn telefoon was een grote afleiding.", "distraction"),
    ("beginner", "Iemand die net begint met iets.", "Als beginner maak je fouten en dat is normaal.", "beginner"),
    ("bewust", "Weten wat je doet of wat er om je heen gebeurt.", "Ze was zich bewust van haar eigen fouten.", "aware / conscious"),
    ("doelgericht", "Met een duidelijk doel voor ogen werken.", "Ze oefende doelgericht aan haar uitspraak.", "goal-oriented"),
    ("fout", "Iets wat niet klopt of niet goed is gedaan.", "Fouten maken hoort bij leren.", "mistake"),
    ("gevoel", "Wat je van binnen ervaart, zoals blijdschap of angst.", "Ze had het gevoel dat ze vooruitging.", "feeling"),
    ("gesprek", "Een uitwisseling van woorden tussen mensen.", "Een goed gesprek vraagt luisteren en spreken.", "conversation"),
    ("gewenning", "Het proces waarbij iets normaal wordt door herhaling.", "Door gewenning wordt spreken minder spannend.", "getting used to something"),
    ("herhalen", "Iets nog een keer zeggen of doen.", "Ze herhaalde het woord totdat ze het kende.", "to repeat"),
    ("indruk", "Het beeld dat iemand van jou krijgt.", "Ze maakte een goede indruk tijdens het gesprek.", "impression"),
    ("inspanning", "De moeite die je ergens in steekt.", "Elke inspanning die je levert telt mee.", "effort"),
    ("klaar", "Gereed zijn om iets te doen.", "Je hoeft niet perfect klaar te zijn om te beginnen.", "ready"),
    ("moeite", "Iets kost energie of is niet gemakkelijk.", "Het kostte haar moeite om de juiste woorden te vinden.", "difficulty / effort"),
    ("motivatie", "De reden waarom je iets wilt doen.", "Haar motivatie om te leren was groot.", "motivation"),
    ("opvallen", "Gezien of opgemerkt worden door anderen.", "Zijn manier van spreken viel op in de groep.", "to stand out"),
    ("rust", "Een gevoel van kalmte en ontspanning.", "Ze nam een moment rust voordat ze antwoordde.", "calm / rest"),
    ("samenvatten", "De belangrijkste punten kort herhalen.", "Ze vatte het gesprek samen in een paar zinnen.", "to summarise"),
    ("stil", "Zonder geluid, of weinig zeggen.", "Een moment stil zijn is geen probleem in een gesprek.", "quiet / silent"),
    ("tempo", "De snelheid waarmee je iets doet.", "Spreek op een tempo dat voor jou comfortabel is.", "pace / speed"),
    ("terughoudend", "Voorzichtig en niet snel geneigd om mee te doen.", "Ze was terughoudend om haar mening te geven.", "reserved / reluctant"),
    ("toepassen", "Iets wat je hebt geleerd gebruiken in de praktijk.", "Ze paste de nieuwe woorden toe in een gesprek.", "to apply"),
    ("twijfel", "Het gevoel dat je niet zeker weet wat je moet denken.", "Twijfel is normaal als je een nieuwe taal leert.", "doubt"),
    ("verduidelijken", "Iets duidelijker maken zodat anderen het beter begrijpen.", "Ze verduidelijkte haar vraag met een voorbeeld.", "to clarify"),
    ("verrassend", "Iets wat je niet had verwacht.", "Het was verrassend hoe snel ze vooruitging.", "surprising"),
    ("volhouden", "Doorgaan ook als het moeilijk wordt.", "Volhouden is het geheim van vooruitgang.", "to keep going / persist"),
    ("zin", "Een reeks woorden die samen een gedachte uitdrukken.", "Probeer elke dag een nieuwe zin te maken.", "sentence"),
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
    """Pick an English word deterministically by date."""
    idx = hash(date_str) % len(WORD_LIST)
    return WORD_LIST[idx]


def _pick_nl_word(date_str: str) -> tuple[str, str, str, str]:
    """Pick a Dutch word deterministically by date."""
    idx = hash(date_str) % len(NL_WORD_LIST)
    return NL_WORD_LIST[idx]


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
    explanation: str,
    example: str,
    english: str,
    date_str: str,
) -> discord.Embed:
    embed = discord.Embed(title=f"Woord van de dag: {word.lower()}")
    embed.description = (
        f"{explanation}\n\n"
        f"**Engels:** {english}"
    )
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
        word, explanation, example, english = _pick_nl_word(date_str)
        embed = build_nl_embed(word, explanation, example, english, date_str)

        ch = await self._get_channel(NL_WOTD_CHANNEL_ID)
        if not ch:
            return
        try:
            await ch.send(embed=embed)
            log.info("WOTD: posted Dutch word '%s' for %s", word, date_str)
        except Exception:
            log.exception("WOTD: failed to post Dutch word")