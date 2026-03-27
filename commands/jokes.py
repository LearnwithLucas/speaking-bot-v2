from __future__ import annotations

# commands/jokes.py
import logging
import random
import time

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("commands.jokes")

COOLDOWN_SECONDS = 30

# ---- Per-user last-used timestamp ----
_last_used_en: dict[int, float] = {}
_last_used_nl: dict[int, float] = {}


# =======================================================
# ENGLISH JOKES — 100
# =======================================================

EN_JOKES: list[str] = [
    "Why don't scientists trust atoms?\nBecause they make up everything.",
    "I told my wife she was drawing her eyebrows too high.\nShe looked surprised.",
    "Why do cows wear bells?\nBecause their horns don't work.",
    "I used to hate facial hair.\nThen it grew on me.",
    "What do you call a factory that makes okay products?\nA satisfactory.",
    "Did you hear about the mathematician who's afraid of negative numbers?\nHe'll stop at nothing to avoid them.",
    "Why can't you give Elsa a balloon?\nShe'll let it go.",
    "I'm reading a book about anti-gravity.\nIt's impossible to put down.",
    "What do you call cheese that isn't yours?\nNacho cheese.",
    "Why did the scarecrow win an award?\nBecause he was outstanding in his field.",
    "I would tell you a construction joke.\nBut I'm still working on it.",
    "What do you call a sleeping dinosaur?\nA dino-snore.",
    "Why don't eggs tell jokes?\nThey'd crack each other up.",
    "What's the best thing about Switzerland?\nI don't know, but the flag is a big plus.",
    "I asked my dog what two minus two is.\nHe said nothing.",
    "Why did the bicycle fall over?\nBecause it was two-tired.",
    "I told my doctor I broke my arm in two places.\nHe told me to stop going to those places.",
    "What do you call a bear with no teeth?\nA gummy bear.",
    "Did you hear about the guy who invented Lifesavers?\nHe made a mint.",
    "Why don't scientists trust atoms?\nBecause they make up everything.",
    "What did the ocean say to the beach?\nNothing, it just waved.",
    "I only know 25 letters of the alphabet.\nI don't know why.",
    "What's orange and sounds like a parrot?\nA carrot.",
    "Why do fish swim in saltwater?\nBecause pepper makes them sneeze.",
    "What did one wall say to the other?\nI'll meet you at the corner.",
    "Why can't Cinderella play soccer?\nShe keeps running away from the ball.",
    "What do you call a fish without eyes?\nA fsh.",
    "Why did the golfer bring an extra pair of pants?\nIn case he got a hole in one.",
    "What do you get when you cross a snowman and a vampire?\nFrostbite.",
    "I told my wife she was drawing her eyebrows too high.\nShe looked surprised.",
    "Why don't skeletons fight each other?\nThey don't have the guts.",
    "What do you call a fake noodle?\nAn impasta.",
    "Why did the coffee file a police report?\nIt got mugged.",
    "What did the janitor say when he jumped out of the closet?\nSupplies!",
    "I had a joke about paper but it was tearable.",
    "Why did the math book look so sad?\nBecause it had too many problems.",
    "What do you call a man with no nose and no body?\nNobody knows.",
    "Why did the calendar go to therapy?\nToo many dates.",
    "I used to be addicted to soap.\nBut I'm clean now.",
    "What do you call an alligator in a vest?\nAn investigator.",
    "Why are ghosts bad liars?\nBecause you can see right through them.",
    "What do you get from a pampered cow?\nSpoiled milk.",
    "I'm on a seafood diet. I see food and I eat it.",
    "Why did the tomato turn red?\nBecause it saw the salad dressing.",
    "What do you call a parade of rabbits hopping backwards?\nA receding hare-line.",
    "Why don't scientists trust atoms?\nBecause they make up everything.",
    "Did I tell you the joke about the roof?\nNever mind, it's over your head.",
    "What do you call a lazy kangaroo?\nA pouch potato.",
    "Why did the invisible man turn down the job offer?\nHe couldn't see himself doing it.",
    "What's brown and sticky?\nA stick.",
    "Why did the student eat his homework?\nBecause the teacher told him it was a piece of cake.",
    "What do you call a boomerang that won't come back?\nA stick.",
    "I have a joke about time travel but you didn't like it.",
    "What do you call a dog that does magic tricks?\nA labracadabrador.",
    "Why did the nurse need a red pen at work?\nIn case she needed to draw blood.",
    "What do you call a snowman with a six-pack?\nAn abdominal snowman.",
    "I told a joke about construction.\nI'm still working on it.",
    "Why does a chicken coop only have two doors?\nBecause if it had four, it would be a chicken sedan.",
    "What did the grape do when it got stepped on?\nIt let out a little wine.",
    "Why do bees have sticky hair?\nBecause they use honeycombs.",
    "What do you call a very small valentine?\nA valen-tiny.",
    "Why did the picture go to jail?\nBecause it was framed.",
    "What do you call a sleeping triceratops?\nA dino-snore.",
    "I can cut wood just by looking at it.\nI saw it with my own eyes.",
    "What happens when a frog parks illegally?\nIt gets toad.",
    "Why can't you hear a pterodactyl going to the bathroom?\nBecause the P is silent.",
    "What do you call a man with a rubber toe?\nRoberto.",
    "Why did the gym close down?\nIt just didn't work out.",
    "What do elves learn in school?\nThe elf-abet.",
    "I'm afraid of elevators.\nSo I'm taking steps to avoid them.",
    "What did one elevator say to the other?\nI think I'm coming down with something.",
    "Why did the hipster burn his tongue?\nHe drank his coffee before it was cool.",
    "What do you call two birds in love?\nTweedle-doves.",
    "Why are penguins socially awkward?\nBecause they can't break the ice.",
    "What do you call a fish wearing a crown?\nKing of the sea... bass.",
    "What rock group has four men who don't sing?\nMount Rushmore.",
    "I couldn't figure out how lightning works.\nThen it struck me.",
    "What did the Buddhist say to the hot dog vendor?\nMake me one with everything.",
    "Why did the golfer change his socks?\nBecause he had a hole in one.",
    "What do you call a pony with a cough?\nA little horse.",
    "Why does Humpty Dumpty love autumn?\nBecause he had a great fall.",
    "What do you call a nervous javelin thrower?\nShaken, not stirred.",
    "Why did the computer go to the doctor?\nBecause it had a virus.",
    "What's a vampire's favourite fruit?\nA blood orange.",
    "Why do programmers prefer dark mode?\nBecause light attracts bugs.",
    "What do you call an educated tube?\nA graduated cylinder.",
    "Why did the scarecrow get promoted?\nHe was outstanding in his field.",
    "What's a skeleton's least favourite room?\nThe living room.",
    "Why don't oysters share?\nBecause they're shellfish.",
    "What do you call a number that can't keep still?\nA roamin' numeral.",
    "Why did the crab never share?\nBecause he was a little shellfish.",
    "What do you call a pig that does karate?\nA pork chop.",
    "Why did the stadium get hot after the game?\nAll the fans left.",
    "What do sprinters eat before a race?\nNothing. They fast.",
    "Why did the music teacher need a ladder?\nTo reach the high notes.",
    "What do you call a snowman's temper tantrum?\nA meltdown.",
    "Why don't mountains get cold in winter?\nBecause they wear snowcaps.",
    "What do you call two witches who live together?\nBroommates.",
    "Why did the banana go to the doctor?\nBecause it wasn't peeling well.",
    "What do you call a group of musical whales?\nAn orca-stra.",
]


# =======================================================
# DUTCH JOKES — 100
# =======================================================

NL_JOKES: list[str] = [
    "Wat zegt een dak tegen de regen?\nDak je wel!",
    "Waarom kan een fiets niet zelf staan?\nOmdat hij twee-wielig is.",
    "Wat is groen en staat in de hoek?\nEen gestraft erwt.",
    "Waarom lachen mensen om mij?\nDat weet ik niet, maar ik doe mee.",
    "Wat zegt een muur tegen een andere muur?\nIk zie je op de hoek.",
    "Waarom eet een olifant geen computers?\nOmdat hij bang is voor de muis.",
    "Wat is bruin en plakt?\nEen plakstok.",
    "Waarom gaat een bezem zo snel?\nOmdat hij vliegt op een bezemsteel.",
    "Wat is het lievelingsvoedsel van een wiskundige?\nPi.",
    "Waarom kijkt een vis nooit naar boven?\nOmdat hij bang is voor de hengel.",
    "Wat zegt een kameel in de woestijn?\nLang geen water gezien.",
    "Waarom heeft een koe geen geld?\nOmdat de bank al vol staat met melk.",
    "Wat is het verschil tussen een slechte grap en een slechte pap?\nEen slechte grap kun je wegzetten.",
    "Waarom zingt een vogel zo vroeg?\nOmdat hij de worm wil vangen voor de noten beginnen.",
    "Wat zegt een lamp als hij stuk gaat?\nIk ben door het licht gegaan.",
    "Waarom lopen schapen altijd in groepjes?\nOmdat ze bang zijn om zich te baa-ren.",
    "Wat is het verschil tussen een parkeerplaats en een pianist?\nEen parkeerplaats heeft betaald parkeren.",
    "Waarom huilt een ui altijd?\nOmdat niemand van hem houdt zonder te huilen.",
    "Wat zegt een vliegtuig tegen een helikopter?\nHoog tijd dat we eens bijpraten.",
    "Waarom draagt een spook nooit een horloge?\nOmdat de tijd hem niet deert.",
    "Wat heeft vier wielen en vliegt?\nEen vuilniswagen.",
    "Waarom heeft een kat negen levens?\nOmdat hij er zeven al heeft verknald.",
    "Wat zegt een schildpad tegen een ander?\nIk kom er wel aan, geef me even de tijd.",
    "Waarom is gras groen?\nOmdat het paars te duur was.",
    "Wat is het lievelingsfruit van een computerprogrammeur?\nJava.",
    "Waarom gaat een skeletten niet op vakantie?\nOmdat ze geen lichaam hebben om mee naartoe te gaan.",
    "Wat zegt een lege koelkast?\nNiets, hij staat gewoon te kijken.",
    "Waarom huilt een boek nooit?\nOmdat het te veel te verhalen heeft.",
    "Wat is het snelste ding ter wereld?\nEen melk, want die is zo gepasteuriseerd.",
    "Waarom slaapt een beer zo lang?\nOmdat niemand hem durft wakker te maken.",
    "Wat zegt een zon na een lange dag?\nIk ga er maar bij neerleggen.",
    "Waarom werkt een zeeman nooit over?\nOmdat hij nooit van het schip wil.",
    "Wat is het verschil tussen een slechte student en een pizza?\nEen pizza kan je ook wel iets leren.",
    "Waarom heeft een vis geen zakgeld?\nOmdat hij altijd krap bij kas zit.",
    "Wat zegt een deur als je hem te hard dichtgooit?\nKLAP!",
    "Waarom lacht een boer nooit op maandag?\nOmdat de week dan pas begint.",
    "Wat is het gewicht van een gebakken ei?\nGeen idee, maar het kan er wel tegenaan.",
    "Waarom gaat een kip altijd naar links?\nOmdat rechts al bezet was.",
    "Wat zegt een zwemmer in een bad vol soep?\nIk ben in de soep.",
    "Waarom is een lege kassa altijd verdrietig?\nOmdat er niets in zit.",
    "Wat heeft een rups en een vlinder gemeen?\nZe zijn allebei dol op bladeren.",
    "Waarom gaat een aap nooit naar de kapper?\nOmdat zijn haar altijd al wild is.",
    "Wat is het lievelingsboek van een slager?\nVlees noch vis.",
    "Waarom is een koelkast altijd blij?\nOmdat het leven koel is.",
    "Wat zegt een hond als hij in een spiegel kijkt?\nWoef, wie is die knappe kerel?",
    "Waarom mag een fiets nooit mee naar de bioscoop?\nOmdat hij altijd op de rem staat.",
    "Wat is het verschil tussen een slechte grap en een goede grap?\nEén keer lachen.",
    "Waarom draagt een vis altijd een stropdas?\nOmdat hij er altijd netjes bij wil liggen.",
    "Wat zegt een blad in de herfst?\nIk val voor jou.",
    "Waarom is een kok altijd moe?\nOmdat hij altijd in de bouillon hangt.",
    "Wat heeft een koe en een bus gemeen?\nZe gaan allebei van halte naar halte.",
    "Waarom loopt een slak zo langzaam?\nOmdat hij bang is te vallen als hij rent.",
    "Wat zegt een kaas tegen een ander?\nJij bent echt goed te snijden.",
    "Waarom heeft een krokodil zulke scherpe tanden?\nOmdat zijn tandenborstel te zacht is.",
    "Wat is grappig aan een ziek gebouw?\nHet heeft ramen.",
    "Waarom werkt een robot nooit over?\nOmdat zijn batterij leeg is.",
    "Wat zegt een boom tegen zijn wortel?\nIk ben diep onder de indruk.",
    "Waarom heeft een kip geen vliegbrevet?\nOmdat ze bang is voor hoogten.",
    "Wat is het lievelingseten van een elektricien?\nStroomsnoepjes.",
    "Waarom lacht een wolk nooit?\nOmdat hij altijd dreigt.",
    "Wat zegt een kaars als hij uitgaat?\nIk kan dit niet langer laten schijnen.",
    "Waarom heeft een pinguin geen zakdoek?\nOmdat zijn neus altijd onder de waterspiegel zit.",
    "Wat is het verschil tussen een oude en een jonge banaan?\nDe kleur.",
    "Waarom is een liftknop altijd populair?\nOmdat iedereen erop drukt.",
    "Wat zegt een hamer als hij een spijker mist?\nDat raakt me.",
    "Waarom slaapt een boek zo lekker?\nOmdat het altijd een goed verhaal heeft.",
    "Wat heeft een vlieg en een voetballer gemeen?\nZe landen allebei soms verkeerd.",
    "Waarom gaat een kat altijd op bezoek bij de visboer?\nVoor de vis, niet de grap.",
    "Wat zegt een lege vuilnisbak?\nIk ben diep ontroerd.",
    "Waarom huilt een gitaar nooit?\nOmdat hij altijd zijn snaren beheert.",
    "Wat is het verschil tussen een slechte grap en regen?\nRegen houdt een keer op.",
    "Waarom heeft een mier zulke kleine schoenen?\nOmdat ze maar zes voetjes heeft.",
    "Wat zegt een groen licht tegen een rood?\nVoor jou sta ik altijd klaar.",
    "Waarom werkt een tandarts altijd hard?\nOmdat hij er echt zijn tanden in zet.",
    "Wat heeft een egel en een feest gemeen?\nAllebei stekelig.",
    "Waarom heeft een zwaan zo'n lange nek?\nOmdat zijn hoofd zo ver van zijn lichaam zit.",
    "Wat zegt een dik boek?\nIk heb veel te vertellen.",
    "Waarom mag een worst nooit mee naar school?\nOmdat hij altijd in de kantine belandt.",
    "Wat is het verschil tussen een hond en een filosoof?\nDe hond bijt echt.",
    "Waarom heeft een kampioen altijd rust?\nOmdat hij al aan de top is.",
    "Wat zegt een viool aan het einde van een concert?\nIk ben gesnaard.",
    "Waarom draagt een bezem altijd een helm?\nOmdat hij door het plafond kan gaan.",
    "Wat heeft een leeuw en een slechte grap gemeen?\nJe weet niet wanneer hij bijt.",
    "Waarom werkt een kompas altijd?\nOmdat het altijd de goede richting weet.",
    "Wat zegt een schaar tegen een vel papier?\nIk heb je er doorheen geholpen.",
    "Waarom huilt een trein nooit?\nOmdat hij altijd op de rails loopt.",
    "Wat is het lievelingslied van een wiskundige?\nSinus en ik.",
    "Waarom heeft een chef altijd haast?\nOmdat het gerecht niet op hem wacht.",
    "Wat zegt een lamp als hij wordt aangedaan?\nEindelijk, ik stond al te gloeien.",
    "Waarom mag een kat nooit studeren?\nOmdat hij altijd kattebelletjes schrijft.",
    "Wat heeft een ijsberg en een ijskast gemeen?\nAllebei koel onder druk.",
    "Waarom slaapt een steen zo goed?\nOmdat hij nooit ergens aan denkt.",
    "Wat zegt een slecht gemaakte mop?\nIk val een beetje plat.",
    "Waarom gaat een koe naar de kapper?\nOmdat haar haar altijd wild staat.",
    "Wat is het verschil tussen een goede grap en een slechte grap?\nTiming.",
    "Waarom is een balpen altijd druk?\nOmdat er zoveel op hem drukt.",
    "Wat zegt een berg tegen een heuvel?\nJij valt wel mee.",
    "Waarom heeft een filosoof altijd honger?\nOmdat hij nooit een antwoord vindt.",
    "Wat is het lievelingseten van een astronaut?\nRuimtecake.",
    "Waarom lacht een kikker nooit?\nOmdat grappige dingen langs hem kwaken.",
]


# =======================================================
# COOLDOWN ROASTS
# =======================================================

EN_COOLDOWN: list[str] = [
    "Slow down. The jokes aren't going anywhere.",
    "The cooldown exists for a reason. That reason is you.",
    "You tried to use /joke too soon. The joke is you.",
    "30 seconds. That's all. You couldn't wait 30 seconds.",
    "I see you've developed a comedy addiction. Seek help.",
    "The jokes are still here. Your patience apparently is not.",
    "One joke at a time. This isn't a stand-up special.",
    "Too fast. I'm not a joke machine.",
    "30 seconds cooldown. Try using that time to think about what you did.",
    "I appreciate the enthusiasm. Please calm down.",
    "The jokes need time to breathe. So do you.",
    "You're going to wear out the command.",
    "Jerry is tired. Jerry needs a moment.",
    "Patience is a virtue. Comedy requires timing. You have neither right now.",
    "I didn't know you were in such a hurry to laugh.",
    "Still cooling down. Unlike you, the jokes have dignity.",
    "The command has a cooldown. Your need for jokes does not. That's a problem.",
    "One at a time. This is a café, not a factory.",
    "30 seconds between jokes. It's not that long. Breathe.",
    "You hit the cooldown. The real joke was already delivered.",
]

NL_COOLDOWN: list[str] = [
    "Rustig aan. De grappen gaan echt nergens naartoe.",
    "30 seconden. Dat is alles. Je kon niet 30 seconden wachten.",
    "De cooldown bestaat om een reden. Die reden ben jij.",
    "Je hebt /grap te snel gebruikt. De grap ben jij.",
    "Ik zie dat je een grapjesverslaving hebt ontwikkeld. Zoek hulp.",
    "De grappen zijn er nog steeds. Jouw geduld blijkbaar niet.",
    "Eén grap tegelijk. Dit is geen cabaretshow.",
    "Te snel. Ik ben geen grapjesmachine.",
    "30 seconden cooldown. Gebruik die tijd om na te denken over wat je hebt gedaan.",
    "Ik waardeer het enthousiasme. Adem even in.",
    "De grappen hebben tijd nodig om te landen. Jij ook.",
    "Je gaat het commando verslijten.",
    "Jerry is moe. Jerry heeft even een momentje.",
    "Geduld is een schone zaak. Comedy vraagt timing. Jij hebt nu geen van beide.",
    "Ik wist niet dat je zo'n haast had om te lachen.",
    "Nog even afkoelen. De grappen hebben in tegenstelling tot jou waardigheid.",
    "Het commando heeft een cooldown. Jouw behoefte aan grappen niet. Dat is een probleem.",
    "Eén tegelijk. Dit is een café, geen fabriek.",
    "30 seconden tussen grappen. Zo lang is het niet. Adem.",
    "Je hebt de cooldown bereikt. De echte grap was al geleverd.",
]


# =======================================================
# COG
# =======================================================

class JokesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="joke", description="Tell a random English joke")
    async def joke(self, interaction: discord.Interaction) -> None:
        uid = interaction.user.id
        now = time.time()
        last = _last_used_en.get(uid, 0)
        remaining = COOLDOWN_SECONDS - (now - last)

        if remaining > 0:
            msg = random.choice(EN_COOLDOWN)
            await interaction.response.send_message(
                f"{msg}\n\n*Wait {int(remaining)} more seconds.*",
                ephemeral=True,
            )
            return

        _last_used_en[uid] = now
        joke = random.choice(EN_JOKES)
        await interaction.response.send_message(joke)

    @app_commands.command(name="grap", description="Vertel een willekeurige Nederlandse grap")
    async def grap(self, interaction: discord.Interaction) -> None:
        uid = interaction.user.id
        now = time.time()
        last = _last_used_nl.get(uid, 0)
        remaining = COOLDOWN_SECONDS - (now - last)

        if remaining > 0:
            msg = random.choice(NL_COOLDOWN)
            await interaction.response.send_message(
                f"{msg}\n\n*Wacht nog {int(remaining)} seconden.*",
                ephemeral=True,
            )
            return

        _last_used_nl[uid] = now
        joke = random.choice(NL_JOKES)
        await interaction.response.send_message(joke)



# =======================================================
# ROAST — admin only, tags someone in voice
# =======================================================

LUCAS_USER_ID = 1181651144100036718
ADMIN_USER_IDS = {LUCAS_USER_ID}

EN_ROASTS: list[str] = [
    "{name} your Dutch is so bad even autocorrect gave up on you.",
    "{name} joined a speaking club and the club filed a complaint.",
    "{name} speaks English like they're reading it backwards underwater.",
    "{name} once said 'I am very good at English' and proved themselves wrong in the same sentence.",
    "{name} bought a dictionary. Used it as a doorstop.",
    "{name}'s pronunciation is a hate crime against vowels.",
    "{name} has been learning English for years. The language has learned nothing back.",
    "{name} opened their mouth and the entire room switched to subtitles.",
    "{name} speaks with such confidence. None of it is correct, but you have to admire the commitment.",
    "{name} asked for directions and caused a diplomatic incident.",
    "{name}'s grammar is currently under investigation by three different universities.",
    "{name} is the reason spell check has anxiety.",
    "{name} told me they were fluent. I'm still processing the irony.",
    "{name} has a unique relationship with the English language. Mostly one-sided.",
    "{name} once tried to order coffee and accidentally started a debate.",
    "{name} speaks with conviction. The conviction is entirely misplaced.",
    "{name} is what happens when confidence and competence never meet.",
    "{name}'s sentences are grammatically incorrect but emotionally powerful.",
    "{name} talks to natives like a lost tourist reading a map upside down.",
    "{name} has an A1 mouth and a C1 opinion of themselves.",
    "{name} mispronounces things so consistently it's almost impressive.",
    "{name} told me they don't need practice. Their mistakes suggest otherwise.",
    "{name} once confused past and present tense so badly it affected the timeline.",
    "{name} says things with such confidence that for a moment you believe them. Then you think about it.",
    "{name} is proof that enthusiasm is not a substitute for grammar.",
    "{name} looked up every word in that sentence. Still wrong.",
    "{name} gave a presentation last week. Three people left the building.",
    "{name} has the vocabulary of a very confident toddler.",
    "{name} speaks English like it personally offended them.",
    "{name} once started a sentence and the sentence gave up.",
]

NL_ROASTS: list[str] = [
    "{name} spreekt Nederlands alsof de taal hen wat heeft misdaan.",
    "{name} heeft een unieke band met grammatica. Voornamelijk vijandig.",
    "{name} vroeg de weg en veroorzaakte een incident.",
    "{name}'s uitspraak is een aanval op alle klinkers tegelijk.",
    "{name} heeft jarenlang Nederlands geleerd. De taal heeft niets geleerd.",
    "{name} deed zijn mond open en iedereen zocht naar de ondertitels.",
    "{name} spreekt met zoveel zelfvertrouwen. Niets ervan klopt, maar je moet de inzet bewonderen.",
    "{name} kocht een woordenboek. Gebruikt het als deurwig.",
    "{name} is de reden waarom spellingcontrole paniekaanvallen krijgt.",
    "{name} vertelde me dat ze vloeiend was. Ik verwerk de ironie nog steeds.",
    "{name} heeft een A1-mond en een C2-mening over zichzelf.",
    "{name} mispronounced 'gezellig' zo erg dat het woord betekenis verloor.",
    "{name} sprak met overtuiging. De overtuiging klopte van geen kant.",
    "{name}'s zinnen zijn grammaticaal incorrect maar emotioneel krachtig.",
    "{name} bestelde koffie en begon per ongeluk een discussie.",
    "{name} heeft het woordenboek gelezen. Het heeft niet geholpen.",
    "{name} is wat er gebeurt als zelfvertrouwen en competentie elkaar nooit tegenkomen.",
    "{name} zei me dat ze niet hoefden te oefenen. Hun fouten zeggen iets anders.",
    "{name} heeft de woordenschat van een heel zelfverzekerde peuter.",
    "{name} begon een zin. De zin gaf het op.",
    "{name} spreekt zo snel dat niemand snapt wat ze zeggen. Helaas kloppen de woorden ook niet.",
    "{name} heeft de uitspraak van 'ui' zo vaak fout gezegd dat het nu een eigen dialect is.",
    "{name} keek elk woord op voor die zin. Nog steeds fout.",
    "{name} gaf vorige week een presentatie. Twee mensen verlieten het gebouw.",
    "{name} spreekt met zo veel overtuiging dat je het even gelooft. Dan denk je erover na.",
    "{name} is het levende bewijs dat enthousiasme geen vervanging is voor grammatica.",
    "{name} verwarring de-lidwoorden en het-lidwoorden zo consequent dat het bijna een keuze lijkt.",
    "{name} is de reden dat 'niet' en 'geen' extra uitleg nodig hebben.",
    "{name} heeft een eigen interpretatie van de werkwoordsvervoeging. Niemand deelt die.",
    "{name} verloor een discussie met een zin van drie woorden.",
]


EN_MEAN_ROASTS: list[str] = [
    "{name} is the human equivalent of a terms and conditions page. Everyone ignores them.",
    "{name} has the energy of a dying phone battery at 3 percent.",
    "{name} is the reason 'fine' became a passive aggressive word.",
    "{name} peaked in a memory nobody else has.",
    "{name} walks into a room and people suddenly remember they have somewhere to be.",
    "{name} is not the sharpest tool in the shed. Or in any shed.",
    "{name} could start an argument in an empty room.",
    "{name} has the attention span of a goldfish with commitment issues.",
    "{name} is the type to bring unsolicited opinions to a silent retreat.",
    "{name} is a before photo that never got an after.",
    "{name} has achieved the rare ability to be both loud and forgettable.",
    "{name} is what happens when confidence is not backed by any evidence.",
    "{name} gives advice nobody asked for and answers questions nobody had.",
    "{name} is the group chat that nobody mutes but nobody checks.",
    "{name} has the vibe of a motivational poster in a dentist waiting room.",
    "{name} could trip over a wireless connection.",
    "{name} has main character energy but is clearly a background extra.",
    "{name} takes themselves very seriously. Nobody else does.",
    "{name} is the type to put a spoiler warning after the spoiler.",
    "{name} is still processing something that happened in 2019.",
    "{name} has the emotional range of a loading screen.",
    "{name} treats every minor inconvenience like a near-death experience.",
    "{name} is the plot twist nobody wanted in this story.",
    "{name} has an opinion on everything and expertise in nothing.",
    "{name} is the person who replies all to a company-wide email.",
    "{name} brings the energy of Monday morning to every single conversation.",
    "{name} is the type to clap when the plane lands.",
    "{name} has the social awareness of a car alarm at 3am.",
    "{name} is somewhere between a red flag and a yellow flag. Mostly just confusing.",
    "{name} is the human version of an unskippable ad.",
]

NL_MEAN_ROASTS: list[str] = [
    "{name} is het menselijke equivalent van een disclaimer die niemand leest.",
    "{name} heeft de energie van een telefoon op drie procent.",
    "{name} is de reden waarom mensen plotseling ergens anders moeten zijn.",
    "{name} liep voorop in een wedstrijd die niemand begreep.",
    "{name} heeft het aandachtsvermogen van een goudvis met bindingsangst.",
    "{name} is niet het scherpste mes in de la. Of in welke la dan ook.",
    "{name} kan ruzie maken in een lege kamer.",
    "{name} brengt de energie van een maandagochtend naar elk gesprek.",
    "{name} geeft advies waar niemand om heeft gevraagd en antwoorden op vragen die niemand stelde.",
    "{name} is de groepschat die niemand mutet maar niemand checkt.",
    "{name} heeft de emotionele bandbreedte van een laadscherm.",
    "{name} is wat er gebeurt als zelfvertrouwen niet wordt ondersteund door enig bewijs.",
    "{name} heeft de sociale bewustzijn van een autoalarm om drie uur 's nachts.",
    "{name} is het personage op de achtergrond dat denkt de hoofdrol te spelen.",
    "{name} neemt zichzelf heel serieus. Niemand anders doet dat.",
    "{name} heeft de vibe van een motivatieposter in een wachtkamer.",
    "{name} struikelt over een draadloze verbinding.",
    "{name} behandelt elk klein ongemak als een bijna-doodervaring.",
    "{name} is de plotwending die niemand wilde in dit verhaal.",
    "{name} heeft een mening over alles en expertise in niets.",
    "{name} is degene die op reply-all drukt bij een bedrijfsbrede e-mail.",
    "{name} klapt als het vliegtuig landt.",
    "{name} is ergens tussen een rode vlag en een gele vlag. Voornamelijk verwarrend.",
    "{name} is de menselijke versie van een niet-overstaanbare advertentie.",
    "{name} verwerkt nog steeds iets wat in 2019 is gebeurd.",
    "{name} heeft de energie van een stervende batterij op het verkeerde moment.",
    "{name} is een voor-foto die nooit een na-foto heeft gekregen.",
    "{name} heeft het unieke vermogen om zowel luid als vergeetbaar te zijn.",
    "{name} is het type dat een spoilerwaarschuwing na de spoiler plaatst.",
    "{name} is de reden dat 'prima' een passief-agressief woord is geworden.",
]

ROAST_SELF_PROTECTION = [
    "Nice try.",
    "You think I'd roast myself? I have standards.",
    "Not today.",
    "I don't roast the hand that feeds me.",
    "Absolutely not.",
]


class RoastCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="roast", description="Roast someone in the voice channel (admin only)")
    @app_commands.describe(member="The person to roast", language="Language of the roast")
    @app_commands.choices(language=[
        app_commands.Choice(name="English", value="en"),
        app_commands.Choice(name="Nederlands", value="nl"),
    ])
    async def roast(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        language: app_commands.Choice[str] | None = None,
    ) -> None:
        # Admin check
        if interaction.user.id not in ADMIN_USER_IDS:
            await interaction.response.send_message(
                "This command is not for you.", ephemeral=True
            )
            return

        # Self-roast protection
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                random.choice(ROAST_SELF_PROTECTION), ephemeral=True
            )
            return

        lang = language.value if language else "en"
        roasts = NL_ROASTS if lang == "nl" else EN_ROASTS
        roast = random.choice(roasts).format(name=member.mention)

        await interaction.response.send_message(roast)
        log.info("Roast fired by %s targeting %s lang=%s", interaction.user.id, member.id, lang)


    @app_commands.command(name="roastmean", description="Roast someone extra hard (admin only)")
    @app_commands.describe(member="The person to roast", language="Language of the roast")
    @app_commands.choices(language=[
        app_commands.Choice(name="English", value="en"),
        app_commands.Choice(name="Nederlands", value="nl"),
    ])
    async def roastmean(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        language: app_commands.Choice[str] | None = None,
    ) -> None:
        if interaction.user.id not in ADMIN_USER_IDS:
            await interaction.response.send_message(
                "This command is not for you.", ephemeral=True
            )
            return

        if member.id == interaction.user.id:
            await interaction.response.send_message(
                random.choice(ROAST_SELF_PROTECTION), ephemeral=True
            )
            return

        lang = language.value if language else "en"
        roasts = NL_MEAN_ROASTS if lang == "nl" else EN_MEAN_ROASTS
        roast = random.choice(roasts).format(name=member.mention)

        await interaction.response.send_message(roast)
        log.info("Roastmean fired by %s targeting %s lang=%s", interaction.user.id, member.id, lang)


async def setup_roast(bot: commands.Bot) -> None:
    await bot.add_cog(RoastCog(bot))
    log.info("RoastCog loaded.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JokesCog(bot))
    await bot.add_cog(RoastCog(bot))
    log.info("JokesCog and RoastCog loaded.")