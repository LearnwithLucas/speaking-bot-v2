from __future__ import annotations

# voice/table_tools.py
#
# Two helpers for the Speak Now voice channels:
#
# 1. Level status: each voice channel shows the levels of the people in it
#    ("Level B1", "Levels A2 + B1"), so members can pick a table that fits.
#    Updated when people join or leave, cleared when the channel is empty.
#
# 2. Knock: someone who finds a table full presses "Knock on a full table"
#    in the partner hub. The bot asks the table in its voice chat. The table
#    can let them in (the limit goes up by one until the table is back to its
#    normal size) or move everyone to a bigger empty table.
#
# Needs the bot to have Manage Channels, Move Members and Set Voice Channel
# Status in the Speak Now categories.

import asyncio
import logging
from typing import Any, Callable

import discord
from discord.http import Route

log = logging.getLogger("voice.table_tools")

STATUS_DELAY_SECONDS = 2
KNOCK_TIMEOUT_SECONDS = 10 * 60
LEVEL_ORDER = ("A2", "B1", "B2")


def _level_status(levels: set[str], *, is_nl: bool) -> str:
    known = [lvl for lvl in LEVEL_ORDER if lvl in levels]
    if not known:
        return ""
    word = ("Niveau" if is_nl else "Level") if len(known) == 1 else ("Niveaus" if is_nl else "Levels")
    return f"🗣️ {word} {' + '.join(known)}"


class TableTools:
    def __init__(
        self,
        *,
        bot: discord.Client,
        repo: Any,
        is_table: Callable[[discord.Guild, Any], bool],
        dutch_guild_id: int | None,
    ) -> None:
        self.bot = bot
        self.repo = repo
        self._is_table = is_table
        self.dutch_guild_id = dutch_guild_id
        self._status_tasks: dict[int, asyncio.Task] = {}
        self._last_status: dict[int, str] = {}
        # channel_id -> the user limit before we raised it for a knock
        self._raised_limits: dict[int, int] = {}

    def _is_nl(self, guild: discord.Guild) -> bool:
        return self.dutch_guild_id is not None and guild.id == self.dutch_guild_id

    # -------------------------
    # Voice updates
    # -------------------------
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if before.channel == after.channel:
            return
        for channel in (before.channel, after.channel):
            if channel is not None and self._is_table(member.guild, channel):
                self._schedule_status(channel)
        if before.channel is not None:
            await self._maybe_restore_limit(before.channel)

    def _schedule_status(self, channel: discord.VoiceChannel) -> None:
        task = self._status_tasks.get(channel.id)
        if task is not None and not task.done():
            return

        async def _run() -> None:
            await asyncio.sleep(STATUS_DELAY_SECONDS)
            try:
                await self._update_status(channel)
            except Exception:
                log.exception("TableTools: status update failed channel=%s", channel.id)

        self._status_tasks[channel.id] = asyncio.create_task(_run())

    async def _update_status(self, channel: discord.VoiceChannel) -> None:
        people = [m for m in channel.members if not m.bot]
        levels: set[str] = set()
        for m in people:
            lvl = await self.repo.member_level_get(channel.guild.id, m.id)
            if lvl:
                levels.add(lvl)
        text = _level_status(levels, is_nl=self._is_nl(channel.guild)) if people else ""
        if self._last_status.get(channel.id) == text:
            return
        await self.bot.http.request(
            Route("PUT", "/channels/{channel_id}/voice-status", channel_id=channel.id),
            json={"status": text},
        )
        self._last_status[channel.id] = text
        log.info("TableTools: status channel=%s status=%r", channel.id, text)

    async def _maybe_restore_limit(self, channel: discord.VoiceChannel) -> None:
        original = self._raised_limits.get(channel.id)
        if original is None:
            return
        people = len([m for m in channel.members if not m.bot])
        if people > original:
            return
        try:
            await channel.edit(user_limit=original, reason="Knock: table back to normal size")
            self._raised_limits.pop(channel.id, None)
            log.info("TableTools: restored limit channel=%s limit=%s", channel.id, original)
        except Exception:
            log.exception("TableTools: could not restore limit channel=%s", channel.id)

    # -------------------------
    # Knock
    # -------------------------
    def full_tables(self, guild: discord.Guild) -> list[discord.VoiceChannel]:
        result = []
        for vc in guild.voice_channels:
            # Tables of one are for solo practice, so nobody knocks there.
            if not self._is_table(guild, vc) or vc.user_limit < 2:
                continue
            if len(vc.members) >= vc.user_limit:
                result.append(vc)
        return result

    async def start_knock(self, interaction: discord.Interaction, *, is_nl: bool) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Dit werkt alleen in de server." if is_nl else "This only works in the server.", ephemeral=True)
            return
        full = self.full_tables(guild)
        if not full:
            await interaction.response.send_message(
                "Er is nu geen volle tafel. Je kunt gewoon bij een tafel gaan zitten." if is_nl
                else "No table is full right now. You can just join one.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Bij welke tafel wil je aankloppen?" if is_nl else "Which table do you want to knock on?",
            view=KnockPickView(tools=self, tables=full, is_nl=is_nl),
            ephemeral=True,
        )

    async def knock(self, interaction: discord.Interaction, channel_id: int, *, is_nl: bool) -> None:
        guild = interaction.guild
        channel = guild.get_channel(channel_id) if guild else None
        if not isinstance(channel, discord.VoiceChannel):
            await interaction.response.send_message("Die tafel bestaat niet meer." if is_nl else "That table is gone.", ephemeral=True)
            return
        if not channel.user_limit or len(channel.members) < channel.user_limit:
            await interaction.response.send_message(
                f"Er is weer plek. Ga gewoon naar {channel.mention}." if is_nl
                else f"There's space again. Just join {channel.mention}.",
                ephemeral=True,
            )
            return

        knocker = interaction.user
        people = [m for m in channel.members if not m.bot]
        mentions = " ".join(m.mention for m in people)
        text = (
            f"{mentions}\n**{knocker.display_name}** wil graag aanschuiven. Is dat goed?"
            if is_nl
            else f"{mentions}\n**{knocker.display_name}** would like to join this table. Is that OK?"
        )
        try:
            await channel.send(
                text,
                view=KnockAnswerView(tools=self, channel_id=channel.id, knocker_id=knocker.id, is_nl=is_nl),
                allowed_mentions=discord.AllowedMentions(users=people),
            )
        except Exception:
            log.exception("TableTools: could not post knock channel=%s", channel.id)
            await interaction.response.send_message(
                "Dat lukte niet. Probeer het zo opnieuw." if is_nl else "That didn't work. Try again in a moment.",
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(
            content=(
                f"Ik heb het gevraagd aan {channel.mention}. Je krijgt een DM als ze antwoorden."
                if is_nl
                else f"I asked {channel.mention}. You'll get a DM when they answer."
            ),
            view=None,
        )
        log.info("TableTools: knock user=%s channel=%s", knocker.id, channel.id)

    async def answer_let_in(self, interaction: discord.Interaction, channel_id: int, knocker_id: int, *, is_nl: bool) -> bool:
        channel = interaction.guild.get_channel(channel_id) if interaction.guild else None
        if not isinstance(channel, discord.VoiceChannel):
            return False
        if channel.id not in self._raised_limits:
            self._raised_limits[channel.id] = channel.user_limit
        new_limit = max(channel.user_limit, len(channel.members)) + 1
        try:
            await channel.edit(user_limit=new_limit, reason="Knock: table let someone in")
        except Exception:
            log.exception("TableTools: could not raise limit channel=%s", channel.id)
            await interaction.response.send_message(
                "Ik kan de tafel niet groter maken." if is_nl else "I can't make this table bigger.", ephemeral=True
            )
            return False
        await self._dm_knocker(
            interaction.guild,
            knocker_id,
            f"Je mag aanschuiven. Ga naar {channel.mention}." if is_nl else f"You can join. Go to {channel.mention}.",
        )
        log.info("TableTools: let in channel=%s knocker=%s limit=%s", channel.id, knocker_id, new_limit)
        return True

    async def answer_bigger(self, interaction: discord.Interaction, channel_id: int, knocker_id: int, *, is_nl: bool) -> bool:
        guild = interaction.guild
        channel = guild.get_channel(channel_id) if guild else None
        if not isinstance(channel, discord.VoiceChannel):
            return False
        needed = len([m for m in channel.members if not m.bot]) + 1
        target = self._free_bigger_table(guild, channel, needed)
        if target is None:
            await interaction.response.send_message(
                "Er is geen grotere lege tafel. Kies **Laat binnen**." if is_nl
                else "No bigger table is free. Choose **Let them in** instead.",
                ephemeral=True,
            )
            return False
        for m in list(channel.members):
            try:
                await m.move_to(target, reason="Knock: moving to a bigger table")
            except Exception:
                log.exception("TableTools: could not move user=%s", m.id)
        await self._dm_knocker(
            guild,
            knocker_id,
            f"De tafel is verhuisd naar {target.mention}. Je kunt erbij." if is_nl
            else f"The table moved to {target.mention}. You can join them there.",
        )
        log.info("TableTools: moved table from=%s to=%s knocker=%s", channel.id, target.id, knocker_id)
        return True

    def _free_bigger_table(self, guild: discord.Guild, current: discord.VoiceChannel, needed: int) -> discord.VoiceChannel | None:
        candidates = []
        for vc in guild.voice_channels:
            if vc.id == current.id or vc.members or not self._is_table(guild, vc):
                continue
            if vc.category_id != current.category_id:
                continue
            if vc.user_limit and vc.user_limit < needed:
                continue
            candidates.append(vc)
        # Smallest table that fits; unlimited channels last.
        candidates.sort(key=lambda vc: vc.user_limit or 10_000)
        return candidates[0] if candidates else None

    async def _dm_knocker(self, guild: discord.Guild, user_id: int, text: str) -> None:
        member = guild.get_member(user_id)
        if member is None:
            return
        try:
            await member.send(text)
        except Exception:
            log.info("TableTools: could not DM knocker=%s", user_id)


class KnockPickView(discord.ui.View):
    def __init__(self, *, tools: TableTools, tables: list[discord.VoiceChannel], is_nl: bool) -> None:
        super().__init__(timeout=5 * 60)
        self.tools = tools
        self.is_nl = is_nl
        options = [
            discord.SelectOption(label=f"{vc.name} ({len(vc.members)}/{vc.user_limit})"[:100], value=str(vc.id))
            for vc in tables[:25]
        ]
        select = discord.ui.Select(
            placeholder="Kies een tafel" if is_nl else "Pick a table",
            options=options,
        )
        select.callback = self._picked
        self._select = select
        self.add_item(select)

    async def _picked(self, interaction: discord.Interaction) -> None:
        await self.tools.knock(interaction, int(self._select.values[0]), is_nl=self.is_nl)


class KnockAnswerView(discord.ui.View):
    def __init__(self, *, tools: TableTools, channel_id: int, knocker_id: int, is_nl: bool) -> None:
        super().__init__(timeout=KNOCK_TIMEOUT_SECONDS)
        self.tools = tools
        self.channel_id = channel_id
        self.knocker_id = knocker_id
        self.is_nl = is_nl
        self.let_in.label = "Laat binnen" if is_nl else "Let them in"
        self.bigger.label = "Naar een grotere tafel" if is_nl else "Move to a bigger table"

    async def _check(self, interaction: discord.Interaction) -> bool:
        voice = getattr(interaction.user, "voice", None)
        if voice is None or voice.channel is None or voice.channel.id != self.channel_id:
            await interaction.response.send_message(
                "Alleen mensen aan deze tafel kunnen antwoorden." if self.is_nl
                else "Only people at this table can answer.",
                ephemeral=True,
            )
            return False
        return True

    async def _done(self, interaction: discord.Interaction, text: str) -> None:
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content=text, view=self)
        self.stop()

    @discord.ui.button(label="Let them in", style=discord.ButtonStyle.success)
    async def let_in(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await self._check(interaction):
            return
        if await self.tools.answer_let_in(interaction, self.channel_id, self.knocker_id, is_nl=self.is_nl):
            await self._done(
                interaction,
                f"{interaction.user.display_name} heeft een plek vrijgemaakt." if self.is_nl
                else f"{interaction.user.display_name} made room.",
            )

    @discord.ui.button(label="Move to a bigger table", style=discord.ButtonStyle.primary)
    async def bigger(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await self._check(interaction):
            return
        if await self.tools.answer_bigger(interaction, self.channel_id, self.knocker_id, is_nl=self.is_nl):
            await self._done(
                interaction,
                "Verhuisd naar een grotere tafel." if self.is_nl else "Moved to a bigger table.",
            )
