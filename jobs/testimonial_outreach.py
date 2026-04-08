from __future__ import annotations

# jobs/testimonial_outreach.py
import asyncio
import logging
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import tasks

log = logging.getLogger("jobs.testimonial_outreach")

# ---- Config ----
EN_GUILD_ID = 1181652389732831323
NL_GUILD_ID = 1336419808811679754
ADMIN_LOG_CHANNEL_ID = 1490322440788644011   # 🌱┃collected-testimonials

MESSAGE_THRESHOLD = 15          # messages in guild before eligible
VOICE_HOURS_THRESHOLD = 3       # cumulative voice hours before eligible
COOLDOWN_DAYS = 180             # 6 months before re-sending

TZ_NAME = "Europe/Amsterdam"
# Run twice a day: 10:00 and 18:00
CHECK_HOURS = {10, 18}

KV_PREFIX = "testimonial_dm_sent:"   # key = f"{KV_PREFIX}{user_id}"


def _get_tz() -> ZoneInfo:
    try:
        return ZoneInfo(TZ_NAME)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _kv_key(user_id: int) -> str:
    return f"{KV_PREFIX}{user_id}"


# ---- DM content ----

EN_STORY_URL = "https://discord.com/channels/1181652389732831323/1490320758507962490/1490341318801756402"
NL_STORY_URL = "https://discord.com/channels/1336419808811679754/1490320826027741185/1490341327362195606"


class ShareStoryViewEN(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="Share my story ✍️",
            style=discord.ButtonStyle.link,
            url=EN_STORY_URL,
        ))


class ShareStoryViewNL(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="Deel mijn verhaal ✍️",
            style=discord.ButtonStyle.link,
            url=NL_STORY_URL,
        ))


def _build_dm_embed_en(member: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="🌟 Would you share your story?",
        description=(
            f"Hey {member.display_name}!\n\n"
            "You've been a wonderful part of our community. "
            "Your story could inspire others to join and learn.\n\n"
            "Would you share your success? Here's a quick template — just answer what you like:\n\n"
            "**1.** What's one thing you're proud of since joining?\n"
            "**2.** How has practicing here helped you?\n"
            "**3.** How would you describe your progress to a friend?\n\n"
            "It takes less than 2 minutes and you choose whether it stays private or gets shared. "
            "Head to the **#your-successes-and-stories** channel and press **Share my story** 🌟"
        ),
        color=discord.Color.gold(),
    )
    embed.set_footer(text="You can always keep it private — the choice is yours.")
    return embed


def _build_dm_embed_nl(member: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="🌟 Wil je jouw verhaal delen?",
        description=(
            f"Hey {member.display_name}!\n\n"
            "Je bent een geweldig onderdeel van onze community. "
            "Jouw verhaal kan anderen inspireren om ook mee te doen en te leren.\n\n"
            "Wil je jouw succes delen? Hier is een kleine template — beantwoord wat je wilt:\n\n"
            "**1.** Wat is iets waar je trots op bent sinds je lid bent geworden?\n"
            "**2.** Hoe heeft het oefenen hier jou geholpen?\n"
            "**3.** Hoe zou je jouw vooruitgang omschrijven aan een vriend?\n\n"
            "Het duurt minder dan 2 minuten en jij kiest of het privé blijft of gedeeld wordt. "
            "Ga naar **#jouw-successen-en-verhalen** en druk op **Deel mijn verhaal** 🌟"
        ),
        color=discord.Color.gold(),
    )
    embed.set_footer(text="Je kunt het altijd privé houden — de keuze is aan jou.")
    return embed


async def _count_recent_messages(guild: discord.Guild, member: discord.Member) -> int:
    """Count messages sent by member across all text channels. Capped at threshold+1 for efficiency."""
    count = 0
    for channel in guild.text_channels:
        try:
            async for msg in channel.history(limit=200, oldest_first=False):
                if msg.author.id == member.id:
                    count += 1
                    if count > MESSAGE_THRESHOLD:
                        return count
        except (discord.Forbidden, discord.HTTPException):
            continue
        except Exception:
            continue
    return count


class TestimonialOutreachJob:
    def __init__(
        self,
        *,
        bot: discord.Client,
        repo,
        en_guild_id: int = EN_GUILD_ID,
        nl_guild_id: int = NL_GUILD_ID,
    ) -> None:
        self._bot = bot
        self._repo = repo
        self._en_guild_id = en_guild_id
        self._nl_guild_id = nl_guild_id
        self._tz = _get_tz()
        self._last_run_hour: int | None = None
        self._tick.start()

    def _now(self) -> int:
        return int(time.time())

    @tasks.loop(minutes=1)
    async def _tick(self) -> None:
        now_dt = discord.utils.utcnow().astimezone(self._tz)
        if now_dt.hour not in CHECK_HOURS or now_dt.minute != 0:
            return
        if self._last_run_hour == now_dt.hour:
            return
        self._last_run_hour = now_dt.hour
        log.info("TestimonialOutreach: starting check hour=%s", now_dt.hour)
        await self._run_check()

    @_tick.before_loop
    async def _before(self) -> None:
        await self._bot.wait_until_ready()

    async def _run_check(self) -> None:
        for guild_id, is_nl in [(self._en_guild_id, False), (self._nl_guild_id, True)]:
            guild = self._bot.get_guild(guild_id)
            if not guild:
                log.warning("TestimonialOutreach: guild %s not found", guild_id)
                continue
            try:
                await self._check_guild(guild, guild_id, is_nl)
            except Exception:
                log.exception("TestimonialOutreach: error in guild %s", guild_id)

    async def _check_guild(
        self, guild: discord.Guild, guild_id: int, is_nl: bool
    ) -> None:
        now = self._now()
        cooldown_seconds = COOLDOWN_DAYS * 86400
        sent_count = 0

        for member in guild.members:
            if member.bot:
                continue

            # Check KV cooldown
            kv_key = _kv_key(member.id)
            try:
                last_sent_str = await self._repo.kv_get(guild_id, kv_key)
                if last_sent_str:
                    last_sent = int(last_sent_str)
                    if now - last_sent < cooldown_seconds:
                        continue
            except Exception:
                continue

            # Check voice hours (cumulative seconds from repo)
            qualified_by_voice = False
            try:
                total_seconds = await self._repo.compute_and_cache_total_seconds(
                    guild_id, member.id
                )
                if total_seconds >= VOICE_HOURS_THRESHOLD * 3600:
                    qualified_by_voice = True
            except Exception:
                pass

            # Check message count (only if not already qualified by voice)
            qualified_by_messages = False
            if not qualified_by_voice:
                try:
                    msg_count = await _count_recent_messages(guild, member)
                    if msg_count >= MESSAGE_THRESHOLD:
                        qualified_by_messages = True
                except Exception:
                    pass

            if not qualified_by_voice and not qualified_by_messages:
                continue

            # Send DM
            try:
                embed = _build_dm_embed_nl(member) if is_nl else _build_dm_embed_en(member)
                await member.send(embed=embed)
                log.info(
                    "TestimonialOutreach: DM sent user=%s guild=%s reason=%s",
                    member.id, guild_id,
                    "voice" if qualified_by_voice else "messages",
                )

                # Store timestamp in KV
                await self._repo.kv_set(guild_id, kv_key, str(now))
                sent_count += 1

                # Log to admin channel
                await self._log_dm_sent(member, is_nl, qualified_by_voice)

                # Small delay to avoid rate limiting
                await asyncio.sleep(1.5)

            except discord.Forbidden:
                log.info("TestimonialOutreach: DM blocked by user=%s", member.id)
            except Exception:
                log.exception("TestimonialOutreach: failed to DM user=%s", member.id)

        log.info(
            "TestimonialOutreach: guild=%s sent=%s", guild_id, sent_count
        )

    async def _log_dm_sent(
        self,
        member: discord.Member,
        is_nl: bool,
        by_voice: bool,
    ) -> None:
        try:
            ch = self._bot.get_channel(ADMIN_LOG_CHANNEL_ID)
            if ch is None:
                ch = await self._bot.fetch_channel(ADMIN_LOG_CHANNEL_ID)
            if not isinstance(ch, discord.TextChannel):
                return
            reason = (
                f"{'🎙️ Spraaktijd' if is_nl else '🎙️ Voice time'} ≥ {VOICE_HOURS_THRESHOLD}h"
                if by_voice else
                f"{'💬 Berichten' if is_nl else '💬 Messages'} ≥ {MESSAGE_THRESHOLD}"
            )
            lang = "NL" if is_nl else "EN"
            await ch.send(
                f"📨 DM verzonden naar" if is_nl else f"📨 DM sent to"
                f" **{member.display_name}** (`{member.id}`) [{lang}] — {reason}"
            )
        except Exception:
            log.exception("TestimonialOutreach: failed to log DM for user=%s", member.id)

    def stop(self) -> None:
        self._tick.cancel()