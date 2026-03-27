import asyncio
import time
import logging
import random
from typing import Dict, Optional, Tuple

import discord

from db.repo import Repo
from utils.time import amsterdam_iso_week_key, amsterdam_day_key, amsterdam_day_key_from_epoch
from .rules import is_in_speak_now_category, should_count_state, qualifies_first_voice_attempt

log = logging.getLogger("voice.tracker")

"""
Achievements intentionally do not reward duration, frequency, or volume.
They exist to mark courage moments, not progress.

Guardrails:
- Private only (no public messaging)
- No streaks / sequences / escalation
- At most ONE achievement awarded per join event (prevents reinforcement spikes)
"""

# Existing
ACH_FIRST_VOICE_ATTEMPT = "first_voice_attempt"
FIRST_VOICE_ATTEMPT_CHECK_SECONDS = 180  # 3 minutes

# New approved achievements
ACH_JOINED_AGAIN = "joined_again"
ACH_CAME_BACK_AFTER_BREAK = "came_back_after_break"
ACH_SPOKE_WITH_SOMEONE_NEW = "spoke_with_someone_new"

# Joined-again reconnection cooldown (prevents false positives on hiccups / quick reconnects)
JOINED_AGAIN_MIN_GAP_SECONDS = 30 * 60  # 30 minutes

# Came back after break threshold
BREAK_MIN_DAYS = 14
BREAK_MIN_SECONDS = BREAK_MIN_DAYS * 86400

# Spoke-with-new guardrail: avoid crowded-room mass awarding (applies to ANY qualifying channel)
MAX_NEW_MEET_ROOM_SIZE = 4

# ---- Voice encouragement ----
EN_VOICE_CATEGORY_ID = 1181652390835916818
NL_VOICE_CATEGORY_ID = 1336419808811679756

EN_ENCOURAGEMENT_5MIN = [
    "5 minutes in. Good to see you here.",
    "You showed up. That already counts for something.",
    "Nice, 5 minutes. Keep going.",
    "You're in the channel. That's the hardest part.",
    "5 minutes. You're doing it.",
    "Good to have you in here.",
    "Still here after 5 minutes. Nice work.",
    "You came. That matters more than you think.",
    "5 minutes of practice in the bag.",
    "You didn't just think about joining. You actually did it.",
    "Here you are. Good.",
    "5 minutes. Not bad at all.",
    "You made it in. That's what counts.",
    "Good job getting started.",
    "5 minutes in. This is how progress actually happens.",
    "You're practicing. Simple as that.",
    "Showing up is most of it. You're here.",
    "5 minutes. Every session starts this way.",
    "You're in the room. That's real.",
    "Nice. 5 minutes of actual speaking practice.",
    "You picked up the phone, so to speak. Good.",
    "5 minutes. You'll be glad you did this.",
    "Look at you, actually showing up.",
    "You didn't wait for the perfect moment. You just joined.",
    "5 minutes. Keep the conversation going.",
    "Here we go. 5 minutes in.",
    "You're practicing English right now. That's it. That's the thing.",
    "5 minutes. One sentence at a time.",
    "Good to see someone in here.",
    "5 minutes in the channel. Solid start.",
]

EN_ENCOURAGEMENT_30MIN = [
    "30 minutes. That's a real session.",
    "You've been here for 30 minutes. That's genuinely impressive.",
    "30 minutes of speaking practice. Well done.",
    "Still going after 30 minutes. Good work.",
    "30 minutes. You should feel good about that.",
    "Half an hour of English practice. That adds up.",
    "30 minutes in. You showed up and stayed. That's the hard part.",
    "That's 30 minutes. Seriously, well done.",
    "You've been practicing for 30 minutes. That takes effort.",
    "30 minutes. Most people don't make it this far.",
    "Half an hour. Not everyone does that.",
    "30 minutes of conversation practice. That's a lot of good work.",
    "You're still here. 30 minutes. Respect.",
    "30 minutes in the channel. That's dedication.",
    "Good. 30 minutes. Keep going if you feel like it.",
    "30 minutes. You did that. Nice.",
    "That's half an hour of real practice. Be proud of that.",
    "30 minutes. Every single minute of that was useful.",
    "Still going after 30 minutes. You're doing great.",
    "30 minutes of speaking practice is no small thing.",
    "You've been here half an hour. That's a proper session.",
    "30 minutes. This is what consistent practice looks like.",
    "Look at that. 30 minutes.",
    "Half an hour in. You're making this a habit.",
    "30 minutes. You stuck with it. That's the whole game.",
    "That's 30 minutes of English practice. Genuinely well done.",
    "You've been at it for 30 minutes. Give yourself some credit.",
    "30 minutes. Still in the channel. Love to see it.",
    "Half an hour of practice. That's not nothing. That's a lot.",
    "30 minutes in. You came, you stayed, you practiced.",
]

EN_ENGAGEMENT_QUESTIONS = [
    "What's something you did this week that you hadn't planned?",
    "If you could only eat one meal for a week, what would it be?",
    "What's a small thing that made you happy recently?",
    "What's a word in your language that doesn't exist in English?",
    "What's something you're looking forward to?",
    "What did you do last weekend?",
    "What's a movie or series you've watched recently?",
    "What's something you learned in the last month?",
    "If you had one extra hour today, what would you do with it?",
    "What's a place you really want to visit one day?",
    "What's your go-to food when you don't feel like cooking?",
    "What's something that's harder than it looks?",
    "What's a habit you've been trying to build?",
    "What's something that always makes you laugh?",
    "What would you do differently if you could redo yesterday?",
    "What's a skill you wish you had?",
    "What's the best advice someone gave you?",
    "What's something you're proud of from this year?",
    "What do you do to relax after a long day?",
    "What's a question you've always wanted to ask someone but haven't?",
    "What's something you used to believe that you don't anymore?",
    "What's the most interesting conversation you've had recently?",
    "What's a simple pleasure you really enjoy?",
    "If you could swap lives with someone for a day, who would it be?",
    "What's something people don't know about you?",
    "What's a sound that makes you feel calm?",
    "What's something that surprised you recently?",
    "What's a topic you could talk about for hours?",
    "What's something you want to get better at?",
    "What's a place that feels like home to you?",
    "Not sure what to talk about? Try /topics for some conversation starters.",
    "If the conversation has slowed down, /topics has questions ready to go.",
    "Want a conversation starter? Use /topics and pick a subject.",
]

NL_ENCOURAGEMENT_5MIN = [
    "5 minuten bezig. Goed dat je er bent.",
    "Je bent gekomen. Dat telt al.",
    "Mooi, 5 minuten. Ga zo door.",
    "Je zit in het kanaal. Dat is het moeilijkste deel.",
    "5 minuten. Je doet het.",
    "Fijn dat je er bent.",
    "Nog steeds hier na 5 minuten. Goed bezig.",
    "Je bent gekomen. Dat is meer waard dan je denkt.",
    "5 minuten oefening gedaan.",
    "Je dacht er niet alleen aan. Je hebt het ook gedaan.",
    "Hier ben je. Goed.",
    "5 minuten. Niet slecht.",
    "Je bent er in gekomen. Dat is wat telt.",
    "Goed dat je bent begonnen.",
    "5 minuten. Zo gaat vooruitgang.",
    "Je oefent. Zo simpel is het.",
    "Opdagen is het meeste. Je bent er.",
    "5 minuten. Elke sessie begint zo.",
    "Je bent in de kamer. Dat is echt.",
    "Mooi. 5 minuten echte spreekoefening.",
    "5 minuten. Hier gaat het om.",
    "Je wachtte niet op het perfecte moment. Je deed het gewoon.",
    "5 minuten. Ga zo door.",
    "Kijk je eens, gewoon komen opdagen.",
    "5 minuten in het kanaal. Goede start.",
    "Je oefent Nederlands op dit moment. Dat is het.",
    "5 minuten. Zin voor zin.",
    "Goed om iemand in hier te zien.",
    "5 minuten. Elke minuut telt.",
    "Je bent erin. Dat is alles wat nodig was.",
]

NL_ENCOURAGEMENT_30MIN = [
    "30 minuten. Dat is een echte sessie.",
    "Je bent hier al 30 minuten. Dat is echt knap.",
    "30 minuten spreekoefening. Goed gedaan.",
    "Nog steeds bezig na 30 minuten. Goed werk.",
    "30 minuten. Daar mag je trots op zijn.",
    "Een half uur Nederlands oefenen. Dat telt op.",
    "30 minuten erin. Je bent gekomen en gebleven. Dat is het moeilijke deel.",
    "30 minuten. Serieus, goed gedaan.",
    "Je oefent al 30 minuten. Dat vraagt inzet.",
    "30 minuten. De meeste mensen komen niet zo ver.",
    "Een half uur. Niet iedereen doet dat.",
    "30 minuten gespreksoefening. Dat is veel goed werk.",
    "Je bent er nog. 30 minuten. Respect.",
    "30 minuten in het kanaal. Dat is toewijding.",
    "Goed. 30 minuten. Ga door als je wilt.",
    "30 minuten. Dat heb je gedaan. Mooi.",
    "Een half uur echte oefening. Wees daar trots op.",
    "30 minuten. Elke minuut was nuttig.",
    "Nog steeds bezig na 30 minuten. Je doet het goed.",
    "30 minuten spreekoefening is geen kleine moeite.",
    "Je bent er een half uur. Dat is een echte sessie.",
    "30 minuten. Zo ziet consistent oefenen eruit.",
    "Kijk dat. 30 minuten.",
    "Een half uur bezig. Je maakt er een gewoonte van.",
    "30 minuten. Je bent gebleven. Dat is het hele verhaal.",
    "30 minuten Nederlands oefenen. Echt goed gedaan.",
    "Je bent al 30 minuten bezig. Gun jezelf wat credits.",
    "30 minuten. Nog in het kanaal. Fijn om te zien.",
    "Een half uur oefening. Dat is echt wat. Veel.",
    "30 minuten erin. Je bent gekomen, gebleven, geoefend.",
]

NL_ENGAGEMENT_QUESTIONS = [
    "Wat heb je deze week gedaan wat je niet had gepland?",
    "Als je een week lang maar een maaltijd mocht eten, wat zou het zijn?",
    "Wat is iets kleins dat je onlangs blij maakte?",
    "Wat is een woord in jouw taal dat niet bestaat in het Nederlands?",
    "Waar kijk je naar uit?",
    "Wat heb je afgelopen weekend gedaan?",
    "Welke film of serie heb je recentelijk gekeken?",
    "Wat heb je de afgelopen maand geleerd?",
    "Als je vandaag een extra uur had, wat zou je ermee doen?",
    "Welke plek wil je ooit echt bezoeken?",
    "Wat eet je als je geen zin hebt om te koken?",
    "Wat is iets dat moeilijker is dan het lijkt?",
    "Welke gewoonte probeer je op te bouwen?",
    "Wat zorgt er altijd voor dat je moet lachen?",
    "Wat zou je anders doen als je gisteren opnieuw kon doen?",
    "Welke vaardigheid zou je willen hebben?",
    "Wat is het beste advies dat iemand je ooit gaf?",
    "Waar ben je dit jaar trots op?",
    "Wat doe je om te ontspannen na een lange dag?",
    "Wat is een vraag die je altijd al aan iemand wilde stellen maar nog niet hebt gedaan?",
    "Wat is iets wat je vroeger geloofde maar nu niet meer?",
    "Wat is het interessantste gesprek dat je recentelijk hebt gehad?",
    "Wat is een eenvoudig genieten dat je echt leuk vindt?",
    "Als je voor een dag van leven kon ruilen met iemand, wie zou het zijn?",
    "Wat weten mensen niet over jou?",
    "Wat is een geluid dat je kalm maakt?",
    "Wat heeft je onlangs verrast?",
    "Over welk onderwerp kun je uren praten?",
    "Wat wil je beter leren?",
    "Weet je niet waarover praten? Gebruik /onderwerpen voor gespreksonderwerpen.",
    "Als het gesprek wat stilvalt, /onderwerpen heeft vragen klaarstaan.",
    "Wil je een gespreksopener? Gebruik /onderwerpen en kies een onderwerp.",
]

WEEKLY_DM_MESSAGE = (
    "👋 Hey! Noticed you hopped into voice this week — nice.\n"
    "If you feel like speaking, start tiny: one sentence is enough. No pressure."
)

INACTIVITY_MIN_DAYS = 14
INACTIVITY_COOLDOWN_DAYS = 30
NO_NUDGE_AFTER_SPEAK_SECONDS = 72 * 3600

INACTIVITY_MSG_A = (
    "If you ever feel like joining a table again, you don’t need to catch up or explain anything. You can just join."
)
INACTIVITY_MSG_B = (
    "No pressure to be consistent here. If you want to speak again sometime, you can just join and leave whenever."
)


class VoiceTracker:
    def __init__(
        self,
        repo: Repo,
        guild_id: int,
        speak_now_category_id: int,
        enable_inactivity_nudge: bool,
        inactivity_variant: str,
        afk_channel_id: int | None = None,
        dutch_guild_id: int | None = None,
        bot: discord.Client | None = None,
    ):
        self.repo = repo
        self.guild_id = guild_id
        self.speak_now_category_id = speak_now_category_id
        self.afk_channel_id = afk_channel_id
        self.dutch_guild_id = dutch_guild_id
        self._bot = bot

        self.active: Dict[int, Tuple[int, int]] = {}
        self._pending_first_attempt: Dict[int, asyncio.Task] = {}
        self._pending_encouragement: Dict[int, asyncio.Task] = {}
        self._last_engagement_at: Dict[int, float] = {}  # channel_id -> epoch
        self._weekly_dm_inflight: set[int] = set()

        self.enable_inactivity_nudge = enable_inactivity_nudge
        self.inactivity_variant = inactivity_variant

    def _is_afk_channel(self, guild: discord.Guild, channel: Optional[discord.abc.GuildChannel]) -> bool:
        if channel is None:
            return False

        # Prefer explicit AFK_CHANNEL_ID (works even if guild AFK isn't configured correctly)
        if self.afk_channel_id is not None:
            return bool(getattr(channel, "id", None) == self.afk_channel_id)

        # Fallback to Discord server AFK channel setting
        afk = getattr(guild, "afk_channel", None)
        return bool(afk and afk.id == getattr(channel, "id", None))

    def _is_target_voice_channel(self, guild: discord.Guild, channel) -> bool:
        if channel is None:
            return False
        # Accept channels in either the English or Dutch Spreek Nu category
        in_en = is_in_speak_now_category(channel, self.speak_now_category_id)
        in_nl = is_in_speak_now_category(channel, NL_VOICE_CATEGORY_ID)
        if not (in_en or in_nl):
            return False
        if self._is_afk_channel(guild, channel):
            return False
        return True

    def _is_nl_channel(self, channel) -> bool:
        """True if the channel belongs to the Dutch Spreek Nu category."""
        if channel is None:
            return False
        return bool(is_in_speak_now_category(channel, NL_VOICE_CATEGORY_ID))

    def _cancel_first_attempt_task(self, user_id: int) -> None:
        task = self._pending_first_attempt.pop(user_id, None)
        if task and not task.done():
            task.cancel()

    def _schedule_first_attempt_check(self, member: discord.Member, channel_id: int, started_at: int) -> None:
        uid = member.id
        self._cancel_first_attempt_task(uid)

        async def _job():
            try:
                await asyncio.sleep(FIRST_VOICE_ATTEMPT_CHECK_SECONDS)

                voice = member.voice
                if voice is None or voice.channel is None:
                    return
                if voice.channel.id != channel_id:
                    return
                if not self._is_target_voice_channel(member.guild, voice.channel):
                    return
                if not qualifies_first_voice_attempt(voice):
                    return

                newly_awarded = await self.repo.achievement_award_once(
                    guild_id=self.guild_id,
                    user_id=uid,
                    achievement_id=ACH_FIRST_VOICE_ATTEMPT,
                    earned_at=int(time.time()),
                )
                if newly_awarded:
                    log.info("Achievement awarded: %s user=%s", ACH_FIRST_VOICE_ATTEMPT, uid)

            except asyncio.CancelledError:
                return
            except Exception:
                log.exception("First voice attempt check failed for user=%s", uid)

        self._pending_first_attempt[uid] = asyncio.create_task(_job())

    async def _maybe_send_weekly_dm(self, member: discord.Member, now_epoch: int) -> None:
        uid = member.id
        if uid in self._weekly_dm_inflight:
            return

        self._weekly_dm_inflight.add(uid)
        try:
            week_key = amsterdam_iso_week_key()

            state = await self.repo.user_state_get(self.guild_id, uid)
            last_week = state["last_weekly_dm_week"] if state else None
            if last_week == week_key:
                return

            await self.repo.user_state_mark_weekly_dm(self.guild_id, uid, week_key, now_epoch)

            try:
                await member.send(WEEKLY_DM_MESSAGE)
                log.info("Weekly DM sent user=%s week=%s", uid, week_key)
            except discord.Forbidden:
                log.info("Weekly DM blocked by user privacy settings user=%s week=%s", uid, week_key)
            except discord.HTTPException:
                log.exception("Weekly DM failed (HTTPException) user=%s week=%s", uid, week_key)
            except Exception:
                log.exception("Weekly DM failed user=%s week=%s", uid, week_key)

        finally:
            self._weekly_dm_inflight.discard(uid)

    async def _maybe_send_inactivity_dm(self, member: discord.Member, now: int) -> None:
        if not self.enable_inactivity_nudge:
            return

        state = await self.repo.user_state_get(self.guild_id, member.id)
        if not state or not state.get("last_voice_join_at"):
            return

        last_join = int(state["last_voice_join_at"])
        last_nudge = state.get("last_inactivity_nudge_at")
        last_nudge = int(last_nudge) if last_nudge else None

        if now - last_join < INACTIVITY_MIN_DAYS * 86400:
            return
        if now - last_join < NO_NUDGE_AFTER_SPEAK_SECONDS:
            return
        if last_nudge and now - last_nudge < INACTIVITY_COOLDOWN_DAYS * 86400:
            return

        message = INACTIVITY_MSG_B if self.inactivity_variant == "B" else INACTIVITY_MSG_A

        await self.repo.user_state_mark_inactivity_nudge(self.guild_id, member.id, now)

        try:
            await member.send(message)
            log.info("Inactivity DM sent user=%s", member.id)
        except discord.Forbidden:
            log.info("Inactivity DM blocked by privacy user=%s", member.id)
        except Exception:
            log.exception("Inactivity DM failed user=%s", member.id)

    # -------------------------
    # Achievements (join-time; max 1 per join)
    # Priority:
    #   1) first_voice_attempt (handled separately; if not earned, suppress join-time awards)
    #   2) came_back_after_break
    #   3) joined_again
    #   4) spoke_with_someone_new
    # -------------------------
    async def _maybe_award_join_achievement(self, member: discord.Member, after_channel: discord.VoiceChannel, now: int) -> None:
        uid = member.id

        # Suppress join-time achievements until "first voice" is earned.
        has_first = await self.repo.achievement_has(self.guild_id, uid, ACH_FIRST_VOICE_ATTEMPT)
        if not has_first:
            return

        state = await self.repo.user_state_get(self.guild_id, uid)
        prev_last_join = int(state["last_voice_join_at"]) if state and state.get("last_voice_join_at") else None

        awarded = False

        # 1) Came back after a break (award on join; no time threshold)
        if not awarded and prev_last_join is not None:
            if now - prev_last_join >= BREAK_MIN_SECONDS:
                if not await self.repo.achievement_has(self.guild_id, uid, ACH_CAME_BACK_AFTER_BREAK):
                    if await self.repo.achievement_award_once(self.guild_id, uid, ACH_CAME_BACK_AFTER_BREAK, now):
                        log.info("Achievement awarded: %s user=%s", ACH_CAME_BACK_AFTER_BREAK, uid)
                        awarded = True

        # 2) Joined again (new Amsterdam day) with reconnection cooldown guardrail
        if not awarded and prev_last_join is not None:
            prev_day = amsterdam_day_key_from_epoch(prev_last_join)
            today = amsterdam_day_key()
            if prev_day != today and (now - prev_last_join) >= JOINED_AGAIN_MIN_GAP_SECONDS:
                if not await self.repo.achievement_has(self.guild_id, uid, ACH_JOINED_AGAIN):
                    if await self.repo.achievement_award_once(self.guild_id, uid, ACH_JOINED_AGAIN, now):
                        log.info("Achievement awarded: %s user=%s", ACH_JOINED_AGAIN, uid)
                        awarded = True

        # 3) Spoke with someone new (joining member only), with room-size guardrail
        if not awarded:
            # Only evaluate in small groups to prevent noisy/crowded-room awarding.
            humans = [m for m in after_channel.members if not m.bot]
            if len(humans) <= MAX_NEW_MEET_ROOM_SIZE:
                for other in humans:
                    if other.id == uid:
                        continue
                    is_new_pair = await self.repo.voice_met_add_if_new_pair(self.guild_id, uid, other.id, now)
                    if is_new_pair:
                        if not await self.repo.achievement_has(self.guild_id, uid, ACH_SPOKE_WITH_SOMEONE_NEW):
                            if await self.repo.achievement_award_once(self.guild_id, uid, ACH_SPOKE_WITH_SOMEONE_NEW, now):
                                log.info("Achievement awarded: %s user=%s other=%s", ACH_SPOKE_WITH_SOMEONE_NEW, uid, other.id)
                        awarded = True
                        break

    # -------------------------
    # Bootstrap / events
    # -------------------------
    async def bootstrap_from_guild(self, guild: discord.Guild) -> None:
        now = int(time.time())

        for vc in guild.voice_channels:
            for member in vc.members:
                await self.repo.end_open_session(self.guild_id, member.id, ended_at=now)

        # Start sessions for users currently in target category and not self-deafened
        # NOTE: no weekly DM, no inactivity DM, no join-achievements during bootstrap.
        for vc in guild.voice_channels:
            if not self._is_target_voice_channel(guild, vc):
                continue
            for member in vc.members:
                if member.bot:
                    continue

                await self.repo.user_state_touch_voice_join(self.guild_id, member.id, now)

                if not should_count_state(member.voice):
                    continue
                await self._start(member.id, vc.id, now)

                self._schedule_first_attempt_check(member, vc.id, now)

        log.info("Bootstrap complete. Active sessions: %s", len(self.active))

    async def handle_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.bot:
            return

        uid = member.id
        now = int(time.time())

        before_channel = before.channel
        after_channel = after.channel

        before_in_target = self._is_target_voice_channel(member.guild, before_channel)
        after_in_target = self._is_target_voice_channel(member.guild, after_channel)

        # Entering target voice: evaluate inactivity + achievements using PREVIOUS state, then update state.
        if not before_in_target and after_in_target and after_channel is not None:
            # Step 6 (gated)
            await self._maybe_send_inactivity_dm(member, now)

            # Achievements (join-time, max 1 per join)
            await self._maybe_award_join_achievement(member, after_channel, now)

            # Record join (this becomes the new last_voice_join_at)
            await self.repo.user_state_touch_voice_join(self.guild_id, uid, now)

            # Schedule first voice attempt check
            self._schedule_first_attempt_check(member, after_channel.id, now)

            # Weekly DM check
            await self._maybe_send_weekly_dm(member, now)

        # Cancel pending first-attempt checks if they leave target voice or move away.
        if before_in_target and not after_in_target:
            self._cancel_first_attempt_task(uid)
        elif before_in_target and after_in_target and before_channel and after_channel and before_channel.id != after_channel.id:
            self._cancel_first_attempt_task(uid)
            await self.repo.user_state_touch_voice_join(self.guild_id, uid, now)
            self._schedule_first_attempt_check(member, after_channel.id, now)

        # Existing "counted minutes" logic (unchanged)
        before_counts = before_in_target and should_count_state(before)
        after_counts = after_in_target and should_count_state(after)

        if before_counts and not after_counts:
            await self._end(uid, now)
            return

        if not before_counts and after_counts and after_channel is not None:
            await self._start(uid, after_channel.id, now)
            self._schedule_encouragement(member, after_channel.id)
            return

        if before_counts and after_counts and before_channel and after_channel and before_channel.id != after_channel.id:
            await self._end(uid, now)
            await self._start(uid, after_channel.id, now)
            self._schedule_encouragement(member, after_channel.id)
            return

    def _is_nl_guild(self) -> bool:
        return self.dutch_guild_id is not None and self.guild_id == self.dutch_guild_id

    def _cancel_encouragement_task(self, user_id: int) -> None:
        task = self._pending_encouragement.pop(user_id, None)
        if task and not task.done():
            task.cancel()

    def _schedule_encouragement(self, member: discord.Member, channel_id: int) -> None:
        if self._bot is None:
            return
        uid = member.id
        self._cancel_encouragement_task(uid)
        # Detect language by which category the channel belongs to
        channel = self._bot.get_channel(channel_id)
        is_nl = self._is_nl_channel(channel)
        msgs_5 = NL_ENCOURAGEMENT_5MIN if is_nl else EN_ENCOURAGEMENT_5MIN
        msgs_30 = NL_ENCOURAGEMENT_30MIN if is_nl else EN_ENCOURAGEMENT_30MIN
        msgs_engage = NL_ENGAGEMENT_QUESTIONS if is_nl else EN_ENGAGEMENT_QUESTIONS

        async def _job() -> None:
            try:
                # 5-minute encouragement
                await asyncio.sleep(5 * 60)

                voice = member.voice
                if voice is None or voice.channel is None or voice.channel.id != channel_id:
                    return

                vc = self._bot.get_channel(channel_id)
                if isinstance(vc, discord.VoiceChannel):
                    try:
                        await vc.send(f"{random.choice(msgs_5)} <@{uid}>")
                    except (discord.Forbidden, discord.HTTPException):
                        pass

                # Engagement question at a random point between 10 and 50 minutes
                # max one per channel per hour
                engage_wait = random.randint(5 * 60, 45 * 60)
                await asyncio.sleep(engage_wait)

                voice = member.voice
                if voice is None or voice.channel is None or voice.channel.id != channel_id:
                    return

                now = time.time()
                last = self._last_engagement_at.get(channel_id, 0)
                if now - last >= 3600:
                    vc = self._bot.get_channel(channel_id)
                    if isinstance(vc, discord.VoiceChannel):
                        try:
                            await vc.send(random.choice(msgs_engage))
                            self._last_engagement_at[channel_id] = now
                        except (discord.Forbidden, discord.HTTPException):
                            pass

                # 30-minute encouragement (wait remaining time from 5min mark)
                elapsed = 5 * 60 + engage_wait
                remaining = max(0, 30 * 60 - elapsed)
                await asyncio.sleep(remaining)

                voice = member.voice
                if voice is None or voice.channel is None or voice.channel.id != channel_id:
                    return

                vc = self._bot.get_channel(channel_id)
                if isinstance(vc, discord.VoiceChannel):
                    try:
                        await vc.send(f"{random.choice(msgs_30)} <@{uid}>")
                    except (discord.Forbidden, discord.HTTPException):
                        pass

            except asyncio.CancelledError:
                return
            except Exception:
                log.exception("Encouragement task failed user=%s", uid)

        self._pending_encouragement[uid] = asyncio.create_task(_job())

    async def _start(self, user_id: int, channel_id: int, started_at: int) -> None:
        self.active[user_id] = (channel_id, started_at)
        await self.repo.start_session(self.guild_id, user_id, channel_id, started_at)
        log.debug("Start session user=%s channel=%s", user_id, channel_id)

    async def _end(self, user_id: int, ended_at: int) -> None:
        self.active.pop(user_id, None)
        self._cancel_encouragement_task(user_id)
        await self.repo.end_open_session(self.guild_id, user_id, ended_at)
        log.debug("End session user=%s", user_id)

    async def shutdown(self) -> None:
        for uid in list(self._pending_first_attempt.keys()):
            self._cancel_first_attempt_task(uid)
        for uid in list(self._pending_encouragement.keys()):
            self._cancel_encouragement_task(uid)