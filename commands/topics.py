from __future__ import annotations

# commands/topics.py
import logging

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("commands.topics")

# =====================
# TOPIC DATA
# =====================

EN_TOPICS: dict[str, dict] = {
    "family": {
        "label": "👨‍👩‍👧 Family",
        "questions": [
            ("How many people are in your family?", "Try: *sibling, only child, extended family, household*"),
            ("Who are you closest to in your family and why?", "Try: *bond with, look up to, grow up with, depend on*"),
            ("How often do you spend time with your family?", "Try: *get together, catch up, stay in touch, reunion*"),
            ("Did you grow up in a big city or a small town?", "Try: *neighbourhood, move around, settle down, hometown*"),
            ("What's a tradition your family has?", "Try: *celebrate, gather, pass down, every year without fail*"),
            ("How has your relationship with your parents changed as you got older?", "Try: *independent, appreciate, see eye to eye, perspective*"),
            ("Do you think family is something you're born into or something you choose?", "Try: *close-knit, chosen family, blood, unconditional*"),
            ("What's something you learned from a family member that you still use today?", "Try: *taught me, picked up, pass on, grateful for*"),
            ("How do you handle disagreements with family?", "Try: *conflict, set boundaries, talk it out, let it go*"),
            ("What does a typical family dinner look like in your home?", "Try: *sit down together, catch up, noisy, quiet, take turns*"),
        ],
    },
    "food": {
        "label": "🍜 Food",
        "questions": [
            ("What's your favourite meal and when do you usually eat it?", "Try: *comfort food, go-to, have it whenever, grew up eating*"),
            ("Are you a good cook? What can you make?", "Try: *follow a recipe, from scratch, experiment, disaster*"),
            ("What food from your country do you think everyone should try?", "Try: *traditional, typical, you have to try it, underrated*"),
            ("Is there a food you hated as a child but like now?", "Try: *couldn't stand, an acquired taste, grew on me, now I love it*"),
            ("Do you prefer eating at home or going to a restaurant?", "Try: *atmosphere, convenience, homemade, treat yourself*"),
            ("How important is food in your culture?", "Try: *central to, bring people together, celebration, expression*"),
            ("Have you ever tried food from another country that surprised you?", "Try: *wasn't expecting, turned out to be, completely different, loved it*"),
            ("Do you eat breakfast every day? What do you have?", "Try: *skip it, proper breakfast, quick bite, habit*"),
            ("Is there a food you absolutely refuse to eat?", "Try: *can't stand, no matter what, texture, just not for me*"),
            ("What's the most interesting thing you've ever eaten?", "Try: *unusual, wouldn't normally, dared to try, glad I did*"),
        ],
    },
    "hobbies": {
        "label": "🎨 Hobbies",
        "questions": [
            ("What do you do when you have free time?", "Try: *unwind, keep busy, lose track of time, go-to activity*"),
            ("Is there a hobby you've always wanted to try but haven't yet?", "Try: *been meaning to, intimidated by, give it a go, someday*"),
            ("How did you get into your current hobby?", "Try: *picked it up, got into it, stumbled across, started when*"),
            ("Do you prefer active hobbies or more relaxing ones?", "Try: *get moving, wind down, depends on the day, balance*"),
            ("Has a hobby ever turned into something more, like a job or a business?", "Try: *side project, monetise, passion project, took off*"),
            ("What hobby would you recommend to someone who says they're bored?", "Try: *gets you out of your head, easy to start, cheap, rewarding*"),
            ("Do you have a hobby that most people find surprising?", "Try: *you'd never guess, people always react, unusual, niche*"),
            ("How much time per week do you spend on your hobbies?", "Try: *fit it in, make time for, whenever I can, dedicated*"),
            ("Is there a hobby you gave up? Why?", "Try: *lost interest, ran out of time, moved on, not for me*"),
            ("What's something you've made or created that you're proud of?", "Try: *put a lot into it, came out well, showed someone, kept it*"),
        ],
    },
    "travel": {
        "label": "✈️ Travel",
        "questions": [
            ("What's the best place you've ever visited?", "Try: *blew me away, worth every penny, would go back, recommend*"),
            ("Do you prefer beach holidays or city breaks?", "Try: *switch off, explore, take in the sights, pace*"),
            ("What's the worst travel experience you've had?", "Try: *went wrong, delayed, lost, somehow survived*"),
            ("How do you usually travel — planned or spontaneous?", "Try: *book in advance, last minute, go with the flow, itinerary*"),
            ("Is there a place you really want to visit one day?", "Try: *on my list, always dreamed of, ever since I saw*"),
            ("What do you always bring with you when you travel?", "Try: *can't leave without, essential, learned my lesson, always pack*"),
            ("How has travel changed you?", "Try: *opened my eyes, perspective, appreciate, realised*"),
            ("Do you prefer travelling alone or with others?", "Try: *your own pace, compromise, share the experience, depends*"),
            ("What's something about your home country that surprises visitors?", "Try: *people always say, didn't expect, turns out, not what they imagined*"),
            ("What's the most important thing you've learned from being in a different country?", "Try: *realised, assumption, took for granted, normal isn't universal*"),
        ],
    },
    "work": {
        "label": "💼 Work",
        "questions": [
            ("What do you do for work and how did you end up there?", "Try: *fell into it, planned, one thing led to another, studied for it*"),
            ("What do you enjoy most about your job?", "Try: *fulfilling, keeps me busy, good at it, look forward to*"),
            ("What's the most stressful part of your work?", "Try: *pressure, deadline, dealing with, never quite switches off*"),
            ("Do you work from home or in an office?", "Try: *flexible, miss the office, prefer working from, commute*"),
            ("What would your dream job be if money wasn't a factor?", "Try: *if I could do anything, imagine doing, passion, pay the bills*"),
            ("Have you ever had a job you really disliked?", "Try: *just to get by, couldn't stand, quit eventually, not for me*"),
            ("How do you separate work from your personal life?", "Try: *switch off, set boundaries, hard to disconnect, routine helps*"),
            ("What skills do you use every day at work?", "Try: *rely on, comes naturally now, took time to develop, essential*"),
            ("How important is work to your identity?", "Try: *define yourself by, more than a job, just a job, sense of purpose*"),
            ("What's one thing you wish people understood about your job?", "Try: *not as easy as it looks, a lot goes into it, misconception, actually*"),
        ],
    },
    "learning": {
        "label": "📚 Learning",
        "questions": [
            ("Why did you start learning English?", "Try: *practical reason, always wanted to, needed it for, just decided*"),
            ("What's the hardest thing about learning a new language?", "Try: *pronunciation, grammar, vocabulary, thinking in it*"),
            ("How do you practise English outside of lessons?", "Try: *watch series, read, use it at work, talk to myself*"),
            ("Have you ever felt embarrassed speaking English? What happened?", "Try: *froze, said the wrong thing, people were kind, laughed it off*"),
            ("What's something you can do now in English that you couldn't do before?", "Try: *follow a conversation, express myself, understand humour*"),
            ("Do you learn better alone or with other people?", "Try: *focus better, learn from others, need feedback, at my own pace*"),
            ("Is there something outside of English you're currently learning?", "Try: *picked up, trying to get better at, just started, slowly*"),
            ("What's a word or phrase in English you really like?", "Try: *no equivalent, sounds right, useful, hard to translate*"),
            ("How has learning English changed your life?", "Try: *opened doors, access to, confidence, connected me to*"),
            ("What advice would you give someone just starting to learn English?", "Try: *don't wait until, just start, mistakes are part of, be patient*"),
        ],
    },
    "health": {
        "label": "🏃 Health",
        "questions": [
            ("Do you exercise regularly? What do you do?", "Try: *keep active, routine, fit it in, not really but*"),
            ("How do you take care of your mental health?", "Try: *switch off, talk to someone, need space, helps me*"),
            ("What does a healthy lifestyle look like to you?", "Try: *balance, not obsessive, realistic, sustainable*"),
            ("Have you ever changed a habit for health reasons?", "Try: *cut out, started, made a difference, harder than expected*"),
            ("Do you sleep enough? What gets in the way?", "Try: *struggle to, too much on my mind, routine, early riser*"),
            ("Is health something you think about a lot or not really?", "Try: *in the background, only when something's wrong, conscious of*"),
            ("What's one healthy habit you'd like to build?", "Try: *been meaning to, tried before, small step, consistent*"),
            ("How do you feel when you haven't moved your body in a few days?", "Try: *restless, sluggish, doesn't bother me, notice the difference*"),
            ("Do you think mental and physical health are equally important?", "Try: *connected, one affects the other, often ignore, take seriously*"),
            ("What's something people get wrong about being healthy?", "Try: *all or nothing, misconception, doesn't have to be, actually*"),
        ],
    },
    "technology": {
        "label": "📱 Technology",
        "questions": [
            ("How much time do you spend on your phone each day?", "Try: *scroll, check it constantly, try to limit, before I know it*"),
            ("What app do you use most and why?", "Try: *can't be without, habit, useful for, check it first*"),
            ("Do you think social media is mostly positive or negative?", "Try: *connects people, comparison, time sink, depends how you use it*"),
            ("Has technology made your life easier or more complicated?", "Try: *saves time, always available, expectation, can't switch off*"),
            ("Is there a piece of technology you couldn't live without?", "Try: *rely on, panic without, changed how I, essential*"),
            ("Do you worry about privacy online?", "Try: *careful about, doesn't bother me, should probably, aware of*"),
            ("How do you feel about AI?", "Try: *excited, nervous, useful, not sure what to think yet*"),
            ("Do you remember life before smartphones?", "Try: *used to just, can't imagine now, simpler in some ways, miss*"),
            ("How has technology changed the way you communicate with people?", "Try: *keep in touch, less personal, easier, different from before*"),
            ("Do you think we use technology too much?", "Try: *hard to step away, numbing, useful but, balance*"),
        ],
    },
    "emotions": {
        "label": "💬 Emotions",
        "questions": [
            ("What makes you feel most at peace?", "Try: *calm down, let go, at ease, feels right*"),
            ("How do you handle stress?", "Try: *go-to, cope with, doesn't help, works for me*"),
            ("Is it easy for you to talk about how you feel?", "Try: *open up, hold it in, depends who with, grew up not*"),
            ("What's something that makes you genuinely happy?", "Try: *lights me up, look forward to, simple things, can't explain*"),
            ("Have you ever felt proud of yourself? What for?", "Try: *wasn't easy, pushed through, turned out well, surprised myself*"),
            ("What do you do when you're feeling down?", "Try: *withdraw, reach out, keep going, give it time*"),
            ("Do you find it easier to express emotions in your first language?", "Try: *comes naturally, lose something in translation, more direct, feels different*"),
            ("Is there an emotion that's difficult for you to express?", "Try: *uncomfortable, not used to, comes out wrong, working on it*"),
            ("What's something small that can change your whole mood?", "Try: *turns the day around, unexpected, just need, surprisingly effective*"),
            ("How do you support someone you care about when they're struggling?", "Try: *be there, listen, don't always know what to say, just show up*"),
        ],
    },
    "future": {
        "label": "🔮 Future",
        "questions": [
            ("Where do you see yourself in five years?", "Try: *hard to say, heading towards, working on, hope to*"),
            ("Is there something you really want to achieve in life?", "Try: *drive me, keep coming back to, not giving up on, someday*"),
            ("Do you prefer to plan ahead or take things as they come?", "Try: *need structure, go with the flow, depends, mix of both*"),
            ("What's something you want to learn or do before you turn a certain age?", "Try: *before I'm too old, always said I would, running out of excuses*"),
            ("Are you optimistic or realistic about the future?", "Try: *cautiously, tend to, try to be, not always*"),
            ("What kind of life do you want to be living in ten years?", "Try: *picture it, working towards, honestly not sure, matters most*"),
            ("Is there something holding you back from a goal right now?", "Try: *hesitant, practical reasons, fear of, waiting for the right time*"),
            ("Do you think about the impact you want to have on other people?", "Try: *leave behind, small ways, not something I, matters to me*"),
            ("What does success mean to you personally?", "Try: *not about money, feeling of, on your own terms, changes over time*"),
            ("If you could give advice to your younger self, what would you say?", "Try: *would tell myself, wish I'd known, taken too seriously, let go of*"),
        ],
    },
}

# Dutch topics — same structure
NL_TOPICS: dict[str, dict] = {
    "familie": {
        "label": "👨‍👩‍👧 Familie",
        "questions": [
            ("Hoeveel mensen wonen er in jouw huishouden?", "Probeer: *gezin, alleen, samenwonen, thuis bij*"),
            ("Met wie in jouw familie heb je de beste band en waarom?", "Probeer: *opkijken naar, vertrouwen, altijd voor me klaar, band met*"),
            ("Hoe vaak zie je je familie?", "Probeer: *bij elkaar komen, contact houden, lang niet gezien, elk weekend*"),
            ("Ben je opgegroeid in een grote stad of een klein dorp?", "Probeer: *buurt, verhuisd, gesetteld, thuis voelen*"),
            ("Heeft jouw familie een traditie die je elk jaar herhaalt?", "Probeer: *elke keer, samen doen, altijd al, doorgeven*"),
            ("Hoe is jouw relatie met je ouders veranderd toen je ouder werd?", "Probeer: *zelfstandig, anders gaan kijken, meer begrip, anders dan vroeger*"),
            ("Denk je dat familie iets is wat je kiest of iets wat je gegeven is?", "Probeer: *verbonden, gekozen, onvoorwaardelijk, meer dan bloed*"),
            ("Wat heb je van een familielid geleerd wat je nog steeds gebruikt?", "Probeer: *bijgebracht, meegegeven, dankbaar voor, nooit vergeten*"),
            ("Hoe ga je om met ruzies in de familie?", "Probeer: *uitpraten, grenzen stellen, loslaten, moeilijk soms*"),
            ("Hoe ziet een typische avondmaaltijd bij jou thuis eruit?", "Probeer: *samen aan tafel, bijpraten, druk, rustig, om beurten*"),
        ],
    },
    "eten": {
        "label": "🍜 Eten",
        "questions": [
            ("Wat is jouw favoriete maaltijd en wanneer eet je die?", "Probeer: *troosteten, altijd zin in, ben er mee opgegroeid, kookt lekker*"),
            ("Kun je goed koken? Wat maak je?", "Probeer: *recept volgen, van scratch, experimenteren, mislukt*"),
            ("Welk gerecht uit jouw land zou iedereen moeten proberen?", "Probeer: *typisch, traditioneel, je moet het echt proberen, onderschat*"),
            ("Is er een eten dat je als kind haatte maar nu lekker vindt?", "Probeer: *kon het niet uitstaan, went aan, nu ben ik er dol op, grappig eigenlijk*"),
            ("Eet je liever thuis of ga je liever uit eten?", "Probeer: *gezelligheid, gemak, zelf gemaakt, traktatie*"),
            ("Hoe belangrijk is eten in jouw cultuur?", "Probeer: *centraal, mensen bijeenbrengen, feest, uitdrukking van*"),
            ("Heb je ooit iets gegeten uit een ander land dat je verraste?", "Probeer: *had het niet verwacht, bleek heerlijk te zijn, totaal anders, blij dat ik het probeerde*"),
            ("Eet je elke dag ontbijt? Wat eet je dan?", "Probeer: *sla het over, uitgebreid ontbijt, snel iets, gewoonte*"),
            ("Is er een eten dat je echt niet lust?", "Probeer: *al van kleins af, structuur, gewoon niet voor mij, ruikt al*"),
            ("Wat is het opvallendste dat je ooit gegeten hebt?", "Probeer: *ongewoon, normaal nooit, aangedurfd, blij dat ik het deed*"),
        ],
    },
    "hobby": {
        "label": "🎨 Hobby's",
        "questions": [
            ("Wat doe je als je vrije tijd hebt?", "Probeer: *ontspannen, bezig houden, tijd vergeet ik bij, favoriete bezigheid*"),
            ("Is er een hobby die je altijd hebt willen proberen maar nog niet hebt?", "Probeer: *ben er al een tijdje mee bezig, ertegenop zie, gewoon beginnen, ooit nog*"),
            ("Hoe ben je bij jouw huidige hobby terechtgekomen?", "Probeer: *toevallig, opgebouwd, ben er ingerold, begonnen toen*"),
            ("Heb je liever actieve hobby's of meer ontspannende?", "Probeer: *in beweging, tot rust komen, hangt van de dag af, combinatie*"),
            ("Is een hobby ooit iets groters geworden, zoals een baan of een project?", "Probeer: *nevenproject, uitgebouwd, passieproject, liep er mee weg*"),
            ("Welke hobby zou je aanraden aan iemand die zegt dat ze zich vervelen?", "Probeer: *zet je hoofd leeg, makkelijk te beginnen, goedkoop, voldoening*"),
            ("Heb je een hobby die mensen verrast?", "Probeer: *dat hadden ze niet verwacht, reacties erop, ongewoon, niche*"),
            ("Hoeveel tijd besteed je per week aan je hobby's?", "Probeer: *inplannen, tijd voor maken, wanneer het kan, vaste tijd*"),
            ("Is er een hobby die je hebt opgegeven? Waarom?", "Probeer: *verloor mijn interesse, geen tijd meer, voorbij, toch niet voor mij*"),
            ("Wat heb je ooit gemaakt of bereikt waar je trots op bent?", "Probeer: *veel in gestoken, goed uitgekomen, aan anderen laten zien, bewaard*"),
        ],
    },
    "reizen": {
        "label": "✈️ Reizen",
        "questions": [
            ("Wat is de mooiste plek die je ooit hebt bezocht?", "Probeer: *overweldigd, elke cent waard, zou er graag terugkeren, aanrader*"),
            ("Ga je liever naar het strand of een stad op vakantie?", "Probeer: *uitschakelen, verkennen, bezienswaardigheden, tempo*"),
            ("Wat is de slechtste reiservaring die je hebt gehad?", "Probeer: *fout gegaan, vertraging, verloren, op de een of andere manier overleefd*"),
            ("Reis je liever gepland of spontaan?", "Probeer: *ver van tevoren boeken, op het laatste moment, meestromen, reisplan*"),
            ("Is er een plek die je echt een keer wilt bezoeken?", "Probeer: *staat op mijn lijst, altijd gedroomd van, ooit nog*"),
            ("Wat neem je altijd mee op reis?", "Probeer: *kan niet zonder, essentieel, les geleerd, altijd in mijn tas*"),
            ("Hoe heeft reizen jou veranderd?", "Probeer: *ogen geopend, perspectief, meer waardering, besefte*"),
            ("Reis je liever alleen of met anderen?", "Probeer: *eigen tempo, compromissen sluiten, beleving delen, hangt ervan af*"),
            ("Wat verrast bezoekers aan jouw land?", "Probeer: *mensen zeggen altijd, had het niet verwacht, blijkt, anders dan verwacht*"),
            ("Wat heb je geleerd door in een ander land te zijn?", "Probeer: *besefte, aanname, vanzelfsprekend, normaal is niet universeel*"),
        ],
    },
    "werk": {
        "label": "💼 Werk",
        "questions": [
            ("Wat doe je voor werk en hoe ben je daar terechtgekomen?", "Probeer: *erin gerold, bewust gekozen, het een leidde tot het ander, voor gestudeerd*"),
            ("Wat vind je het leukste aan je werk?", "Probeer: *geeft voldoening, houdt me bezig, goed in, kijk naar uit*"),
            ("Wat is het meest stressvolle aan jouw werk?", "Probeer: *druk, deadline, omgaan met, schakel nooit helemaal uit*"),
            ("Werk je thuis of op kantoor?", "Probeer: *flexibel, mis het kantoor, werk liever vanuit, reistijd*"),
            ("Wat zou jouw droomjob zijn als geld geen rol speelde?", "Probeer: *als ik alles kon doen, stel je voor, passie, rekeningen betalen*"),
            ("Heb je ooit een baan gehad die je echt niet leuk vond?", "Probeer: *gewoon voor de centen, kon het niet uitstaan, uiteindelijk gestopt, niet voor mij*"),
            ("Hoe scheid je werk van je privéleven?", "Probeer: *loskoppelen, grenzen stellen, moeilijk af te schakelen, routine helpt*"),
            ("Welke vaardigheden gebruik je elke dag op je werk?", "Probeer: *steun op, gaat nu vanzelf, duurde even, onmisbaar*"),
            ("Hoe belangrijk is werk voor jouw identiteit?", "Probeer: *meer dan alleen een baan, gewoon werk, zingeving, bepaalt wie ik ben*"),
            ("Wat wil je dat mensen beter begrijpen over jouw werk?", "Probeer: *zo makkelijk is het niet, er gaat veel in om, misverstand, eigenlijk*"),
        ],
    },
    "leren": {
        "label": "📚 Leren",
        "questions": [
            ("Waarom ben je begonnen met Nederlands leren?", "Probeer: *praktische reden, altijd al gewild, had het nodig voor, gewoon besloten*"),
            ("Wat vind je het moeilijkste aan een nieuwe taal leren?", "Probeer: *uitspraak, grammatica, woordenschat, erin denken*"),
            ("Hoe oefen je Nederlands buiten de lessen om?", "Probeer: *series kijken, lezen, gebruik het op mijn werk, praat met mezelf*"),
            ("Heb je je ooit verlegen gevoeld bij het spreken van Nederlands? Wat gebeurde er?", "Probeer: *werd blokker, zei het verkeerd, mensen reageerden vriendelijk, moest erom lachen*"),
            ("Wat kun je nu in het Nederlands wat je eerder niet kon?", "Probeer: *een gesprek volgen, mezelf uitdrukken, humor begrijpen*"),
            ("Leer je liever alleen of met anderen?", "Probeer: *beter focussen, leer van anderen, feedback nodig, op mijn eigen tempo*"),
            ("Is er iets buiten het Nederlands wat je momenteel aan het leren bent?", "Probeer: *opgebouwd, probeer beter in te worden, net begonnen, langzaam*"),
            ("Is er een woord of uitdrukking in het Nederlands die je echt leuk vindt?", "Probeer: *geen equivalent voor, klinkt goed, handig, moeilijk te vertalen*"),
            ("Hoe heeft het leren van Nederlands jouw leven veranderd?", "Probeer: *deuren geopend, toegang tot, zelfvertrouwen, verbindt me met*"),
            ("Welk advies zou jij geven aan iemand die net begint met Nederlands leren?", "Probeer: *wacht niet tot, gewoon beginnen, fouten horen erbij, wees geduldig*"),
        ],
    },
    "gezondheid": {
        "label": "🏃 Gezondheid",
        "questions": [
            ("Beweeg je regelmatig? Wat doe je?", "Probeer: *actief blijven, routine, past het in, niet echt maar*"),
            ("Hoe zorg je voor je mentale gezondheid?", "Probeer: *afschakelen, met iemand praten, ruimte nodig, helpt me*"),
            ("Hoe ziet een gezonde leefstijl er voor jou uit?", "Probeer: *balans, niet obsessief, realistisch, vol te houden*"),
            ("Heb je ooit een gewoonte veranderd om gezondheidsredenen?", "Probeer: *gestopt met, begonnen met, maakte verschil, moeilijker dan verwacht*"),
            ("Slaap je genoeg? Wat staat dat in de weg?", "Probeer: *moeite mee, te veel aan mijn hoofd, routine, vroege vogel*"),
            ("Is gezondheid iets wat je veel aan denkt of niet zo?", "Probeer: *op de achtergrond, pas als er iets is, bewust van*"),
            ("Welke gezonde gewoonte wil je opbouwen?", "Probeer: *al een tijdje van plan, eerder geprobeerd, kleine stap, consequent*"),
            ("Hoe voel je je als je een paar dagen niet in beweging bent geweest?", "Probeer: *rusteloos, traag, maakt me niet uit, merk het verschil*"),
            ("Denk je dat mentale en fysieke gezondheid even belangrijk zijn?", "Probeer: *verbonden, het een beïnvloedt het ander, vaak vergeten, serieus nemen*"),
            ("Wat begrijpen mensen verkeerd over gezond zijn?", "Probeer: *alles of niets, misverstand, hoeft niet zo, eigenlijk*"),
        ],
    },
    "toekomst": {
        "label": "🔮 Toekomst",
        "questions": [
            ("Waar zie jij jezelf over vijf jaar?", "Probeer: *moeilijk te zeggen, op weg naar, mee bezig, hoop op*"),
            ("Is er iets wat je echt wilt bereiken in je leven?", "Probeer: *drijfveer, blijf op terugkomen, geef het niet op, ooit nog*"),
            ("Plan je liever vooruit of neem je het zoals het komt?", "Probeer: *structuur nodig, meegaan met de stroom, hangt ervan af, mix van beide*"),
            ("Is er iets wat je wilt leren of doen voor een bepaalde leeftijd?", "Probeer: *voor ik te oud ben, altijd gezegd dat ik zou, geen excuses meer*"),
            ("Ben je optimistisch of realistisch over de toekomst?", "Probeer: *voorzichtig, neig ik naar, probeer het te zijn, niet altijd*"),
            ("Hoe wil je leven over tien jaar?", "Probeer: *stel me voor, werk naartoe, eerlijk gezegd niet zeker, telt het meest*"),
            ("Is er iets wat je nu tegenhoudt om een doel te bereiken?", "Probeer: *aarzelen, praktische redenen, angst voor, wachten op het juiste moment*"),
            ("Denk je na over de impact die je wilt hebben op anderen?", "Probeer: *achterlaten, op kleine manieren, niet iets wat ik, belangrijk voor me*"),
            ("Wat betekent succes voor jou persoonlijk?", "Probeer: *niet om het geld, gevoel van, op jouw eigen voorwaarden, verandert met de tijd*"),
            ("Wat zou je jezelf als kind willen meegeven?", "Probeer: *had ik gewild, te serieus genomen, loslaten, eerder geweten*"),
        ],
    },
}


# =====================
# CAROUSEL VIEW
# =====================

class TopicCarouselView(discord.ui.View):
    def __init__(
        self,
        *,
        topic_key: str,
        questions: list[tuple[str, str]],
        topic_label: str,
        index: int = 0,
        is_nl: bool = False,
    ) -> None:
        super().__init__(timeout=600)
        self.topic_key = topic_key
        self.questions = questions
        self.topic_label = topic_label
        self.index = index
        self.is_nl = is_nl
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.clear_items()
        total = len(self.questions)

        prev_btn = discord.ui.Button(
            label="◀",
            style=discord.ButtonStyle.secondary,
            disabled=(self.index == 0),
            custom_id="topic:prev",
            row=0,
        )
        counter_btn = discord.ui.Button(
            label=f"{self.index + 1} / {total}",
            style=discord.ButtonStyle.secondary,
            disabled=True,
            custom_id="topic:counter",
            row=0,
        )
        next_btn = discord.ui.Button(
            label="▶",
            style=discord.ButtonStyle.secondary,
            disabled=(self.index == total - 1),
            custom_id="topic:next",
            row=0,
        )

        prev_btn.callback = self._prev
        next_btn.callback = self._next

        self.add_item(prev_btn)
        self.add_item(counter_btn)
        self.add_item(next_btn)

    def build_embed(self) -> discord.Embed:
        question, vocab_tip = self.questions[self.index]
        total = len(self.questions)
        label = "Vraag" if self.is_nl else "Question"
        vocab_label = "Handige woorden" if self.is_nl else "Useful vocabulary"

        embed = discord.Embed(
            title=f"{self.topic_label} — {label} {self.index + 1}/{total}",
            description=f"**{question}**",
        )
        embed.add_field(name=vocab_label, value=vocab_tip, inline=False)
        return embed

    async def _prev(self, interaction: discord.Interaction) -> None:
        self.index = max(0, self.index - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _next(self, interaction: discord.Interaction) -> None:
        self.index = min(len(self.questions) - 1, self.index + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


# =====================
# TOPIC PICKER VIEW
# =====================

def _build_topic_picker(topics: dict, is_nl: bool) -> discord.ui.View:
    view = discord.ui.View(timeout=120)
    pick_label = "Kies een onderwerp" if is_nl else "Pick a topic"

    options = [
        discord.SelectOption(label=info["label"], value=key)
        for key, info in topics.items()
    ]

    select = discord.ui.Select(
        placeholder=pick_label,
        options=options,
        min_values=1,
        max_values=1,
    )

    async def on_select(interaction: discord.Interaction) -> None:
        key = select.values[0]
        topic = topics[key]
        carousel = TopicCarouselView(
            topic_key=key,
            questions=topic["questions"],
            topic_label=topic["label"],
            index=0,
            is_nl=is_nl,
        )
        await interaction.response.edit_message(
            content=None,
            embed=carousel.build_embed(),
            view=carousel,
        )

    select.callback = on_select
    view.add_item(select)
    return view


# =====================
# COG
# =====================

class TopicsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="topics",
        description="Pick a speaking topic and get 10 conversation questions.",
    )
    async def topics(self, interaction: discord.Interaction) -> None:
        view = _build_topic_picker(EN_TOPICS, is_nl=False)
        await interaction.response.send_message(
            "Pick a topic to get started:",
            view=view,
        )

    @app_commands.command(
        name="onderwerpen",
        description="Kies een spreekonderwerp en krijg 10 gespreksvragen.",
    )
    async def onderwerpen(self, interaction: discord.Interaction) -> None:
        view = _build_topic_picker(NL_TOPICS, is_nl=True)
        await interaction.response.send_message(
            "Kies een onderwerp om te beginnen:",
            view=view,
        )


async def setup(bot: commands.Bot, *, guild_id: int, dutch_guild_id: int | None = None) -> None:
    cog = TopicsCog(bot)
    await bot.add_cog(cog)
    log.info("TopicsCog loaded.")
