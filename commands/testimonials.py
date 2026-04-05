from __future__ import annotations

# commands/testimonials.py
import logging
from typing import Any

import discord
from discord.ext import commands

log = logging.getLogger("commands.testimonials")

# ---- Channel IDs ----
EN_SUCCESS_CHANNEL_ID = 1490320758507962490      # Your Successes and Stories
NL_SUCCESS_CHANNEL_ID = 1490320826027741185      # Jouw Successen en Verhalen
EN_COLLECTED_CHANNEL_ID = 1490322440788644011    # 🌱┃collected-testimonials (admin)
NL_COLLECTED_CHANNEL_ID = 1490322080678543542    # 🌱┃verzamelde-getuigenissen (admin)

LUCAS_USER_ID = 1181651144100036718

KV_EN_HUB_MSG = "testimonial_hub_en_v1"
KV_NL_HUB_MSG = "testimonial_hub_nl_v1"

# ---- Questions ----
# Short labels (≤45 chars) shown in the modal input
# Full questions shown as placeholders
EN_QUESTIONS = [
    "What are you proud of since joining?",
    "How has practicing here helped you?",
    "How would you describe your progress?",
]
EN_PLACEHOLDERS = [
    "What's one thing you're proud of since joining?",
    "How has practicing here helped you?",
    "If you were telling a friend, how would you describe your progress?",
]

NL_QUESTIONS = [
    "Waar ben je trots op sinds je lid bent?",
    "Hoe heeft oefenen hier jou geholpen?",
    "Hoe zou je jouw vooruitgang omschrijven?",
]
NL_PLACEHOLDERS = [
    "Wat is iets waar je trots op bent sinds je lid bent geworden?",
    "Hoe heeft het oefenen hier jou geholpen?",
    "Als je het aan een vriend zou vertellen, hoe zou je je vooruitgang omschrijven?",
]


# =======================================================
# MODAL — one question at a time
# =======================================================

class TestimonialModal(discord.ui.Modal):
    """Single modal with all 3 questions — Discord does not allow modal-to-modal chaining."""

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
        self.add_item(self.q1)
        self.add_item(self.q2)
        self.add_item(self.q3)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        answers = [
            self.q1.value.strip(),
            self.q2.value.strip(),
            self.q3.value.strip(),
        ]
        view = ShareChoiceView(
            answers=answers,
            member=interaction.user,
            is_nl=self._is_nl,
            publisher=self._publisher,
        )
        if self._is_nl:
            msg = (
                "Bedankt! Wil je jouw verhaal delen met de community?\n\n"
                "Je kunt altijd kiezen om het privé te houden."
            )
        else:
            msg = (
                "Thank you! Would you like to share your story with the community?\n\n"
                "You can always choose to keep it private."
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
        custom_id="testimonial:share",
    )
    async def share(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self._member.id:
            await interaction.response.send_message("This is not your form.", ephemeral=True)
            return
        self._disable_all()
        await interaction.response.edit_message(
            content="✅ Your story has been shared. Thank you!" if not self._is_nl
            else "✅ Jouw verhaal is gedeeld. Bedankt!",
            view=self,
        )
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
        custom_id="testimonial:private",
    )
    async def keep_private(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self._member.id:
            await interaction.response.send_message("This is not your form.", ephemeral=True)
            return
        self._disable_all()
        await interaction.response.edit_message(
            content="🔒 Your story has been kept private. Thank you for sharing it with us." if not self._is_nl
            else "🔒 Jouw verhaal blijft privé. Bedankt dat je het met ons hebt gedeeld.",
            view=self,
        )
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
# START BUTTON VIEW (on the hub embed)
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


# Global publisher reference for persistent views (after restart)
_global_publisher: "TestimonialPublisher | None" = None


def _get_global_publisher() -> "TestimonialPublisher":
    if _global_publisher is None:
        raise RuntimeError("TestimonialPublisher not initialised")
    return _global_publisher


# =======================================================
# PUBLISHER
# =======================================================

def _build_public_embed(
    answers: list[str],
    member: discord.User | discord.Member,
    is_nl: bool,
) -> discord.Embed:
    questions = NL_PLACEHOLDERS if is_nl else EN_PLACEHOLDERS
    if is_nl:
        title = f"🌟 Verhaal van {member.display_name}"
        footer = "Gedeeld door een lid van de community"
    else:
        title = f"🌟 {member.display_name}'s Story"
        footer = "Shared by a community member"

    lines = []
    for q, a in zip(questions, answers):
        lines.append(f"**{q}**\n{a}")

    embed = discord.Embed(
        title=title,
        description="\n\n".join(lines),
        color=discord.Color.gold(),
    )
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
    visibility = ("🔓 Publiek gedeeld" if is_nl else "🔓 Shared publicly") if public \
        else ("🔒 Privé gehouden" if is_nl else "🔒 Kept private")

    lines = [f"**User:** {member.display_name} (`{member.id}`)", f"**Language:** {lang}", f"**Visibility:** {visibility}", ""]
    for q, a in zip(questions, answers):
        lines.append(f"**{q}**\n{a}")

    embed = discord.Embed(
        title=f"📋 Testimonial — {member.display_name}",
        description="\n\n".join(lines),
        color=discord.Color.green() if public else discord.Color.light_grey(),
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
            "It takes less than 2 minutes. Three simple questions, then you choose "
            "whether to share it publicly or keep it just between us."
        ),
        color=discord.Color.gold(),
    )
    embed.set_footer(text="testimonial:hub:en:v1")
    return embed


def _build_hub_embed_nl() -> discord.Embed:
    embed = discord.Embed(
        title="🌟 Jouw Successen en Verhalen",
        description=(
            "Dit is een plek om je vooruitgang te vieren — groot of klein.\n\n"
            "Elke stap telt. Of je nu je eerste echte gesprek had, "
            "eindelijk een grap begreep, of gewoon opdaagde op een moeilijke dag.\n\n"
            "**Deel jouw verhaal** en inspireer anderen die hetzelfde pad bewandelen.\n\n"
            "Het duurt minder dan 2 minuten. Drie eenvoudige vragen, dan kies jij zelf "
            "of je het publiek deelt of privé houdt."
        ),
        color=discord.Color.gold(),
    )
    embed.set_footer(text="testimonial:hub:nl:v1")
    return embed


class TestimonialPublisher:
    def __init__(self, *, bot: discord.Client, repo: Any) -> None:
        self._bot = bot
        self._repo = repo

    async def publish_hub(self, is_nl: bool) -> None:
        channel_id = NL_SUCCESS_CHANNEL_ID if is_nl else EN_SUCCESS_CHANNEL_ID
        kv_key = KV_NL_HUB_MSG if is_nl else KV_EN_HUB_MSG
        marker = "testimonial:hub:nl:v1" if is_nl else "testimonial:hub:en:v1"
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

        # Find existing hub message by footer marker
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
            # Store message ID
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
        collected_channel_id = NL_COLLECTED_CHANNEL_ID if is_nl else EN_COLLECTED_CHANNEL_ID

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

    # Register persistent views
    bot.add_view(StartTestimonialView(publisher=publisher))
    bot.add_view(StartTestimonialViewNL(publisher=publisher))

    log.info("TestimonialsCog loaded.")
    return publisher