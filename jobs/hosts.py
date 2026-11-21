from __future__ import annotations

# jobs/hosts.py
#
# Conversation Host invites (EN server only for now).
#
# At 20 hours of voice time, a member who joined the server 30+ days ago and
# was never invited gets one DM: what a host does, with "Yes, I'd like to host"
# and "Not now". A yes posts a card in #admin-suggestions for Lucas to approve
# or decline. Approve gives the Conversation Host role and sends a short guide.
# Every outcome is stored, and nobody gets a second invite.

import datetime as dt
import logging
import re
import time
from typing import Any

import discord

from config import CONVERSATION_HOST_ROLE_ID

log = logging.getLogger("jobs.hosts")

HOST_INVITE_HOURS = 20
HOST_MIN_MEMBER_DAYS = 30
ADMIN_SUGGESTIONS_CHANNEL_ID = 1530193017053642805

INVITE_DM = """\
Thank you. You've now spent 20 hours speaking in voice here, and that helps everyone around you.

Would you like to be a Conversation Host? A host:
- opens a table and waits for people to join
- welcomes newcomers and helps them say their first sentence
- keeps the table calm and friendly

It's about 1 hour a week, when it suits you. You don't need to teach anything.\
"""

HOST_GUIDE_DM = """\
You're now a Conversation Host. Thank you.

How to host:
1. Once a week, open a Table for 2 or a Table for 4 and stay for about an hour.
2. When someone new joins, say hi and ask an easy question.
3. Stuck for a topic? Type /topics and pick a card.
4. Keep it friendly. If something goes wrong, send Lucas a message.

You don't need to correct people. Your job is to help them keep talking.\
"""


def _hours(seconds: int) -> str:
    return f"{seconds / 3600:.1f}h"


class HostInviteView(discord.ui.View):
    """Persistent buttons under the invite DM. The member is interaction.user."""

    def __init__(self, hosts: "HostInvites | None" = None) -> None:
        super().__init__(timeout=None)
        self.hosts = hosts

    @discord.ui.button(label="Yes, I'd like to host", style=discord.ButtonStyle.success, custom_id="host_invite:yes:v1")
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await _hosts(interaction).answer(interaction, "yes")

    @discord.ui.button(label="Not now", style=discord.ButtonStyle.secondary, custom_id="host_invite:not_now:v1")
    async def not_now(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await _hosts(interaction).answer(interaction, "not_now")


class HostReviewButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"host_review:(?P<action>approve|decline):(?P<uid>\d+)",
):
    """Approve / Decline on the admin card. Survives restarts (user ID is in the custom_id)."""

    def __init__(self, action: str, user_id: int) -> None:
        super().__init__(
            discord.ui.Button(
                label="Approve" if action == "approve" else "Decline",
                style=discord.ButtonStyle.success if action == "approve" else discord.ButtonStyle.danger,
                custom_id=f"host_review:{action}:{user_id}",
            )
        )
        self.action = action
        self.user_id = user_id

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        return cls(match["action"], int(match["uid"]))

    async def callback(self, interaction: discord.Interaction) -> None:
        await _hosts(interaction).decide(interaction, self.action, self.user_id)


def _hosts(interaction: discord.Interaction) -> "HostInvites":
    return getattr(interaction.client, "host_invites")


class HostInvites:
    def __init__(self, *, bot: discord.Client, repo: Any, guild_id: int) -> None:
        self.bot = bot
        self.repo = repo
        self.guild_id = guild_id
        if not CONVERSATION_HOST_ROLE_ID:
            log.warning("Hosts: CONVERSATION_HOST_ROLE_ID is not set; approvals can't give the role")

    async def maybe_invite(self, member: discord.Member, seconds: int) -> None:
        if member.guild.id != self.guild_id or member.bot:
            return
        if seconds < HOST_INVITE_HOURS * 3600:
            return
        if member.joined_at is None:
            return
        joined_days = (discord.utils.utcnow() - member.joined_at).days
        if joined_days < HOST_MIN_MEMBER_DAYS:
            return
        if CONVERSATION_HOST_ROLE_ID and member.get_role(CONVERSATION_HOST_ROLE_ID):
            return  # already a host

        # Record first, so a crash can never send a second invite.
        if not await self.repo.host_invite_create(member.guild.id, member.id, int(time.time())):
            return
        try:
            await member.send(INVITE_DM, view=HostInviteView())
            log.info("Hosts: invite sent user=%s", member.id)
        except discord.Forbidden:
            log.info("Hosts: invite DM blocked user=%s", member.id)
        except Exception:
            log.exception("Hosts: invite DM failed user=%s", member.id)

    async def answer(self, interaction: discord.Interaction, answer: str) -> None:
        user = interaction.user
        stored = await self.repo.host_invite_answer(self.guild_id, user.id, answer, int(time.time()))
        if not stored:
            await interaction.response.send_message("You already answered this one. Thank you.")
            return

        if answer == "not_now":
            await interaction.response.edit_message(content=INVITE_DM + "\n\nNo problem. Thank you for practising with us.", view=None)
            log.info("Hosts: not now user=%s", user.id)
            return

        await interaction.response.edit_message(
            content=INVITE_DM + "\n\nThank you. Lucas will get back to you soon.",
            view=None,
        )
        await self._post_review_card(user.id)
        log.info("Hosts: yes user=%s", user.id)

    async def _post_review_card(self, user_id: int) -> None:
        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(user_id) if guild else None
        channel = self.bot.get_channel(ADMIN_SUGGESTIONS_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            log.warning("Hosts: admin-suggestions channel not found")
            return

        start = await self._milestone_start()
        seconds = await self.repo.user_voice_seconds_since(self.guild_id, user_id, start)
        weeks = await self.repo.user_weeks_active(self.guild_id, user_id)
        joined = member.joined_at.date().isoformat() if member and member.joined_at else "unknown"
        start_day = dt.datetime.fromtimestamp(start, tz=dt.timezone.utc).date().isoformat()

        embed = discord.Embed(title="Conversation Host: wants to host")
        embed.add_field(name="Member", value=f"{member.mention if member else user_id} ({member.display_name if member else ''})", inline=False)
        embed.add_field(name="Voice time", value=f"{_hours(seconds)} since {start_day}", inline=True)
        embed.add_field(name="Joined", value=joined, inline=True)
        embed.add_field(name="Weeks active", value=str(weeks), inline=True)

        view = discord.ui.View(timeout=None)
        view.add_item(HostReviewButton("approve", user_id))
        view.add_item(HostReviewButton("decline", user_id))
        await channel.send(embed=embed, view=view)

    async def _milestone_start(self) -> int:
        from jobs.milestones import MILESTONE_START_KV

        raw = await self.repo.kv_get(self.guild_id, MILESTONE_START_KV)
        return int(raw) if raw else 0

    async def decide(self, interaction: discord.Interaction, action: str, user_id: int) -> None:
        perms = getattr(interaction.user, "guild_permissions", None)
        if perms is None or not perms.manage_guild:
            await interaction.response.send_message("Only admins can decide this.", ephemeral=True)
            return

        decision = "approved" if action == "approve" else "declined"
        if not await self.repo.host_invite_decide(self.guild_id, user_id, decision, interaction.user.id, int(time.time())):
            await interaction.response.send_message("This one is already decided.", ephemeral=True)
            return

        note = f"{'✅ Approved' if decision == 'approved' else '❌ Declined'} by {interaction.user.display_name}"
        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(user_id) if guild else None

        if decision == "approved" and member is not None:
            role = guild.get_role(CONVERSATION_HOST_ROLE_ID) if CONVERSATION_HOST_ROLE_ID else None
            if role is None:
                note += " (role not set: give the Conversation Host role by hand)"
            else:
                try:
                    await member.add_roles(role, reason="Conversation Host approved")
                except Exception:
                    log.exception("Hosts: could not add host role user=%s", user_id)
                    note += " (couldn't add the role: check the bot's role position)"
            try:
                await member.send(HOST_GUIDE_DM)
            except Exception:
                log.info("Hosts: guide DM failed user=%s", user_id)
                note += " (guide DM blocked)"

        embed = interaction.message.embeds[0] if interaction.message and interaction.message.embeds else None
        if embed is not None:
            embed.set_footer(text=note)
        await interaction.response.edit_message(embed=embed, view=None)
        log.info("Hosts: %s user=%s by=%s", decision, user_id, interaction.user.id)
