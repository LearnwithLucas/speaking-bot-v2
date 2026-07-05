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
OPEN_CONVERSATION_CHANNEL_ID = 1456551629301219420  # 🌍 | Open Conversation

KV_EN_HUB_MSG_ID = "partner_hub_message_id"
KV_NL_HUB_MSG_ID = "partner_hub_nl_message_id"

DURATION_OPTIONS: tuple[tuple[int, str, str], ...] = (
    (15 * 60, "15 min", "15 min"),
    (30 * 60, "30 min", "30 min"),
    (45 * 60, "45 min", "45 min"),
    (60 * 60, "1 hour", "1 uur"),
    (2 * 60 * 60, "2 hours", "2 uur"),
    (3 * 60 * 60, "3 hours", "3 uur"),
)
DEFAULT_DURATION_SECONDS = 30 * 60


def _duration_label(seconds: int, *, is_nl: bool = False) -> str:
    for option_seconds, en_label, nl_label in DURATION_OPTIONS:
        if option_seconds == seconds:
            return nl_label if is_nl else en_label
    minutes = max(1, int(seconds / 60))
    if minutes < 60:
        return f"{minutes} min"
    hours = round(minutes / 60, 1)
    if is_nl:
        return f"{hours:g} uur"
    return f"{hours:g} hour" if hours == 1 else f"{hours:g} hours"


def _open_conversation_link(guild_id: int) -> str:
    return f"https://discord.com/channels/{guild_id}/{OPEN_CONVERSATION_CHANNEL_ID}"


# =====================
# HUB EMBEDS
# =====================

def build_en_embed(available_count: int = 0) -> discord.Embed:
    if available_count == 0:
        status = "Nobody is available right now. Press a time button to be the first."
    elif available_count == 1:
        status = "1 person is free to practice right now."
    else:
        status = f"{available_count} people are free to practice right now."

    embed = discord.Embed(
        title="🤝 Find a speaking partner",
        description=(
            "Choose how long you are available to practice.\n"
            "If someone else is free at the same time, you both get a DM with the Open Conversation channel.\n"
            "You can refresh or change your time whenever you want.\n\n"
            f"**Right now:** {status}"
        ),
    )
    embed.set_footer(text="hub:en:partner:v3")
    return embed


def build_nl_embed(available_count: int = 0) -> discord.Embed:
    if available_count == 0:
        status = "Er is nu niemand beschikbaar. Druk op een tijdknop om de eerste te zijn."
    elif available_count == 1:
        status = "1 persoon is nu vrij om te oefenen."
    else:
        status = f"{available_count} mensen zijn nu vrij om te oefenen."

    embed = discord.Embed(
        title="🤝 Vind een spreekpartner",
        description=(
            "Kies hoe lang je beschikbaar bent om te oefenen.\n"
            "Als iemand anders ook vrij is, krijgen jullie allebei een DM met het Open Conversation kanaal.\n"
            "Je kunt je tijd altijd vernieuwen of aanpassen.\n\n"
            f"**Op dit moment:** {status}"
        ),
    )
    embed.set_footer(text="hub:nl:partner:v3")
    return embed


# =====================
# PERSISTENT HUB VIEWS
# =====================

class PartnerHubView(discord.ui.View):
    """English persistent view in #looking-for-a-partner."""

    def __init__(self, *, finder: "PartnerFinder | None" = None) -> None:
        super().__init__(timeout=None)
        self._finder = finder

    async def _mark(self, interaction: discord.Interaction, *, duration_seconds: int) -> None:
        if self._finder is None:
            await interaction.response.send_message(
                "Not ready yet. Try again in a moment.", ephemeral=True
            )
            return
        await self._finder.mark_available(
            user=interaction.user,
            guild=interaction.guild,
            interaction=interaction,
            duration_seconds=duration_seconds,
            is_nl=False,
        )

    @discord.ui.button(label="15 min", style=discord.ButtonStyle.secondary, custom_id="partner:free:en:15m:v3", row=0)
    async def free_15(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=15 * 60)

    @discord.ui.button(label="30 min", style=discord.ButtonStyle.success, custom_id="partner:free:en:30m:v3", row=0)
    async def free_30(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=30 * 60)

    @discord.ui.button(label="45 min", style=discord.ButtonStyle.secondary, custom_id="partner:free:en:45m:v3", row=0)
    async def free_45(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=45 * 60)

    @discord.ui.button(label="1 hour", style=discord.ButtonStyle.secondary, custom_id="partner:free:en:1h:v3", row=1)
    async def free_1h(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=60 * 60)

    @discord.ui.button(label="2 hours", style=discord.ButtonStyle.secondary, custom_id="partner:free:en:2h:v3", row=1)
    async def free_2h(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=2 * 60 * 60)

    @discord.ui.button(label="3 hours", style=discord.ButtonStyle.secondary, custom_id="partner:free:en:3h:v3", row=1)
    async def free_3h(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=3 * 60 * 60)


class PartnerHubViewNL(discord.ui.View):
    """Dutch persistent view in #op-zoek-naar-een-partner."""

    def __init__(self, *, finder: "PartnerFinder | None" = None) -> None:
        super().__init__(timeout=None)
        self._finder = finder

    async def _mark(self, interaction: discord.Interaction, *, duration_seconds: int) -> None:
        if self._finder is None:
            await interaction.response.send_message(
                "Nog niet klaar. Probeer het zo opnieuw.", ephemeral=True
            )
            return
        await self._finder.mark_available(
            user=interaction.user,
            guild=interaction.guild,
            interaction=interaction,
            duration_seconds=duration_seconds,
            is_nl=True,
        )

    @discord.ui.button(label="15 min", style=discord.ButtonStyle.secondary, custom_id="partner:free:nl:15m:v3", row=0)
    async def free_15_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=15 * 60)

    @discord.ui.button(label="30 min", style=discord.ButtonStyle.success, custom_id="partner:free:nl:30m:v3", row=0)
    async def free_30_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=30 * 60)

    @discord.ui.button(label="45 min", style=discord.ButtonStyle.secondary, custom_id="partner:free:nl:45m:v3", row=0)
    async def free_45_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=45 * 60)

    @discord.ui.button(label="1 uur", style=discord.ButtonStyle.secondary, custom_id="partner:free:nl:1h:v3", row=1)
    async def free_1h_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=60 * 60)

    @discord.ui.button(label="2 uur", style=discord.ButtonStyle.secondary, custom_id="partner:free:nl:2h:v3", row=1)
    async def free_2h_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=2 * 60 * 60)

    @discord.ui.button(label="3 uur", style=discord.ButtonStyle.secondary, custom_id="partner:free:nl:3h:v3", row=1)
    async def free_3h_nl(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._mark(interaction, duration_seconds=3 * 60 * 60)


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
        duration_seconds: int = DEFAULT_DURATION_SECONDS,
        is_nl: bool = False,
    ) -> None:
        pool = self._pool(is_nl)
        self._clean_expired(is_nl)
        uid = user.id
        now = time.time()
        duration_label = _duration_label(duration_seconds, is_nl=is_nl)

        already_available = uid in pool
        expires_at = now + duration_seconds
        pool[uid] = expires_at

        others = [u for u in self._available_users(is_nl) if u != uid]

        if is_nl:
            if already_available:
                msg = (
                    f"Je bent nog steeds beschikbaar. Je tijd is bijgewerkt naar **{duration_label}**.\n"
                    + ("Er is ook iemand anders vrij. Bekijk je DMs." if others else "Er is nog niemand anders vrij. Je krijgt een DM zodra iemand zich aanmeldt.")
                )
            elif others:
                count = len(others)
                msg = (
                    f"Je bent **{duration_label}** vrij om te oefenen. {count} {'persoon is' if count == 1 else 'mensen zijn'} ook vrij.\n"
                    "Bekijk je DMs."
                )
            else:
                msg = (
                    f"Je bent de komende **{duration_label}** beschikbaar.\n"
                    "Je krijgt een DM zodra iemand anders ook vrij is."
                )
        else:
            if already_available:
                msg = (
                    f"You're still marked as free. Your time is now **{duration_label}**.\n"
                    + ("Someone else is also free right now. Check your DMs." if others else "Nobody else is free yet. You will get a DM when someone joins.")
                )
            elif others:
                count = len(others)
                msg = (
                    f"You're free to practice for **{duration_label}**. {count} {'person is' if count == 1 else 'people are'} also free right now.\n"
                    "Check your DMs."
                )
            else:
                msg = (
                    f"You're marked as free for the next **{duration_label}**.\n"
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

        asyncio.create_task(self._expire_after(uid, duration_seconds, expires_at=expires_at, is_nl=is_nl))

    async def _expire_after(self, user_id: int, seconds: float, *, expires_at: float, is_nl: bool) -> None:
        await asyncio.sleep(seconds)
        pool = self._pool(is_nl)
        current_expires_at = pool.get(user_id)
        if current_expires_at is None:
            return
        if current_expires_at > expires_at + 0.5:
            return
        pool.pop(user_id, None)
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
        open_conversation = _open_conversation_link(guild.id)

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
                    f"Ga naar Open Conversation: {open_conversation}\n"
                    "Begin rustig. Je kunt gewoon hoi zeggen."
                )
            else:
                await new_user.send(
                    f"🤝 **Partner match!**\n\n"
                    f"**{names_str}** {verb} also free right now.\n\n"
                    f"Go to Open Conversation: {open_conversation}\n"
                    "Start gently. You can just say hi."
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
                        f"Ga naar Open Conversation: {open_conversation}\n"
                        "Begin rustig. Je kunt gewoon hoi zeggen."
                    )
                else:
                    await match_member.send(
                        f"🤝 **Partner match!**\n\n"
                        f"**{new_user.display_name}** is free to practice right now.\n\n"
                        f"Go to Open Conversation: {open_conversation}\n"
                        "Start gently. You can just say hi."
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