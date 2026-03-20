from __future__ import annotations

# jobs/partner_finder.py
import asyncio
import logging
import time

import discord

from db.repo import Repo

log = logging.getLogger("jobs.partner_finder")

# ---- Channel IDs ----
EN_LOOKING_CHANNEL_ID = 1435902125652578434   # 🙋┃looking-for-a-partner
NL_LOOKING_CHANNEL_ID = 1484566832982654996   # 🙋┃op-zoek-naar-een-partner

EN_PRACTICE_VOICE_IDS = [
    1274733631298076745,  # ☕ | Drop In and Talk
    1456551629301219420,  # 🌍 | Open Conversation
]

NL_PRACTICE_VOICE_IDS = [
    1274733631298076745,  # same voice channels for now — update if NL gets dedicated ones
]

KV_EN_HUB_MSG_ID = "partner_hub_message_id"
KV_NL_HUB_MSG_ID = "partner_hub_nl_message_id"

AVAILABLE_FOR_SECONDS = 30 * 60  # 30 minutes


def _voice_links(is_nl: bool = False) -> str:
    ids = NL_PRACTICE_VOICE_IDS if is_nl else EN_PRACTICE_VOICE_IDS
    return " or ".join(f"<#{vc_id}>" for vc_id in ids)


# =====================
# HUB EMBEDS
# =====================

def build_en_embed(available_count: int = 0) -> discord.Embed:
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


def build_nl_embed(available_count: int = 0) -> discord.Embed:
    if available_count == 0:
        status = "Er is nu niemand beschikbaar. Druk op de knop om de eerste te zijn."
    elif available_count == 1:
        status = "1 persoon is nu vrij om te oefenen."
    else:
        status = f"{available_count} mensen zijn nu vrij om te oefenen."

    embed = discord.Embed(
        title="🤝 Vind een spreekpartner",
        description=(
            "Druk op de knop als je zin hebt om te oefenen.\n"
            "Als iemand anders ook vrij is, krijgen jullie allebei een DM.\n"
            "Je beschikbaarheid duurt 30 minuten.\n\n"
            f"**Op dit moment:** {status}"
        ),
    )
    embed.set_footer(text="hub:nl:partner:v2")
    return embed


# =====================
# PERSISTENT HUB VIEWS
# =====================

class PartnerHubView(discord.ui.View):
    """English persistent view in #looking-for-a-partner."""

    def __init__(self, *, finder: "PartnerFinder | None" = None) -> None:
        super().__init__(timeout=None)
        self._finder = finder

    @discord.ui.button(
        label="I'm free to practice",
        style=discord.ButtonStyle.success,
        emoji="🙋",
        custom_id="partner:free_now:en:v2",
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
            is_nl=False,
        )


class PartnerHubViewNL(discord.ui.View):
    """Dutch persistent view in #op-zoek-naar-een-partner."""

    def __init__(self, *, finder: "PartnerFinder | None" = None) -> None:
        super().__init__(timeout=None)
        self._finder = finder

    @discord.ui.button(
        label="Ik ben vrij om te oefenen",
        style=discord.ButtonStyle.success,
        emoji="🙋",
        custom_id="partner:free_now:nl:v2",
    )
    async def free_now_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self._finder is None:
            await interaction.response.send_message(
                "Nog niet klaar. Probeer het zo opnieuw.", ephemeral=True
            )
            return
        await self._finder.mark_available(
            user=interaction.user,
            guild=interaction.guild,
            interaction=interaction,
            is_nl=True,
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
        dutch_guild_id: int | None = None,
    ) -> None:
        self.bot = bot
        self.repo = repo
        self.guild_id = guild_id
        self.dutch_guild_id = dutch_guild_id

        # Separate availability dicts per server
        # user_id -> expires_at (epoch)
        self._available_en: dict[int, float] = {}
        self._available_nl: dict[int, float] = {}

    def _pool(self, is_nl: bool) -> dict[int, float]:
        return self._available_nl if is_nl else self._available_en

    def _clean_expired(self, is_nl: bool) -> None:
        pool = self._pool(is_nl)
        now = time.time()
        for uid in [uid for uid, exp in pool.items() if now >= exp]:
            del pool[uid]

    def _available_users(self, is_nl: bool) -> list[int]:
        self._clean_expired(is_nl)
        return list(self._pool(is_nl).keys())

    async def mark_available(
        self,
        *,
        user: discord.User | discord.Member,
        guild: discord.Guild | None,
        interaction: discord.Interaction,
        is_nl: bool = False,
    ) -> None:
        pool = self._pool(is_nl)
        self._clean_expired(is_nl)
        uid = user.id
        now = time.time()

        already_available = uid in pool
        pool[uid] = now + AVAILABLE_FOR_SECONDS

        others = [u for u in self._available_users(is_nl) if u != uid]

        if is_nl:
            if already_available:
                msg = (
                    "Je bent nog steeds beschikbaar. Je 30 minuten zijn verlengd.\n"
                    + ("Er is ook iemand anders vrij." if others else "Er is nog niemand anders vrij. Je krijgt een DM zodra iemand zich aanmeldt.")
                )
            elif others:
                count = len(others)
                msg = (
                    f"Je bent vrij om te oefenen. {count} {'persoon is' if count == 1 else 'mensen zijn'} ook vrij.\n"
                    "Bekijk je DMs."
                )
            else:
                msg = (
                    "Je bent de komende 30 minuten beschikbaar.\n"
                    "Je krijgt een DM zodra iemand anders ook vrij is."
                )
        else:
            if already_available:
                msg = (
                    "You're still marked as free. Your 30 minutes has been refreshed.\n"
                    + ("Someone else is also free right now." if others else "Nobody else is free yet. You will get a DM when someone joins.")
                )
            elif others:
                count = len(others)
                msg = (
                    f"You're free to practice. {count} {'person is' if count == 1 else 'people are'} also free right now.\n"
                    "Check your DMs."
                )
            else:
                msg = (
                    "You're marked as free for the next 30 minutes.\n"
                    "You will get a DM as soon as someone else is free too."
                )

        await interaction.response.send_message(msg, ephemeral=True)
        await self._update_hub_embed(is_nl=is_nl)

        if others and guild:
            await self._notify_matches(
                new_user=user,
                match_ids=others,
                guild=guild,
                is_nl=is_nl,
            )

        asyncio.create_task(self._expire_after(uid, AVAILABLE_FOR_SECONDS, is_nl=is_nl))

    async def _expire_after(self, user_id: int, seconds: float, *, is_nl: bool) -> None:
        await asyncio.sleep(seconds)
        self._pool(is_nl).pop(user_id, None)
        await self._update_hub_embed(is_nl=is_nl)
        log.info("PartnerFinder: availability expired user=%s is_nl=%s", user_id, is_nl)

    async def _notify_matches(
        self,
        *,
        new_user: discord.User | discord.Member,
        match_ids: list[int],
        guild: discord.Guild,
        is_nl: bool,
    ) -> None:
        links = _voice_links(is_nl)

        names = []
        for mid in match_ids[:3]:
            try:
                m = guild.get_member(mid) or await guild.fetch_member(mid)
                names.append(m.display_name)
            except Exception:
                pass
        names_str = ", ".join(names) if names else ("iemand" if is_nl else "someone")
        verb = "is" if len(names) == 1 else "are"
        verb_nl = "is" if len(names) == 1 else "zijn"

        try:
            if is_nl:
                await new_user.send(
                    f"🤝 **Spreekpartner gevonden!**\n\n"
                    f"**{names_str}** {verb_nl} ook vrij op dit moment.\n\n"
                    f"Spring in {links} en begin te praten. ☕"
                )
            else:
                await new_user.send(
                    f"🤝 **Partner match!**\n\n"
                    f"**{names_str}** {verb} also free right now.\n\n"
                    f"Jump into {links} and start talking. ☕"
                )
        except discord.Forbidden:
            log.info("PartnerFinder: DM blocked user=%s", new_user.id)
        except Exception:
            log.exception("PartnerFinder: failed to DM new user=%s", new_user.id)

        for match_id in match_ids:
            try:
                match_member = guild.get_member(match_id) or await guild.fetch_member(match_id)
                if is_nl:
                    await match_member.send(
                        f"🤝 **Spreekpartner gevonden!**\n\n"
                        f"**{new_user.display_name}** is nu vrij om te oefenen.\n\n"
                        f"Spring in {links} en begin te praten. ☕"
                    )
                else:
                    await match_member.send(
                        f"🤝 **Partner match!**\n\n"
                        f"**{new_user.display_name}** is free to practice right now.\n\n"
                        f"Jump into {links} and start talking. ☕"
                    )
            except discord.Forbidden:
                log.info("PartnerFinder: DM blocked match=%s", match_id)
            except Exception:
                log.exception("PartnerFinder: failed to DM match=%s", match_id)

    # ---- Hub embeds ----

    async def _update_hub_embed(self, *, is_nl: bool) -> None:
        self._clean_expired(is_nl)
        count = len(self._pool(is_nl))
        channel_id = NL_LOOKING_CHANNEL_ID if is_nl else EN_LOOKING_CHANNEL_ID
        kv_key = KV_NL_HUB_MSG_ID if is_nl else KV_EN_HUB_MSG_ID
        guild_id = self.dutch_guild_id if is_nl else self.guild_id

        if guild_id is None:
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception:
                return

        if not isinstance(channel, discord.TextChannel):
            return

        existing_id_raw = await self.repo.kv_get(guild_id, kv_key)
        if not existing_id_raw:
            return

        embed = build_nl_embed(count) if is_nl else build_en_embed(count)
        view = PartnerHubViewNL(finder=self) if is_nl else PartnerHubView(finder=self)

        try:
            msg = await channel.fetch_message(int(existing_id_raw))
            await msg.edit(embed=embed, view=view)
        except Exception:
            log.warning("PartnerFinder: could not update hub embed is_nl=%s", is_nl)

    async def publish_hub(self, *, is_nl: bool = False) -> None:
        channel_id = NL_LOOKING_CHANNEL_ID if is_nl else EN_LOOKING_CHANNEL_ID
        kv_key = KV_NL_HUB_MSG_ID if is_nl else KV_EN_HUB_MSG_ID
        guild_id = self.dutch_guild_id if is_nl else self.guild_id

        if guild_id is None:
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception:
                log.warning("PartnerFinder: could not fetch channel %s", channel_id)
                return

        if not isinstance(channel, discord.TextChannel):
            return

        embed = build_nl_embed(0) if is_nl else build_en_embed(0)
        view = PartnerHubViewNL(finder=self) if is_nl else PartnerHubView(finder=self)

        existing_id_raw = await self.repo.kv_get(guild_id, kv_key)
        if existing_id_raw:
            try:
                msg = await channel.fetch_message(int(existing_id_raw))
                await msg.edit(embed=embed, view=view)
                log.info("PartnerFinder: updated hub message %s is_nl=%s", existing_id_raw, is_nl)
                return
            except Exception:
                log.warning("PartnerFinder: could not edit hub message, recreating is_nl=%s", is_nl)

        try:
            sent = await channel.send(embed=embed, view=view)
            await self.repo.kv_set(guild_id, kv_key, str(sent.id))
            log.info("PartnerFinder: posted hub message %s is_nl=%s", sent.id, is_nl)
            try:
                await sent.pin()
            except discord.Forbidden:
                log.warning("PartnerFinder: missing pin permission channel=%s", channel_id)
            except Exception:
                log.warning("PartnerFinder: could not pin hub message")
        except Exception:
            log.exception("PartnerFinder: failed to post hub message is_nl=%s", is_nl)