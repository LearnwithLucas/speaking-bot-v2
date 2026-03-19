from __future__ import annotations

# jobs/partner_finder.py
import asyncio
import logging
import time

import discord

from db.repo import Repo

log = logging.getLogger("jobs.partner_finder")

LOOKING_FOR_PARTNER_CHANNEL_ID = 1435902125652578434
PRACTICE_VOICE_CHANNEL_IDS = [
    1274733631298076745,  # ☕ | Drop In and Talk
    1456551629301219420,  # 🌍 | Open Conversation
]

KV_PARTNER_HUB_MSG_ID = "partner_hub_message_id"

AVAILABLE_FOR_SECONDS = 30 * 60  # 30 minutes


def _voice_links() -> str:
    return " or ".join(f"<#{vc_id}>" for vc_id in PRACTICE_VOICE_CHANNEL_IDS)


# =====================
# HUB EMBED
# =====================

def build_hub_embed(available_count: int = 0) -> discord.Embed:
    if available_count == 0:
        status = "Nobody is available right now. Press the button to be the first."
    elif available_count == 1:
        status = "1 person is free to practice right now."
    else:
        status = f"{available_count} people are free to practice right now."

    embed = discord.Embed(
        title="🤝 Find a speaking partner",
        description=(
            "Press the button when you feel like practicing.\n"
            "If someone else is free at the same time, you both get a DM.\n"
            "Your availability lasts 30 minutes.\n\n"
            f"**Right now:** {status}"
        ),
    )
    embed.set_footer(text="hub:en:partner:v2")
    return embed


# =====================
# PERSISTENT HUB VIEW
# =====================

class PartnerHubView(discord.ui.View):
    """Persistent view in #looking-for-a-partner."""

    def __init__(self, *, finder: "PartnerFinder | None" = None) -> None:
        super().__init__(timeout=None)
        self._finder = finder

    @discord.ui.button(
        label="I'm free to practice",
        style=discord.ButtonStyle.success,
        emoji="🙋",
        custom_id="partner:free_now:v2",
    )
    async def free_now(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self._finder is None:
            await interaction.response.send_message(
                "Not ready yet. Try again in a moment.", ephemeral=True
            )
            return

        await self._finder.mark_available(
            user=interaction.user,
            guild=interaction.guild,
            interaction=interaction,
        )


# =====================
# CORE SERVICE
# =====================

class PartnerFinder:
    def __init__(
        self,
        *,
        bot: discord.Client,
        repo: Repo,
        guild_id: int,
    ) -> None:
        self.bot = bot
        self.repo = repo
        self.guild_id = guild_id

        # user_id -> expires_at (epoch)
        self._available: dict[int, float] = {}

    # ---- Availability ----

    def _clean_expired(self) -> None:
        now = time.time()
        expired = [uid for uid, exp in self._available.items() if now >= exp]
        for uid in expired:
            del self._available[uid]

    def _available_users(self) -> list[int]:
        self._clean_expired()
        return list(self._available.keys())

    async def mark_available(
        self,
        *,
        user: discord.User | discord.Member,
        guild: discord.Guild | None,
        interaction: discord.Interaction,
    ) -> None:
        self._clean_expired()
        uid = user.id
        now = time.time()

        # Already available — just refresh their timer
        already_available = uid in self._available
        self._available[uid] = now + AVAILABLE_FOR_SECONDS

        # Find other available users to match with
        others = [u for u in self._available_users() if u != uid]

        if already_available:
            await interaction.response.send_message(
                "You're still marked as free. Your 30 minutes has been refreshed.\n"
                f"{'Someone else is also free right now.' if others else 'Nobody else is free yet. You will get a DM when someone joins.'}",
                ephemeral=True,
            )
        elif others:
            await interaction.response.send_message(
                f"You're free to practice. {len(others)} {'person is' if len(others) == 1 else 'people are'} also free right now.\n"
                "Check your DMs.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "You're marked as free for the next 30 minutes.\n"
                "You will get a DM as soon as someone else is free too.",
                ephemeral=True,
            )

        # Update hub embed with new count
        await self._update_hub_embed()

        # DM matches
        if others and guild:
            await self._notify_matches(
                new_user=user,
                match_ids=others,
                guild=guild,
            )

        # Schedule expiry refresh
        asyncio.create_task(self._expire_after(uid, AVAILABLE_FOR_SECONDS))

    async def _expire_after(self, user_id: int, seconds: float) -> None:
        await asyncio.sleep(seconds)
        self._available.pop(user_id, None)
        await self._update_hub_embed()
        log.info("PartnerFinder: availability expired user=%s", user_id)

    async def _notify_matches(
        self,
        *,
        new_user: discord.User | discord.Member,
        match_ids: list[int],
        guild: discord.Guild,
    ) -> None:
        links = _voice_links()

        # DM the person who just pressed the button
        names = []
        for mid in match_ids[:3]:
            try:
                m = guild.get_member(mid) or await guild.fetch_member(mid)
                names.append(m.display_name)
            except Exception:
                pass
        names_str = ", ".join(names) if names else "someone"
        verb = "is" if len(names) == 1 else "are"

        try:
            await new_user.send(
                f"🤝 **Partner match!**\n\n"
                f"**{names_str}** {verb} also free right now.\n\n"
                f"Jump into {links} and start talking. ☕"
            )
        except discord.Forbidden:
            log.info("PartnerFinder: DM blocked user=%s", new_user.id)
        except Exception:
            log.exception("PartnerFinder: failed to DM new user=%s", new_user.id)

        # DM the existing available users
        for match_id in match_ids:
            try:
                match_member = guild.get_member(match_id) or await guild.fetch_member(match_id)
                await match_member.send(
                    f"🤝 **Partner match!**\n\n"
                    f"**{new_user.display_name}** is free to practice right now.\n\n"
                    f"Jump into {links} and start talking. ☕"
                )
            except discord.Forbidden:
                log.info("PartnerFinder: DM blocked match=%s", match_id)
            except Exception:
                log.exception("PartnerFinder: failed to DM match=%s", match_id)

    # ---- Hub embed ----

    async def _update_hub_embed(self) -> None:
        self._clean_expired()
        count = len(self._available)

        channel = self.bot.get_channel(LOOKING_FOR_PARTNER_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(LOOKING_FOR_PARTNER_CHANNEL_ID)
            except Exception:
                return

        if not isinstance(channel, discord.TextChannel):
            return

        existing_id_raw = await self.repo.kv_get(self.guild_id, KV_PARTNER_HUB_MSG_ID)
        if not existing_id_raw:
            return

        try:
            msg = await channel.fetch_message(int(existing_id_raw))
            await msg.edit(
                embed=build_hub_embed(count),
                view=PartnerHubView(finder=self),
            )
        except Exception:
            log.warning("PartnerFinder: could not update hub embed")

    async def publish_hub(self) -> None:
        channel = self.bot.get_channel(LOOKING_FOR_PARTNER_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(LOOKING_FOR_PARTNER_CHANNEL_ID)
            except Exception:
                log.warning("PartnerFinder: could not fetch channel %s", LOOKING_FOR_PARTNER_CHANNEL_ID)
                return

        if not isinstance(channel, discord.TextChannel):
            return

        embed = build_hub_embed(0)
        view = PartnerHubView(finder=self)

        existing_id_raw = await self.repo.kv_get(self.guild_id, KV_PARTNER_HUB_MSG_ID)
        if existing_id_raw:
            try:
                msg = await channel.fetch_message(int(existing_id_raw))
                await msg.edit(embed=embed, view=view)
                log.info("PartnerFinder: updated hub message %s", existing_id_raw)
                return
            except Exception:
                log.warning("PartnerFinder: could not edit hub message, recreating")

        try:
            sent = await channel.send(embed=embed, view=view)
            await self.repo.kv_set(self.guild_id, KV_PARTNER_HUB_MSG_ID, str(sent.id))
            log.info("PartnerFinder: posted hub message %s", sent.id)
            try:
                await sent.pin()
            except discord.Forbidden:
                log.warning("PartnerFinder: missing pin permission")
            except Exception:
                log.warning("PartnerFinder: could not pin hub message")
        except Exception:
            log.exception("PartnerFinder: failed to post hub message")