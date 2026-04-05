from __future__ import annotations

# commands/testimonials.py
import logging
from typing import Any

import discord
from discord.ext import commands

log = logging.getLogger("commands.testimonials")

# ---- Channel IDs ----
EN_SUCCESS_CHANNEL_ID = 1490320758507962490
NL_SUCCESS_CHANNEL_ID = 1490320826027741185
EN_COLLECTED_CHANNEL_ID = 1490322440788644011
NL_COLLECTED_CHANNEL_ID = 1490322080678543542

LUCAS_USER_ID = 1181651144100036718

KV_EN_HUB_MSG = "testimonial_hub_en_v2"
KV_NL_HUB_MSG = "testimonial_hub_nl_v2"

# ---- Questions (labels must be <=45 chars) ----
EN_QUESTIONS = [
    "What are you proud of since joining?",
    "How has practicing here helped you?",
    "How would you describe your progress?",
    "Anything else you'd like to add?",
]
EN_PLACEHOLDERS = [
    "What's one thing you're proud of since joining?",
    "How has practicing here helped you?",
    "If you were telling a friend, how would you describe your progress?",
    "Optional — any other thoughts, moments or people you'd like to mention?",
]

NL_QUESTIONS = [
    "Waar ben je trots op sinds je lid bent?",
    "Hoe heeft oefenen hier jou geholpen?",
    "Hoe zou je jouw vooruitgang omschrijven?",
    "Nog iets anders dat je wilt toevoegen?",
]
NL_PLACEHOLDERS = [
    "Wat is iets waar je trots op bent sinds je lid bent geworden?",
    "Hoe heeft het oefenen hier jou geholpen?",
    "Als je het aan een vriend zou vertellen, hoe zou je je vooruitgang omschrijven?",
    "Optioneel — andere gedachten, momenten of mensen die je wilt noemen?",
]

# ---- Connectors — 3 sets, rotated by user ID for variety ----
EN_CONNECTORS = [
    [
        "Since joining, I'm proud that",
        "Practicing here has helped me",
        "When it comes to my progress,",
    ],
    [
        "One thing I'm really proud of is",
        "Being here has helped me",
        "If I had to describe how far I've come,",
    ],
    [
        "Looking back since I joined, I'm proud that",
        "The practice here has made a real difference —",
        "In terms of progress,",
    ],
]

NL_CONNECTORS = [
    [
        "Sinds ik lid ben, ben ik trots dat",
        "Oefenen hier heeft mij geholpen",
        "Als ik mijn vooruitgang beschrijf,",
    ],
    [
        "Iets waar ik echt trots op ben is",
        "Hier zijn heeft mij geholpen",
        "Als ik terugkijk op hoe ver ik gekomen ben,",
    ],
    [
        "Terugkijkend ben ik trots dat",
        "De oefensessies hier hebben echt het verschil gemaakt —",
        "Qua vooruitgang,",
    ],
]


def _build_testimonial_block(
    answers: list[str],
    member: discord.User | discord.Member,
    is_nl: bool,
) -> str:
    connector_pool = NL_CONNECTORS if is_nl else EN_CONNECTORS
    connectors = connector_pool[member.id % len(connector_pool)]
    lines = []
    for connector, answer in zip(connectors, answers[:3]):
        a = answer[0].lower() + answer[1:] if answer else answer
        a = a.rstrip(".")
        lines.append(f"{connector} {a}.")
    if len(answers) >= 4 and answers[3].strip():
        lines.append(f"\n{answers[3].strip()}")
    return "\n".join(lines)


# =======================================================
# MODAL — 4 fields, 4th optional
# =======================================================

class TestimonialModal(discord.ui.Modal):
    def __init__(self, *, is_nl: bool, publisher: "TestimonialPublisher") -> None:
        title = "Jouw verhaal" if is_nl else "Your Story"
        super().__init__(title=title)
        self._is_nl = is_nl
        self._publisher = publisher

        questions = NL_QUESTIONS if is_nl else EN_QUESTIONS
        placeholders = NL_PLACEHOLDERS if is_nl else EN_PLACEHOLDERS

        self.q1 = discord.ui.TextInput(
            label=questions[0],
            style=discord.TextStyle.paragraph,
            placeholder=placeholders[0],
            min_length=5,
            max_length=500,
            required=True,
        )
        self.q2 = discord.ui.TextInput(
            label=questions[1],
            style=discord.TextStyle.paragraph,
            placeholder=placeholders[1],
            min_length=5,
            max_length=500,
            required=True,
        )
        self.q3 = discord.ui.TextInput(
            label=questions[2],
            style=discord.TextStyle.paragraph,
            placeholder=placeholders[2],
            min_length=5,
            max_length=500,
            required=True,
        )
        self.q4 = discord.ui.TextInput(
            label=questions[3],
            style=discord.TextStyle.paragraph,
            placeholder=placeholders[3],
            max_length=500,
            required=False,
        )
        self.add_item(self.q1)
        self.add_item(self.q2)
        self.add_item(self.q3)
        self.add_item(self.q4)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        answers = [
            self.q1.value.strip(),
            self.q2.value.strip(),
            self.q3.value.strip(),
            self.q4.value.strip(),
        ]
        view = ShareChoiceView(
            answers=answers,
            member=interaction.user,
            is_nl=self._is_nl,
            publisher=self._publisher,
        )
        if self._is_nl:
            msg = (
                "Dankjewel voor het delen! 🙏\n\n"
                "**Wat wil je doen met jouw verhaal?**\n\n"
                "🌟 **Ja, deel mijn verhaal** — Je verhaal wordt geplaatst in dit kanaal "
                "en ik kan het ook gebruiken op mijn sociale media (zoals TikTok of Instagram) "
                "om andere leerders te inspireren. Je naam wordt erbij vermeld. "
                "Verhalen worden licht gecorrigeerd op grammatica.\n\n"
                "🔒 **Houd het privé** — Je verhaal komt alleen bij mij terecht. "
                "Ik lees het, maar het wordt nergens publiek gedeeld."
            )
        else:
            msg = (
                "Thank you for sharing! 🙏\n\n"
                "**What would you like to do with your story?**\n\n"
                "🌟 **Yes, share my story** — Your story will be posted in this channel "
                "and I may also use it on my social media (like TikTok or Instagram) "
                "to inspire other learners. Your name will be included. "
                "Stories may be lightly corrected for grammar.\n\n"
                "🔒 **Keep it private** — Your story comes to me only. "
                "I'll read it, but it won't be shared anywhere publicly."
            )
        await interaction.response.send_message(msg, view=view, ephemeral=True)


# =======================================================
# SHARE CHOICE VIEW
# =======================================================

class ShareChoiceView(discord.ui.View):
    def __init__(
        self,
        *,
        answers: list[str],
        member: discord.User | discord.Member,
        is_nl: bool,
        publisher: "TestimonialPublisher",
    ) -> None:
        super().__init__(timeout=300)
        self._answers = answers
        self._member = member
        self._is_nl = is_nl
        self._publisher = publisher

    @discord.ui.button(
        label="Yes, share my story",
        style=discord.ButtonStyle.success,
        emoji="🌟",
        custom_id="testimonial:share:v2",
    )
    async def share(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self._member.id:
            msg = "Dit is niet jouw formulier." if self._is_nl else "This is not your form."
            await interaction.response.send_message(msg, ephemeral=True)
            return
        self._disable_all()
        confirm = "✅ Jouw verhaal is gedeeld. Bedankt!" if self._is_nl else "✅ Your story has been shared. Thank you!"
        await interaction.response.edit_message(content=confirm, view=self)
        await self._publisher.publish_testimonial(
            answers=self._answers,
            member=self._member,
            is_nl=self._is_nl,
            public=True,
        )

    @discord.ui.button(
        label="Keep it private",
        style=discord.ButtonStyle.secondary,
        emoji="🔒",
        custom_id="testimonial:private:v2",
    )
    async def keep_private(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self._member.id:
            msg = "Dit is niet jouw formulier." if self._is_nl else "This is not your form."
            await interaction.response.send_message(msg, ephemeral=True)
            return
        self._disable_all()
        confirm = (
            "🔒 Jouw verhaal blijft privé. Bedankt dat je het met ons hebt gedeeld."
            if self._is_nl else
            "🔒 Your story has been kept private. Thank you for sharing it with us."
        )
        await interaction.response.edit_message(content=confirm, view=self)
        await self._publisher.publish_testimonial(
            answers=self._answers,
            member=self._member,
            is_nl=self._is_nl,
            public=False,
        )

    def _disable_all(self) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]


# =======================================================
# START BUTTON VIEWS (hub embed)
# =======================================================

class StartTestimonialView(discord.ui.View):
    def __init__(self, *, publisher: "TestimonialPublisher | None" = None) -> None:
        super().__init__(timeout=None)
        self._publisher = publisher

    @discord.ui.button(
        label="Share my story",
        style=discord.ButtonStyle.success,
        emoji="✍️",
        custom_id="testimonial:start:en:v1",
    )
    async def start_en(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        modal = TestimonialModal(
            is_nl=False,
            publisher=self._publisher or _get_global_publisher(),
        )
        await interaction.response.send_modal(modal)

    def set_publisher(self, publisher: "TestimonialPublisher") -> None:
        self._publisher = publisher


class StartTestimonialViewNL(discord.ui.View):
    def __init__(self, *, publisher: "TestimonialPublisher | None" = None) -> None:
        super().__init__(timeout=None)
        self._publisher = publisher

    @discord.ui.button(
        label="Deel mijn verhaal",
        style=discord.ButtonStyle.success,
        emoji="✍️",
        custom_id="testimonial:start:nl:v1",
    )
    async def start_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        modal = TestimonialModal(
            is_nl=True,
            publisher=self._publisher or _get_global_publisher(),
        )
        await interaction.response.send_modal(modal)

    def set_publisher(self, publisher: "TestimonialPublisher") -> None:
        self._publisher = publisher


_global_publisher: "TestimonialPublisher | None" = None


def _get_global_publisher() -> "TestimonialPublisher":
    if _global_publisher is None:
        raise RuntimeError("TestimonialPublisher not initialised")
    return _global_publisher


# =======================================================
# EMBEDS
# =======================================================

def _build_public_embed(
    answers: list[str],
    member: discord.User | discord.Member,
    is_nl: bool,
) -> discord.Embed:
    questions = NL_PLACEHOLDERS if is_nl else EN_PLACEHOLDERS

    if is_nl:
        title = f"🌟 Verhaal van {member.display_name}"
        footer = "Gedeeld door een lid van de community • Licht gecorrigeerd op grammatica"
        sep_label = "💬 **In hun eigen woorden:**"
    else:
        title = f"🌟 {member.display_name}'s Story"
        footer = "Shared by a community member • Lightly corrected for grammar"
        sep_label = "💬 **In their own words:**"

    lines = []
    for i, (q, a) in enumerate(zip(questions, answers)):
        if i == 3 and not a:
            continue
        lines.append(f"**{q}**\n{a}")

    block = _build_testimonial_block(answers, member, is_nl)
    description = "\n\n".join(lines) + f"\n\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n{sep_label}\n{block}"

    embed = discord.Embed(title=title, description=description, color=discord.Color.gold())
    embed.set_footer(text=footer)
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    return embed


def _build_admin_embed(
    answers: list[str],
    member: discord.User | discord.Member,
    is_nl: bool,
    public: bool,
) -> discord.Embed:
    questions = NL_PLACEHOLDERS if is_nl else EN_PLACEHOLDERS
    lang = "NL" if is_nl else "EN"

    if public:
        visibility = "🔓 Publiek gedeeld" if is_nl else "🔓 Shared publicly"
        color = discord.Color.green()
    else:
        visibility = "🔒 Niet delen" if is_nl else "🔒 Do not share"
        color = discord.Color.light_grey()

    lines = [
        f"**User:** {member.display_name} (`{member.id}`)",
        f"**Language:** {lang}",
        f"**Visibility:** {visibility}",
        "",
    ]
    for i, (q, a) in enumerate(zip(questions, answers)):
        if i == 3 and not a:
            continue
        lines.append(f"**{q}**\n{a}")

    block = _build_testimonial_block(answers, member, is_nl)
    description = "\n\n".join(lines) + f"\n\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n💬 **Testimonial block:**\n{block}"

    embed = discord.Embed(
        title=f"📋 Testimonial — {member.display_name}",
        description=description,
        color=color,
    )
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    return embed


def _build_hub_embed_en() -> discord.Embed:
    embed = discord.Embed(
        title="🌟 Your Successes and Stories",
        description=(
            "This is a space to celebrate your progress — big or small.\n\n"
            "Every step forward counts. Whether you had your first real conversation, "
            "finally understood a joke, or just showed up when it was hard.\n\n"
            "**Share your story** and inspire others who are on the same journey.\n\n"
            "It takes less than 2 minutes. Answer a few simple questions, "
            "then choose what happens next:\n\n"
            "🌟 **Share publicly** — your story gets posted here and I may use it "
            "on my social media to inspire other learners. Your name will be included. "
            "Stories may be lightly corrected for grammar.\n\n"
            "🔒 **Keep it private** — your story comes to me only. No one else sees it."
        ),
        color=discord.Color.gold(),
    )
    embed.set_footer(text="testimonial:hub:en:v2")
    return embed


def _build_hub_embed_nl() -> discord.Embed:
    embed = discord.Embed(
        title="🌟 Jouw Successen en Verhalen",
        description=(
            "Dit is een plek om je vooruitgang te vieren — groot of klein.\n\n"
            "Elke stap telt. Of je nu je eerste echte gesprek had, "
            "eindelijk een grap begreep, of gewoon opdaagde op een moeilijke dag.\n\n"
            "**Deel jouw verhaal** en inspireer anderen die hetzelfde pad bewandelen.\n\n"
            "Het duurt minder dan 2 minuten. Beantwoord een paar eenvoudige vragen, "
            "kies daarna wat er mee gebeurt:\n\n"
            "🌟 **Publiek delen** — jouw verhaal wordt hier geplaatst en ik kan het "
            "ook gebruiken op mijn sociale media om andere leerders te inspireren. "
            "Je naam wordt erbij vermeld. Verhalen worden licht gecorrigeerd op grammatica.\n\n"
            "🔒 **Privé houden** — jouw verhaal komt alleen bij mij terecht. Niemand anders ziet het."
        ),
        color=discord.Color.gold(),
    )
    embed.set_footer(text="testimonial:hub:nl:v2")
    return embed


# =======================================================
# PUBLISHER
# =======================================================

class TestimonialPublisher:
    def __init__(self, *, bot: discord.Client, repo: Any) -> None:
        self._bot = bot
        self._repo = repo

    async def publish_hub(self, is_nl: bool) -> None:
        channel_id = NL_SUCCESS_CHANNEL_ID if is_nl else EN_SUCCESS_CHANNEL_ID
        kv_key = KV_NL_HUB_MSG if is_nl else KV_EN_HUB_MSG
        marker = "testimonial:hub:nl:v2" if is_nl else "testimonial:hub:en:v2"
        embed = _build_hub_embed_nl() if is_nl else _build_hub_embed_en()
        view = StartTestimonialViewNL(publisher=self) if is_nl else StartTestimonialView(publisher=self)

        channel = self._bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self._bot.fetch_channel(channel_id)
            except Exception:
                log.warning("Testimonials: could not fetch channel %s", channel_id)
                return

        if not isinstance(channel, discord.TextChannel):
            return

        existing = None
        try:
            async for msg in channel.history(limit=50):
                if msg.author.id == self._bot.user.id:  # type: ignore[union-attr]
                    if msg.embeds and msg.embeds[0].footer and marker in (msg.embeds[0].footer.text or ""):
                        existing = msg
                        break
        except Exception:
            pass

        if existing:
            try:
                await existing.edit(embed=embed, view=view)
                log.info("Testimonials: updated hub in channel %s", channel_id)
                return
            except Exception:
                pass

        try:
            msg = await channel.send(embed=embed, view=view)
            log.info("Testimonials: posted hub in channel %s", channel_id)
            guild_id = getattr(self._bot, "dutch_guild_id" if is_nl else "guild_id", None)
            if guild_id and hasattr(self._repo, "kv_set"):
                await self._repo.kv_set(guild_id, kv_key, str(msg.id))
        except Exception:
            log.exception("Testimonials: failed to post hub in channel %s", channel_id)

    async def publish_testimonial(
        self,
        *,
        answers: list[str],
        member: discord.User | discord.Member,
        is_nl: bool,
        public: bool,
    ) -> None:
        success_channel_id = NL_SUCCESS_CHANNEL_ID if is_nl else EN_SUCCESS_CHANNEL_ID
        # All testimonials go to the same EN collected channel regardless of language
        collected_channel_id = EN_COLLECTED_CHANNEL_ID

        admin_embed = _build_admin_embed(answers, member, is_nl, public)

        # 1. Always send to admin collected channel
        try:
            collected_ch = self._bot.get_channel(collected_channel_id)
            if collected_ch is None:
                collected_ch = await self._bot.fetch_channel(collected_channel_id)
            if isinstance(collected_ch, discord.TextChannel):
                await collected_ch.send(embed=admin_embed)
                log.info("Testimonials: sent to collected channel %s", collected_channel_id)
        except Exception:
            log.exception("Testimonials: failed to send to collected channel")

        # 2. Always DM Lucas
        try:
            lucas = await self._bot.fetch_user(LUCAS_USER_ID)
            await lucas.send(embed=admin_embed)
            log.info("Testimonials: DMed Lucas")
        except Exception:
            log.exception("Testimonials: failed to DM Lucas")

        # 3. If public — post in success channel
        if public:
            try:
                success_ch = self._bot.get_channel(success_channel_id)
                if success_ch is None:
                    success_ch = await self._bot.fetch_channel(success_channel_id)
                if isinstance(success_ch, discord.TextChannel):
                    public_embed = _build_public_embed(answers, member, is_nl)
                    await success_ch.send(embed=public_embed)
                    log.info("Testimonials: posted public testimonial in %s", success_channel_id)
            except Exception:
                log.exception("Testimonials: failed to post public testimonial")


# =======================================================
# COG + SETUP
# =======================================================

class TestimonialsCog(commands.Cog):
    def __init__(self, bot: commands.Bot, publisher: TestimonialPublisher) -> None:
        self.bot = bot
        self._publisher = publisher


async def setup(
    bot: commands.Bot,
    repo: Any,
    guild_id: int,
    dutch_guild_id: int | None = None,
) -> TestimonialPublisher:
    global _global_publisher
    publisher = TestimonialPublisher(bot=bot, repo=repo)
    _global_publisher = publisher

    await bot.add_cog(TestimonialsCog(bot, publisher))

    bot.add_view(StartTestimonialView(publisher=publisher))
    bot.add_view(StartTestimonialViewNL(publisher=publisher))

    log.info("TestimonialsCog loaded.")
    return publisher