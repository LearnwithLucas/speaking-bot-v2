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
from voice.community_tracker import VoiceTracker
from jobs.nudges import NudgeJobs
from jobs.partner_finder import PartnerFinder, PartnerHubView, PartnerHubViewNL
from jobs.welcome import send_welcome_dm, WelcomeTableView
from commands.topics import setup as setup_topics
from commands.ask_jerry import setup as setup_ask_jerry, AskJerryView, AskJerryViewNL
from commands.chat_jerry import setup as setup_daily_question
from commands.admin_refresh import ADMIN_TESTING_CHANNEL_ID, setup as setup_admin_refresh
from commands.admin_health import setup as setup_admin_health
from commands.profile import setup as setup_profile
from commands.community_guide import setup as setup_community_guide
from commands.jokes import setup as setup_jokes
from jobs.word_of_the_day import WordOfTheDayJob
from jobs.daily_questions import DailyQuestionJob
from commands.testimonials import setup as setup_testimonials, StartTestimonialView, StartTestimonialViewNL
from jobs.milestones import Milestones, ShoutoutOptView
from jobs.hosts import HostInvites, HostInviteView, HostReviewButton
from jobs.winback import WinbackJob
from jobs.cafe_hour import CafeHour
from jobs.server_tag import ServerTag
from jobs.update_dm import UpdateDM, UpdateOptOutView
from jobs.weekly_tip import WeeklyTip
from voice.table_tools import TableTools
from jobs.session_reminder import SessionReminderJob
from jobs.private_lessons_summer import PrivateLessonsPublisher, EnLessonsView, NlLessonsView, EnSupportedView, NlSupportedView

log = logging.getLogger("app")
EN_GUILD_ID = 1181652389732831323
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
        intents.message_content = True
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
        self._chat_jerry_publisher = None
        self._suggestion_publisher = None
        self._daily_question_job: DailyQuestionJob | None = None
        self._wotd_job: WordOfTheDayJob | None = None
        self._testimonial_publisher = None
        self._winback: WinbackJob | None = None

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

        # Daily chat question (posting + counting replies)
        self._chat_jerry_publisher = await setup_daily_question(
            self,
            self.repo,
            guild_id=self.guild_id,
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

        # Load admin commands
        await setup_admin_refresh(self)
        await setup_admin_health(self)
        await setup_profile(self)

        # Load community guide command
        await setup_community_guide(self)

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
            name="dailyquestionnow",
            description="Post today's daily chat question in both community chat channels",
        )
        async def cmd_dailyquestionnow(interaction: discord.Interaction) -> None:
            if int(getattr(interaction, "channel_id", 0) or 0) != ADMIN_TESTING_CHANNEL_ID:
                await interaction.response.send_message(
                    f"Use this in <#{ADMIN_TESTING_CHANNEL_ID}> so admin actions stay in one place.",
                    ephemeral=True,
                )
                return

            if self._chat_jerry_publisher is None:
                await interaction.response.send_message(
                    "The daily question is not ready yet. Try again in a moment.",
                    ephemeral=True,
                )
                return

            await interaction.response.defer(ephemeral=True)
            await self._chat_jerry_publisher.publish_daily_question(
                EN_GUILD_ID,
                force=True,
                is_nl=False,
            )
            await self._chat_jerry_publisher.publish_daily_question(
                self.dutch_guild_id or NL_GUILD_ID,
                force=True,
                is_nl=True,
            )
            await interaction.followup.send(
                "Posted a daily question in both community chat channels.",
                ephemeral=True,
            )

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
                    guild_id, "supported_speaking_nl_message_id_v4", ""
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
        self.add_view(WelcomeTableView(is_nl=False))
        self.add_view(WelcomeTableView(is_nl=True))
        self.add_view(HostInviteView())
        self.add_view(ShoutoutOptView())
        self.add_view(UpdateOptOutView())
        self.add_dynamic_items(HostReviewButton)

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

        dutch_guild = self.get_guild(self.dutch_guild_id) if self.dutch_guild_id else None
        if dutch_guild is not None:
            await self._move_dutch_voice_history(dutch_guild)
            await self.tracker.bootstrap_from_guild(dutch_guild)

        for g in (guild, dutch_guild):
            if g is None:
                continue
            try:
                await self.repo.member_joins_backfill(
                    g.id,
                    [
                        (m.id, int(m.joined_at.timestamp()))
                        for m in g.members
                        if not m.bot and m.joined_at is not None
                    ],
                )
            except Exception:
                log.exception("Member join backfill failed guild=%s", g.id)

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
            # Level status on voice tables + knocking on a full table.
            self._table_tools = TableTools(
                bot=self,
                repo=self.repo,
                is_table=self.tracker._is_target_voice_channel,
                dutch_guild_id=self.dutch_guild_id,
            )
            self._partner_finder.table_tools = self._table_tools
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

        # Daily chat question
        if self._chat_jerry_publisher and not self._daily_question_job:
            self._daily_question_job = DailyQuestionJob(
                bot=self,
                publisher=self._chat_jerry_publisher,
                en_guild_id=EN_GUILD_ID,
                nl_guild_id=self.dutch_guild_id or NL_GUILD_ID,
            )
            log.info("DailyQuestionJob started.")

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

        # Voice milestones (1h, 3h, 10h). The 3h DM also asks for a testimonial,
        # which replaces the old twice-a-day testimonial outreach scan.
        if self.tracker.milestones is None:
            # Conversation Host invites at 20h (EN only for now).
            self.host_invites = HostInvites(bot=self, repo=self.repo, guild_id=self.guild_id)
            milestones = Milestones(
                bot=self,
                repo=self.repo,
                dutch_guild_id=self.dutch_guild_id,
                role_guild_id=self.guild_id,
                hosts=self.host_invites,
            )
            for gid in (self.guild_id, self.dutch_guild_id):
                if gid:
                    await milestones.ensure_start(gid)
            try:
                await milestones.seed_shoutouts()
            except Exception:
                log.exception("Milestones: seeding shout-outs failed")
            self.tracker.milestones = milestones
            log.info("Milestones started.")

        # One-off update DM (admin command) and the Monday tip (EN only).
        if getattr(self, "update_dm", None) is None:
            self.update_dm = UpdateDM(bot=self, repo=self.repo, guild_id=self.guild_id)
        if getattr(self, "weekly_tip", None) is None:
            self.weekly_tip = WeeklyTip(
                bot=self,
                repo=self.repo,
                guild_id=self.guild_id,
                channel_id=self.announcements_channel_id,
            )

        # Server Tag (CAFE) detection and thanks (EN only).
        if getattr(self, "server_tag", None) is None:
            self.server_tag = ServerTag(bot=self, repo=self.repo, guild_id=self.guild_id)

        # Daily Café Hour (EN only). Does nothing unless CAFE_HOUR_ENABLED=true.
        if getattr(self, "cafe_hour", None) is None:
            self.cafe_hour = CafeHour(bot=self, repo=self.repo, guild_id=self.guild_id)

        # Win-back: one DM after 14 days without voice time (daily, 17:07 Amsterdam).
        if self._winback is None:
            self._winback = WinbackJob(
                bot=self,
                repo=self.repo,
                guild_id=self.guild_id,
                dutch_guild_id=self.dutch_guild_id,
            )
            log.info("WinbackJob started.")

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

    async def _move_dutch_voice_history(self, dutch_guild: discord.Guild) -> None:
        """One-time fix: Dutch voice sessions used to be stored under the English guild id."""
        kv_key = "dutch_voice_history_moved_v1"
        if await self.repo.kv_get(dutch_guild.id, kv_key):
            return
        try:
            moved = await self.repo.move_sessions_to_guild(
                self.guild_id,
                dutch_guild.id,
                [c.id for c in dutch_guild.channels],
            )
            await self.repo.kv_set(dutch_guild.id, kv_key, str(int(discord.utils.utcnow().timestamp())))
            log.info("Moved %s Dutch voice sessions to guild %s", moved, dutch_guild.id)
        except Exception:
            log.exception("Moving Dutch voice history failed")

    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        server_tag = getattr(self, "server_tag", None)
        if server_tag is not None and after.guild.id == self.guild_id:
            await server_tag.on_user_changed(before, after)

    async def on_user_update(self, before: discord.User, after: discord.User) -> None:
        server_tag = getattr(self, "server_tag", None)
        if server_tag is not None:
            await server_tag.on_user_changed(before, after)

    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return

        try:
            joined = member.joined_at or discord.utils.utcnow()
            await self.repo.member_join_record(member.guild.id, member.id, int(joined.timestamp()))
        except Exception:
            log.exception("Failed to record member join user=%s guild=%s", member.id, member.guild.id)

        # Welcome DM - both servers
        await send_welcome_dm(
            member=member,
            guild_id=member.guild.id,
            en_guild_id=self.guild_id,
            nl_guild_id=self.dutch_guild_id or 0,
            cafe_hour=getattr(self, "cafe_hour", None),
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
        table_tools = getattr(self, "_table_tools", None)
        if table_tools is not None:
            try:
                await table_tools.on_voice_state_update(member, before, after)
            except Exception:
                log.exception("TableTools: voice update failed user=%s", member.id)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        chat_cog = self.get_cog("ChatJerryCog")
        if chat_cog is not None and hasattr(chat_cog, "handle_message"):
            await chat_cog.handle_message(message)

        await self.process_commands(message)


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
