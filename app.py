# app.py
from __future__ import annotations

import asyncio
import logging
import signal
from contextlib import suppress

import discord
from discord.ext import commands

from config import get_settings
from utils.logging import setup_logging
from db.repo import Repo
from voice.tracker import VoiceTracker
from jobs.nudges import NudgeJobs
from jobs.partner_finder import PartnerFinder, PartnerHubView, PartnerHubViewNL
from jobs.welcome import send_welcome_dm
from commands.topics import setup as setup_topics
from commands.dictionary import setup as setup_dictionary, VocabPublisher
from commands.ask_jerry import setup as setup_ask_jerry, AskJerryView, AskJerryViewNL
from commands.jokes import setup as setup_jokes
from jobs.word_of_the_day import WordOfTheDayJob
from commands.testimonials import setup as setup_testimonials, StartTestimonialView, StartTestimonialViewNL
from jobs.testimonial_outreach import TestimonialOutreachJob
from jobs.session_reminder import SessionReminderJob
from jobs.private_lessons_summer import PrivateLessonsPublisher, EnLessonsView, NlLessonsView, EnSupportedView, NlSupportedView

log = logging.getLogger("app")
NL_GUILD_ID = 1336419808811679754  # Dutch guild fallback


class SpeakingBot(commands.Bot):
    def __init__(
        self,
        *,
        repo: Repo,
        tracker: VoiceTracker,
        guild_id: int,
        announcements_channel_id: int,
        english_learner_role_id: int,
        nudge_days: str = "MON,FRI",
        nudge_time: str = "15:00",
        debug_commands: bool = False,
        dutch_guild_id: int | None = None,
    ):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.voice_states = True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

        self.repo = repo
        self.tracker = tracker

        self.guild_id = guild_id
        self.announcements_channel_id = announcements_channel_id
        self.english_learner_role_id = english_learner_role_id

        self.nudge_days = nudge_days
        self.nudge_time = nudge_time

        self.debug_commands = debug_commands
        self.dutch_guild_id = dutch_guild_id
        self._jobs_started = False
        self._partner_finder: PartnerFinder | None = None
        self._ask_jerry_publisher = None
        self._wotd_job: WordOfTheDayJob | None = None
        self._testimonial_publisher = None
        self._testimonial_outreach: TestimonialOutreachJob | None = None

    async def setup_hook(self) -> None:
        # Load debug tools (dev-only) BEFORE sync so commands appear when enabled.
        if self.debug_commands:
            from commands.debug import setup as setup_debug

            await setup_debug(self, self.repo, enabled=True, guild_id=self.guild_id)
            log.info("Debug commands enabled (DEBUG_COMMANDS=1).")
        else:
            log.info("Debug commands disabled (DEBUG_COMMANDS=0).")

        # Load Ask Jerry cog
        self._ask_jerry_publisher = await setup_ask_jerry(
            self,
            self.repo,
            guild_id=self.guild_id,
        )

        # Load dictionary cog
        await setup_dictionary(
            self,
            self.repo,
            guild_id=self.guild_id,
            dutch_guild_id=self.dutch_guild_id,
        )

        # Load jokes cog
        await setup_jokes(self)

        # Load testimonials cog
        self._testimonial_publisher = await setup_testimonials(
            self,
            self.repo,
            guild_id=self.guild_id,
            dutch_guild_id=self.dutch_guild_id,
        )

        # Load topics cog
        await setup_topics(
            self,
            guild_id=self.guild_id,
            dutch_guild_id=self.dutch_guild_id,
        )

        # Manual commands
        @self.tree.command(
            name="woordvandedag",
            description="Post het woord van de dag nu in het woord-van-de-dag kanaal",
        )
        async def cmd_woordvandedag(interaction: discord.Interaction) -> None:
            if self._wotd_job is None:
                await interaction.response.send_message(
                    "De bot is nog niet klaar. Probeer het over een minuut.", ephemeral=True
                )
                return
            await interaction.response.send_message(
                "Woord van de dag wordt nu gepost.", ephemeral=True
            )
            await self._wotd_job.post_nl_now()

        @self.tree.command(
            name="wordoftheday",
            description="Post the word of the day now in the word-of-the-day channel",
        )
        async def cmd_wordoftheday(interaction: discord.Interaction) -> None:
            if self._wotd_job is None:
                await interaction.response.send_message(
                    "Bot is not ready yet. Try again in a moment.", ephemeral=True
                )
                return
            await interaction.response.send_message(
                "Word of the day is being posted now.", ephemeral=True
            )
            await self._wotd_job.post_en_now()

        @self.tree.command(
            name="herplaats",
            description="Herplaats het Ondersteund Spreken informatie embed in het OS kanaal",
        )
        async def cmd_herplaats(interaction: discord.Interaction) -> None:
            await interaction.response.send_message(
                "Ondersteund Spreken embed wordt opnieuw geplaatst...", ephemeral=True
            )
            try:
                guild_id = self.dutch_guild_id or self.guild_id
                await self.repo.kv_set(
                    guild_id, "supported_speaking_nl_message_id_v3", ""
                )
                pl = PrivateLessonsPublisher(bot=self, repo=self.repo)
                await pl.publish_nl_supported()
                await interaction.followup.send(
                    "Klaar. Het embed is opnieuw geplaatst.", ephemeral=True
                )
            except Exception:
                log.exception("herplaats: failed to repost NL supported embed")
                await interaction.followup.send(
                    "Er ging iets mis. Controleer de logs.", ephemeral=True
                )

        # Register persistent views
        self.add_view(PartnerHubView(finder=None))
        self.add_view(AskJerryView(publisher=None))
        self.add_view(AskJerryViewNL(publisher=None))
        self.add_view(PartnerHubViewNL(finder=None))
        self.add_view(EnLessonsView())
        self.add_view(NlLessonsView())
        self.add_view(EnSupportedView())
        self.add_view(NlSupportedView())
        self.add_view(StartTestimonialView())
        self.add_view(StartTestimonialViewNL())

        # Sync commands to English guild
        guild = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        log.info("Slash commands synced to guild %s", self.guild_id)

        # Sync commands to Dutch guild
        if self.dutch_guild_id:
            dutch_guild = discord.Object(id=self.dutch_guild_id)
            self.tree.copy_global_to(guild=dutch_guild)
            await self.tree.sync(guild=dutch_guild)
            log.info("Slash commands synced to Dutch guild %s", self.dutch_guild_id)

    async def on_ready(self) -> None:
        log.info("Logged in as %s (%s)", self.user, self.user.id)

        guild = self.get_guild(self.guild_id)
        if not guild:
            log.error("Guild %s not found. Is the bot in the server?", self.guild_id)
            return

        # Give tracker a reference to the bot (needed for voice encouragement)
        self.tracker._bot = self
        await self.tracker.bootstrap_from_guild(guild)

        if not self._jobs_started:
            NudgeJobs(
                bot=self,
                repo=self.repo,
                guild_id=self.guild_id,
                channel_id=self.announcements_channel_id,
                nudge_days=self.nudge_days,
                nudge_time=self.nudge_time,
                dutch_guild_id=self.dutch_guild_id,
            )
            self._jobs_started = True
            log.info(
                "NudgeJobs started (days=%s time=%s Europe/Amsterdam).",
                self.nudge_days,
                self.nudge_time,
            )

        # Partner Finder
        if not self._partner_finder:
            self._partner_finder = PartnerFinder(
                bot=self,
                repo=self.repo,
                guild_id=self.guild_id,
                dutch_guild_id=self.dutch_guild_id,
            )
            self.add_view(PartnerHubView(finder=self._partner_finder))
            self.add_view(PartnerHubViewNL(finder=self._partner_finder))
            await self._partner_finder.publish_hub(is_nl=False)
            if self.dutch_guild_id:
                await self._partner_finder.publish_hub(is_nl=True)
            log.info("PartnerFinder started.")

        # Private lessons embeds
        pl = PrivateLessonsPublisher(bot=self, repo=self.repo)
        try:
            await pl.publish_english()
        except Exception:
            log.exception("PrivateLessons: failed to publish English")
        try:
            await pl.publish_dutch()
        except Exception:
            log.exception("PrivateLessons: failed to publish Dutch")
        try:
            await pl.publish_en_supported()
        except Exception:
            log.exception("PrivateLessons: failed to publish EN supported")
        try:
            await pl.publish_nl_supported()
        except Exception:
            log.exception("PrivateLessons: failed to publish NL supported")

        # Vocabulary channel embeds
        vocab = VocabPublisher(bot=self, repo=self.repo)
        try:
            await vocab.publish_english()
        except Exception:
            log.exception("VocabPublisher: failed to publish English")
        try:
            await vocab.publish_dutch()
        except Exception:
            log.exception("VocabPublisher: failed to publish Dutch")

        # Ask Jerry hub
        if self._ask_jerry_publisher:
            try:
                await self._ask_jerry_publisher.publish(self.guild_id)
            except Exception:
                log.exception("AskJerry: failed to publish EN hub")
            if self.dutch_guild_id:
                try:
                    await self._ask_jerry_publisher.publish_dutch(self.dutch_guild_id)
                except Exception:
                    log.exception("AskJerry: failed to publish NL hub")

        # Session reminders
        # Testimonial hubs
        if self._testimonial_publisher:
            try:
                await self._testimonial_publisher.publish_hub(is_nl=False)
            except Exception:
                log.exception("Testimonials: failed to publish EN hub")
            if self.dutch_guild_id:
                try:
                    await self._testimonial_publisher.publish_hub(is_nl=True)
                except Exception:
                    log.exception("Testimonials: failed to publish NL hub")

        # Testimonial outreach
        self._testimonial_outreach = TestimonialOutreachJob(
            bot=self,
            repo=self.repo,
            en_guild_id=self.guild_id,
            nl_guild_id=self.dutch_guild_id or NL_GUILD_ID,
        )
        log.info("TestimonialOutreachJob started.")

        SessionReminderJob(
            bot=self,
            repo=self.repo,
            guild_id=self.guild_id,
            dutch_guild_id=self.dutch_guild_id,
        )
        log.info("SessionReminderJob started.")

        # Word of the day
        self._wotd_job = WordOfTheDayJob(
            bot=self,
            repo=self.repo,
            guild_id=self.guild_id,
            dutch_guild_id=self.dutch_guild_id,
        )
        log.info("WordOfTheDayJob started.")

        log.info("Ready.")

    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return

        # Welcome DM - both servers
        await send_welcome_dm(
            member=member,
            guild_id=member.guild.id,
            en_guild_id=self.guild_id,
            nl_guild_id=self.dutch_guild_id or 0,
        )

        # Auto-assign "English Learner" role - English server only
        if member.guild.id != self.guild_id:
            return

        role = member.guild.get_role(self.english_learner_role_id)
        if role is None:
            log.warning("English Learner role not found role_id=%s", self.english_learner_role_id)
            return

        if role in member.roles:
            return

        try:
            await member.add_roles(role, reason="Auto-assign English Learner role on join (SpeakingBot V2)")
            log.info("Assigned role english_learner user=%s", member.id)
        except discord.Forbidden:
            log.warning(
                "Failed to assign role (Forbidden). Check Manage Roles + role hierarchy. user=%s role_id=%s",
                member.id,
                role.id,
            )
        except discord.HTTPException:
            log.exception("Failed to assign role (HTTPException) user=%s role_id=%s", member.id, role.id)
        except Exception:
            log.exception("Failed to assign role (unexpected) user=%s role_id=%s", member.id, role.id)

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        await self.tracker.handle_voice_state_update(member, before, after)


async def _run_bot() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    repo = Repo(settings.db_path)
    await repo.connect()

    tracker = VoiceTracker(
        repo=repo,
        guild_id=settings.guild_id,
        speak_now_category_id=settings.speak_now_category_id,
        enable_inactivity_nudge=settings.enable_inactivity_nudge,
        inactivity_variant=settings.inactivity_nudge_variant,
        afk_channel_id=settings.afk_channel_id,
        dutch_guild_id=settings.dutch_guild_id,
        bot=None,
    )

    bot = SpeakingBot(
        repo=repo,
        tracker=tracker,
        guild_id=settings.guild_id,
        announcements_channel_id=settings.announcements_channel_id,
        english_learner_role_id=settings.english_learner_role_id,
        nudge_days=settings.nudge_days,
        nudge_time=settings.nudge_time,
        debug_commands=settings.debug_commands,
        dutch_guild_id=settings.dutch_guild_id,
    )

    shutdown_event = asyncio.Event()

    async def _graceful_shutdown(reason: str) -> None:
        if shutdown_event.is_set():
            return
        shutdown_event.set()
        log.info("Shutdown requested (%s). Closing bot...", reason)

        with suppress(Exception):
            await tracker.shutdown()
        with suppress(Exception):
            await bot.close()
        with suppress(Exception):
            await repo.close()

        log.info("Shutdown complete.")

    def _signal_handler(sig_name: str) -> None:
        asyncio.create_task(_graceful_shutdown(sig_name))

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, _signal_handler, sig.name)

    try:
        await bot.start(settings.discord_token)
    finally:
        await _graceful_shutdown("finally")


def main() -> None:
    asyncio.run(_run_bot())


if __name__ == "__main__":
    main()