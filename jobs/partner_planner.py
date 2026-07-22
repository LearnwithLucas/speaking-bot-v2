from __future__ import annotations

# jobs/partner_planner.py
import asyncio
import logging
from dataclasses import dataclass

import discord

log = logging.getLogger("jobs.partner_planner")

EN_LOOKING_CHANNEL_ID = 1435902125652578434
NL_LOOKING_CHANNEL_ID = 1484566832982654996
OPEN_CONVERSATION_CHANNEL_ID = 1456551629301219420
I_WANT_TO_SPEAK_ROLE_ID = 1529421061727322172


@dataclass(frozen=True)
class DayOption:
    key: str
    en_label: str
    nl_label: str
    expires_after_seconds: int


@dataclass(frozen=True)
class TimeOption:
    key: str
    en_label: str
    nl_label: str


DAY_OPTIONS: dict[str, DayOption] = {
    "today": DayOption("today", "later today", "later vandaag", 12 * 60 * 60),
    "tomorrow": DayOption("tomorrow", "tomorrow", "morgen", 36 * 60 * 60),
    "weekend": DayOption("weekend", "this weekend", "dit weekend", 4 * 24 * 60 * 60),
    "next_week": DayOption("next_week", "next week", "volgende week", 8 * 24 * 60 * 60),
}

TIME_OPTIONS: dict[str, TimeOption] = {
    "morning": TimeOption("morning", "morning", "ochtend"),
    "afternoon": TimeOption("afternoon", "afternoon", "middag"),
    "evening": TimeOption("evening", "evening", "avond"),
}


def _display_name(user: discord.abc.User) -> str:
    return getattr(user, "display_name", None) or user.name


def _open_conversation_link(guild_id: int) -> str:
    return f"https://discord.com/channels/{guild_id}/{OPEN_CONVERSATION_CHANNEL_ID}"


def _conversation_starters(*, is_nl: bool) -> str:
    if is_nl:
        return (
            "\n\n**Makkelijke starters:**\n"
            "- What did you do today?\n"
            "- Tell me about a food you like.\n"
            "- What is one thing you want to practice in English?\n\n"
            "Je hoeft niet perfect te praten. Kies gewoon een vraag."
        )
    return (
        "\n\n**Easy starters:**\n"
        "- What did you do today?\n"
        "- Tell me about a food you like.\n"
        "- What is one thing you want to practice in English?\n\n"
        "No need to make it perfect. Pick one and start there."
    )


def _planned_label(day: DayOption, time_option: TimeOption, *, is_nl: bool) -> str:
    if is_nl:
        return f"{day.nl_label} in de {time_option.nl_label}"
    return f"{day.en_label} in the {time_option.en_label}"


async def _fetch_text_channel(bot: discord.Client, channel_id: int) -> discord.TextChannel | None:
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            log.exception("PartnerPlanner: could not fetch channel %s", channel_id)
            return None

    if not isinstance(channel, discord.TextChannel):
        log.warning("PartnerPlanner: channel %s is not a text channel", channel_id)
        return None

    return channel


async def _delete_later(message: discord.Message, seconds: int) -> None:
    await asyncio.sleep(seconds)
    try:
        await message.delete()
    except discord.NotFound:
        return
    except discord.Forbidden:
        log.info("PartnerPlanner: missing permission to delete plan message %s", message.id)
        try:
            await message.edit(view=None)
        except Exception:
            log.exception("PartnerPlanner: could not clear expired plan view %s", message.id)
    except Exception:
        log.exception("PartnerPlanner: could not delete expired plan message %s", message.id)


class PartnerPlanStartView(discord.ui.View):
    def __init__(self, *, bot: discord.Client, is_nl: bool) -> None:
        super().__init__(timeout=5 * 60)
        self.bot = bot
        self.is_nl = is_nl

    async def _choose_day(self, interaction: discord.Interaction, key: str) -> None:
        day = DAY_OPTIONS[key]
        if self.is_nl:
            content = f"Wanneer op **{day.nl_label}** past ongeveer?"
        else:
            content = f"What time on **{day.en_label}** works roughly?"
        await interaction.response.edit_message(
            content=content,
            view=PartnerPlanTimeView(bot=self.bot, is_nl=self.is_nl, day=day),
        )

    @discord.ui.button(label="Later today", style=discord.ButtonStyle.secondary, custom_id="partner:plan:day:en_today:v1", row=0)
    async def later_today(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._choose_day(interaction, "today")

    @discord.ui.button(label="Tomorrow", style=discord.ButtonStyle.success, custom_id="partner:plan:day:tomorrow:v1", row=0)
    async def tomorrow(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._choose_day(interaction, "tomorrow")

    @discord.ui.button(label="This weekend", style=discord.ButtonStyle.secondary, custom_id="partner:plan:day:weekend:v1", row=1)
    async def weekend(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._choose_day(interaction, "weekend")

    @discord.ui.button(label="Next week", style=discord.ButtonStyle.secondary, custom_id="partner:plan:day:next_week:v1", row=1)
    async def next_week(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._choose_day(interaction, "next_week")


class PartnerPlanTimeView(discord.ui.View):
    def __init__(self, *, bot: discord.Client, is_nl: bool, day: DayOption) -> None:
        super().__init__(timeout=5 * 60)
        self.bot = bot
        self.is_nl = is_nl
        self.day = day

    async def _choose_time(self, interaction: discord.Interaction, key: str) -> None:
        if interaction.guild is None:
            await interaction.response.edit_message(
                content="This only works inside the server.",
                view=None,
            )
            return

        time_option = TIME_OPTIONS[key]
        label = _planned_label(self.day, time_option, is_nl=self.is_nl)
        channel_id = NL_LOOKING_CHANNEL_ID if self.is_nl else EN_LOOKING_CHANNEL_ID
        channel = await _fetch_text_channel(self.bot, channel_id)
        if channel is None:
            await interaction.response.edit_message(
                content="I could not find the partner channel. Please tell Lucas to check the bot logs.",
                view=None,
            )
            return

        embed = discord.Embed(
            title="Plan a speaking time" if not self.is_nl else "Plan een spreekmoment",
            description=(
                f"{interaction.user.mention} is looking for a speaking partner **{label}**.\n\n"
                "Click **I might join** if you may want to join. No pressure - this just helps people find each other."
                if not self.is_nl
                else f"{interaction.user.mention} zoekt een spreekpartner **{label}**.\n\n"
                "Klik op **Misschien doe ik mee** als je misschien wilt aansluiten. Geen druk - dit helpt mensen elkaar te vinden."
            ),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="This post disappears after the planned time." if not self.is_nl else "Dit bericht verdwijnt na het geplande moment.")
        content = None if self.is_nl else f"<@&{I_WANT_TO_SPEAK_ROLE_ID}>"
        allowed_mentions = (
            discord.AllowedMentions(roles=True)
            if not self.is_nl
            else discord.AllowedMentions.none()
        )

        view = PlannedPracticeView(
            requester_id=interaction.user.id,
            requester_name=_display_name(interaction.user),
            planned_label=label,
            guild_id=interaction.guild.id,
            is_nl=self.is_nl,
        )

        try:
            await interaction.response.defer(ephemeral=True)
            message = await channel.send(
                content=content,
                embed=embed,
                view=view,
                allowed_mentions=allowed_mentions,
            )
            asyncio.create_task(_delete_later(message, self.day.expires_after_seconds))
            await interaction.edit_original_response(
                content=(
                    f"Posted your plan for **{label}** in <#{channel_id}>."
                    if not self.is_nl
                    else f"Je planning voor **{label}** staat nu in <#{channel_id}>."
                ),
                embed=None,
                view=None,
            )
        except discord.Forbidden:
            log.exception("PartnerPlanner: missing permission to post plan in channel %s", channel_id)
            await interaction.edit_original_response(
                content="I do not have permission to post in the partner channel. Please tell Lucas to check channel permissions.",
                embed=None,
                view=None,
            )
        except Exception:
            log.exception("PartnerPlanner: failed to post planned practice")
            await interaction.edit_original_response(
                content="Something went wrong while posting your plan. Please try again in a moment.",
                embed=None,
                view=None,
            )

    @discord.ui.button(label="Morning", style=discord.ButtonStyle.secondary, custom_id="partner:plan:time:morning:v1", row=0)
    async def morning(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._choose_time(interaction, "morning")

    @discord.ui.button(label="Afternoon", style=discord.ButtonStyle.secondary, custom_id="partner:plan:time:afternoon:v1", row=0)
    async def afternoon(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._choose_time(interaction, "afternoon")

    @discord.ui.button(label="Evening", style=discord.ButtonStyle.success, custom_id="partner:plan:time:evening:v1", row=0)
    async def evening(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._choose_time(interaction, "evening")


class PlannedPracticeView(discord.ui.View):
    def __init__(
        self,
        *,
        requester_id: int,
        requester_name: str,
        planned_label: str,
        guild_id: int,
        is_nl: bool,
    ) -> None:
        super().__init__(timeout=8 * 24 * 60 * 60)
        self.requester_id = requester_id
        self.requester_name = requester_name
        self.planned_label = planned_label
        self.guild_id = guild_id
        self.is_nl = is_nl
        self._sent_to: set[int] = set()

    @discord.ui.button(label="I might join", style=discord.ButtonStyle.success, custom_id="partner:plan:join:v1")
    async def might_join(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id == self.requester_id:
            await interaction.response.send_message(
                "This is your plan. Someone else can click the button to connect with you."
                if not self.is_nl
                else "Dit is jouw planning. Iemand anders kan op de knop klikken om met je te oefenen.",
                ephemeral=True,
            )
            return

        if interaction.user.id in self._sent_to:
            await interaction.response.send_message(
                "I already sent the DMs for this plan."
                if not self.is_nl
                else "Ik heb de DMs voor deze planning al gestuurd.",
                ephemeral=True,
            )
            return

        self._sent_to.add(interaction.user.id)
        await interaction.response.send_message(
            "Nice. I will DM you both with the conversation channel."
            if not self.is_nl
            else "Mooi. Ik stuur jullie allebei een DM met het gesprekskanaal.",
            ephemeral=True,
        )

        sent = await self._send_match_dms(interaction)
        if sent == 0:
            await interaction.followup.send(
                "I could not DM either person. You can still use the Open Conversation channel from the server."
                if not self.is_nl
                else "Ik kon niemand een DM sturen. Je kunt nog steeds het Open Conversation kanaal in de server gebruiken.",
                ephemeral=True,
            )

    async def _send_match_dms(self, interaction: discord.Interaction) -> int:
        if interaction.guild is None:
            return 0

        try:
            requester = interaction.guild.get_member(self.requester_id) or await interaction.guild.fetch_member(self.requester_id)
        except Exception:
            log.exception("PartnerPlanner: could not fetch requester %s", self.requester_id)
            requester = None

        joiner = interaction.user
        open_conversation = _open_conversation_link(self.guild_id)
        starters = _conversation_starters(is_nl=self.is_nl)
        sent = 0

        if requester is not None:
            try:
                if self.is_nl:
                    await requester.send(
                        f"🤝 **Spreekmoment gepland**\n\n"
                        f"**{_display_name(joiner)}** wil misschien aansluiten **{self.planned_label}**.\n\n"
                        f"Open Conversation: {open_conversation}\n"
                        f"Begin rustig. Je kunt gewoon hoi zeggen.{starters}"
                    )
                else:
                    await requester.send(
                        f"🤝 **Speaking plan match**\n\n"
                        f"**{_display_name(joiner)}** might join you **{self.planned_label}**.\n\n"
                        f"Open Conversation: {open_conversation}\n"
                        f"Start gently. You can just say hi.{starters}"
                    )
                sent += 1
            except discord.Forbidden:
                log.info("PartnerPlanner: requester DM blocked user=%s", self.requester_id)
            except Exception:
                log.exception("PartnerPlanner: failed to DM requester %s", self.requester_id)

        try:
            if self.is_nl:
                await joiner.send(
                    f"🤝 **Spreekmoment gepland**\n\n"
                    f"Je wilt misschien aansluiten bij **{self.requester_name}** **{self.planned_label}**.\n\n"
                    f"Open Conversation: {open_conversation}\n"
                    f"Begin rustig. Je kunt gewoon hoi zeggen.{starters}"
                )
            else:
                await joiner.send(
                    f"🤝 **Speaking plan match**\n\n"
                    f"You might join **{self.requester_name}** **{self.planned_label}**.\n\n"
                    f"Open Conversation: {open_conversation}\n"
                    f"Start gently. You can just say hi.{starters}"
                )
            sent += 1
        except discord.Forbidden:
            log.info("PartnerPlanner: joiner DM blocked user=%s", joiner.id)
        except Exception:
            log.exception("PartnerPlanner: failed to DM joiner %s", joiner.id)

        return sent
