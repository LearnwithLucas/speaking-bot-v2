from __future__ import annotations

# jobs/partner_finder.py
import asyncio
import logging
import time
import datetime as dt
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import tasks

from db.repo import Repo

log = logging.getLogger("jobs.partner_finder")

TZ_NAME = "Europe/Amsterdam"

# ---- Channel IDs ----
LOOKING_FOR_PARTNER_CHANNEL_ID = 1435902125652578434
PRACTICE_VOICE_CHANNEL_IDS = [
    1274733631298076745,  # ☕ | Drop In and Talk
    1456551629301219420,  # 🌍 | Open Conversation
]

# KV key for persisting hub message ID
KV_PARTNER_HUB_MSG_ID = "partner_hub_message_id"

# ---- Slot definitions ----
# key -> label, days (None=every day, or set of weekday ints Mon=0), hour, minute

SLOTS: dict[str, dict] = {
    "morning": {
        "label": "🌅 Morning — 09:00 CET",
        "days": None,
        "hour": 9,
        "minute": 0,
    },
    "afternoon": {
        "label": "☕ Afternoon — 15:15 CET",
        "days": None,
        "hour": 15,
        "minute": 15,
    },
    "evening": {
        "label": "🌙 Evening — 20:00 CET",
        "days": None,
        "hour": 20,
        "minute": 0,
    },
}


def _get_tz() -> ZoneInfo | None:
    try:
        return ZoneInfo(TZ_NAME)
    except ZoneInfoNotFoundError:
        log.warning("Timezone '%s' not available. Falling back to UTC.", TZ_NAME)
        return None


def _now_cet(tz: ZoneInfo | None) -> dt.datetime:
    return dt.datetime.now(tz=tz or ZoneInfo("UTC"))


def _slot_label(slot_key: str) -> str:
    return SLOTS[slot_key]["label"]


def _slots_active_today(today_weekday: int) -> list[str]:
    result = []
    for key, info in SLOTS.items():
        days = info["days"]
        if days is None or today_weekday in days:
            result.append(key)
    return result


def _voice_links() -> str:
    return " or ".join(f"<#{vc_id}>" for vc_id in PRACTICE_VOICE_CHANNEL_IDS)


def build_hub_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🤝 Find a speaking partner",
        description=(
            "Pick the times you're usually free to practice.\n"
            "When someone else picks the same time, you both get a DM.\n"
            "You'll also get a short reminder 5 minutes before.\n\n"
            "**Three times, every day:**\n"
            "🌅 Morning — 09:00 CET\n"
            "☕ Afternoon — 15:15 CET\n"
            "🌙 Evening — 20:00 CET\n\n"
            "Press **Update availability** to choose your times.\n"
            "You can change it anytime."
        ),
    )
    embed.set_footer(text="hub:en:partner:v1")
    return embed


# =====================
# UI — Slot picker (ephemeral, shown after button click)
# =====================

class SlotSelect(discord.ui.Select):
    def __init__(self, *, current_slots: list[str]) -> None:
        options = [
            discord.SelectOption(
                label=info["label"],
                value=key,
                default=(key in current_slots),
            )
            for key, info in SLOTS.items()
        ]
        super().__init__(
            placeholder="Pick your times…",
            min_values=0,
            max_values=len(SLOTS),
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        # Selection is read on Save — just ack
        await interaction.response.defer()


class SlotPickerView(discord.ui.View):
    def __init__(self, *, finder: "PartnerFinder", current_slots: list[str]) -> None:
        super().__init__(timeout=300)
        self._finder = finder
        self._current_slots = list(current_slots)
        self._select = SlotSelect(current_slots=current_slots)
        self.add_item(self._select)

    @discord.ui.button(label="Save", style=discord.ButtonStyle.success, emoji="✅", row=1)
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        selected = list(self._select.values)
        old = set(self._current_slots)
        newly_added = set(selected) - old

        await self._finder.repo.partner_slots_set(
            self._finder.guild_id,
            interaction.user.id,
            selected,
        )

        if not selected:
            msg = "Done. Your availability has been cleared."
        else:
            labels = [_slot_label(k) for k in selected]
            msg = "Done. You're free at:\n" + "\n".join(f"• {l}" for l in labels)

        await interaction.response.edit_message(content=msg, view=None)

        # Confirmation DM
        if selected:
            labels = [_slot_label(k) for k in selected]
            slot_lines = "\n".join("\u2022 " + l for l in labels)
            dm_text = (
                "Done! You're free at:\n"
                + slot_lines
                + "\n\nIf someone picks the same time, you both get a DM. "
                "You'll also get a short reminder 5 minutes before. \u2615\n\n"
                "Want to change it? Go to <#"
                + str(LOOKING_FOR_PARTNER_CHANNEL_ID)
                + "> anytime."
            )
            try:
                await interaction.user.send(dm_text)
            except discord.Forbidden:
                pass
            except Exception:
                log.exception("PartnerFinder: confirmation DM failed user=%s", interaction.user.id)

        for slot_key in newly_added:
            await self._finder.notify_match(
                user_id=interaction.user.id,
                slot_key=slot_key,
                guild=interaction.guild,
            )

    @discord.ui.button(label="Clear all", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def clear_all(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._finder.repo.partner_slots_set(
            self._finder.guild_id, interaction.user.id, []
        )
        await interaction.response.edit_message(
            content="Done. Your availability has been cleared.", view=None
        )


# =====================
# UI — Persistent hub view
# =====================

class SlotSelectView(discord.ui.View):
    """Persistent view that lives permanently in #looking-for-a-partner."""

    def __init__(self, *, finder: "PartnerFinder | None" = None) -> None:
        super().__init__(timeout=None)
        self._finder = finder

    @discord.ui.button(
        label="Update availability",
        style=discord.ButtonStyle.primary,
        emoji="🗓️",
        custom_id="partner:open_selector:v1",
    )
    async def update_availability(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self._finder is None:
            await interaction.response.send_message(
                "Partner finder is not ready yet. Try again in a moment.", ephemeral=True
            )
            return

        current = await self._finder.repo.partner_slots_get(
            self._finder.guild_id, interaction.user.id
        )
        view = SlotPickerView(finder=self._finder, current_slots=current)
        await interaction.response.send_message(
            "Pick the times you're usually free:\n"
            "Select one or more, then press **Save**.",
            view=view,
            ephemeral=True,
        )


# =====================
# Core service
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
        self._tz = _get_tz()
        self._reminded_today: set[str] = set()  # "slot_key:YYYY-MM-DD"

    async def publish_hub(self) -> None:
        """Post or update the hub embed in #looking-for-a-partner and pin it."""
        channel = self.bot.get_channel(LOOKING_FOR_PARTNER_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(LOOKING_FOR_PARTNER_CHANNEL_ID)
            except Exception:
                log.warning("PartnerFinder: could not fetch channel %s", LOOKING_FOR_PARTNER_CHANNEL_ID)
                return

        if not isinstance(channel, discord.TextChannel):
            return

        embed = build_hub_embed()
        view = SlotSelectView(finder=self)

        # Try to edit existing
        existing_id_raw = await self.repo.kv_get(self.guild_id, KV_PARTNER_HUB_MSG_ID)
        if existing_id_raw:
            try:
                msg = await channel.fetch_message(int(existing_id_raw))
                await msg.edit(embed=embed, view=view)
                log.info("PartnerFinder: updated hub message %s", existing_id_raw)
                return
            except Exception:
                log.warning("PartnerFinder: could not edit hub message, recreating")

        # Post new
        try:
            sent = await channel.send(embed=embed, view=view)
            await self.repo.kv_set(self.guild_id, KV_PARTNER_HUB_MSG_ID, str(sent.id))
            log.info("PartnerFinder: posted hub message %s", sent.id)
            try:
                await sent.pin()
                log.info("PartnerFinder: pinned hub message")
            except discord.Forbidden:
                log.warning("PartnerFinder: missing pin permission")
            except Exception:
                log.warning("PartnerFinder: could not pin hub message")
        except Exception:
            log.exception("PartnerFinder: failed to post hub message")

    async def notify_match(
        self,
        *,
        user_id: int,
        slot_key: str,
        guild: discord.Guild | None,
    ) -> None:
        """DM the user and any existing matches when a slot is newly selected."""
        if guild is None:
            return

        matches = await self.repo.partner_slots_find_matches(
            self.guild_id, slot_key, exclude_user_id=user_id
        )
        if not matches:
            return

        slot_label = _slot_label(slot_key)
        links = _voice_links()

        # DM the person who just signed up
        try:
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            names = []
            for mid in matches[:3]:
                try:
                    m = guild.get_member(mid) or await guild.fetch_member(mid)
                    names.append(m.display_name)
                except Exception:
                    pass
            names_str = ", ".join(names) if names else "someone"
            verb = "is" if len(names) == 1 else "are"
            await member.send(
                f"🤝 **Partner match!**\n\n"
                f"**{names_str}** {verb} also free at **{slot_label}**.\n\n"
                f"You can both practice in {links}.\n"
                f"See you there! ☕"
            )
        except discord.Forbidden:
            log.info("PartnerFinder: DM blocked user=%s", user_id)
        except Exception:
            log.exception("PartnerFinder: failed to DM user=%s", user_id)

        # DM existing matches
        for match_id in matches:
            try:
                match_member = guild.get_member(match_id) or await guild.fetch_member(match_id)
                try:
                    joiner = guild.get_member(user_id) or await guild.fetch_member(user_id)
                    joiner_name = joiner.display_name
                except Exception:
                    joiner_name = "Someone"
                await match_member.send(
                    f"🤝 **Partner match!**\n\n"
                    f"**{joiner_name}** just signed up for **{slot_label}** — same as you!\n\n"
                    f"You can both practice in {links}.\n"
                    f"See you there! ☕"
                )
            except discord.Forbidden:
                log.info("PartnerFinder: DM blocked match=%s", match_id)
            except Exception:
                log.exception("PartnerFinder: failed to DM match=%s", match_id)

    def start_reminder_loop(self) -> None:
        self._reminder_tick.start()

    @tasks.loop(minutes=1)
    async def _reminder_tick(self) -> None:
        now = _now_cet(self._tz)
        today_weekday = now.weekday()
        date_str = now.date().isoformat()

        for slot_key in _slots_active_today(today_weekday):
            info = SLOTS[slot_key]
            reminder_key = f"{slot_key}:{date_str}"

            if reminder_key in self._reminded_today:
                continue

            # Calculate 5-minute-before time
            slot_dt = now.replace(
                hour=info["hour"], minute=info["minute"], second=0, microsecond=0
            )
            remind_dt = slot_dt - dt.timedelta(minutes=5)

            if now.hour == remind_dt.hour and now.minute == remind_dt.minute:
                self._reminded_today.add(reminder_key)
                await self._send_reminders(slot_key=slot_key)

        # Clean up — keep only today's keys
        self._reminded_today = {k for k in self._reminded_today if k.endswith(date_str)}

    @_reminder_tick.before_loop
    async def _before_reminder(self) -> None:
        await self.bot.wait_until_ready()

    async def _send_reminders(self, *, slot_key: str) -> None:
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            return

        user_ids = await self.repo.partner_slots_get_all_for_slot(self.guild_id, slot_key)
        if not user_ids:
            return

        slot_label = _slot_label(slot_key)
        links = _voice_links()

        log.info("PartnerFinder: sending reminders slot=%s count=%s", slot_key, len(user_ids))

        for user_id in user_ids:
            try:
                member = guild.get_member(user_id) or await guild.fetch_member(user_id)
                await member.send(
                    f"⏰ **5-minute reminder!**\n\n"
                    f"Join in {links} ☕\n"
                    f"No pressure — just drop in whenever you're ready."
                )
                log.info("PartnerFinder: reminder sent user=%s slot=%s", user_id, slot_key)
            except discord.Forbidden:
                log.info("PartnerFinder: reminder DM blocked user=%s", user_id)
            except Exception:
                log.exception("PartnerFinder: reminder failed user=%s", user_id)