import logging
from dataclasses import dataclass

import discord
from discord import app_commands
from discord.ext import commands

from db.repo import Repo

log = logging.getLogger("commands.debug")


STAFF_CATEGORY_ID = 1367444864345833482
ADMIN_LOGS_CHANNEL_ID = 1340397297053339719
ADMIN_TEST_CHANNEL_ID = 1205828956360548383

BACKUP_ADMIN_USER_ID = 1181651144100036718  # learnwithlucas

# Approved achievements (frozen set)
ACH_FIRST_VOICE_ATTEMPT = "first_voice_attempt"
ACH_JOINED_AGAIN = "joined_again"
ACH_CAME_BACK_AFTER_BREAK = "came_back_after_break"
ACH_SPOKE_WITH_SOMEONE_NEW = "spoke_with_someone_new"

ACHIEVEMENT_CHOICES = [
    app_commands.Choice(name="First Voice", value=ACH_FIRST_VOICE_ATTEMPT),
    app_commands.Choice(name="Joined Again", value=ACH_JOINED_AGAIN),
    app_commands.Choice(name="Came Back After Break", value=ACH_CAME_BACK_AFTER_BREAK),
    app_commands.Choice(name="Spoke With Someone New", value=ACH_SPOKE_WITH_SOMEONE_NEW),
]

INACTIVITY_MSG_A = (
    "If you ever feel like joining a table again, you don’t need to catch up or explain anything. You can just join."
)
INACTIVITY_MSG_B = (
    "No pressure to be consistent here. If you want to speak again sometime, you can just join and leave whenever."
)


@dataclass(frozen=True)
class DebugConfig:
    enabled: bool
    guild_id: int


def _in_staff_category(interaction: discord.Interaction) -> bool:
    ch = interaction.channel
    if not isinstance(ch, (discord.TextChannel, discord.Thread)):
        return False
    parent = ch.parent if isinstance(ch, discord.Thread) else ch
    cat = getattr(parent, "category", None)
    return bool(cat and cat.id == STAFF_CATEGORY_ID)


def _is_allowed_debug_channel(interaction: discord.Interaction) -> bool:
    ch = interaction.channel
    if isinstance(ch, discord.Thread):
        ch = ch.parent
    return bool(getattr(ch, "id", None) == ADMIN_TEST_CHANNEL_ID)


def _has_permission(interaction: discord.Interaction) -> bool:
    if interaction.user and interaction.user.id == BACKUP_ADMIN_USER_ID:
        return True
    perms = getattr(interaction.user, "guild_permissions", None)
    return bool(perms and perms.manage_guild)


async def _audit(bot: commands.Bot, message: str) -> None:
    try:
        ch = bot.get_channel(ADMIN_LOGS_CHANNEL_ID)
        if ch is None:
            ch = await bot.fetch_channel(ADMIN_LOGS_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            await ch.send(message)
    except Exception:
        log.exception("Failed to write audit log to admin-logs")


class DebugCog(commands.Cog):
    def __init__(self, bot: commands.Bot, repo: Repo, cfg: DebugConfig):
        self.bot = bot
        self.repo = repo
        self.cfg = cfg

    debug = app_commands.Group(name="debug", description="Developer/admin debug tools (dev-only).")
    achievement = app_commands.Group(name="achievement", parent=debug, description="Achievement debug tools.")
    inactivity = app_commands.Group(name="inactivity", parent=debug, description="Inactivity nudge debug tools.")

    async def _gate(self, interaction: discord.Interaction) -> bool:
        if not self.cfg.enabled:
            await interaction.response.send_message("Debug commands are disabled.", ephemeral=True)
            return False
        if interaction.guild is None or interaction.guild.id != self.cfg.guild_id:
            await interaction.response.send_message("Wrong guild.", ephemeral=True)
            return False
        if not _in_staff_category(interaction):
            await interaction.response.send_message("Not allowed outside STAFF category.", ephemeral=True)
            return False
        if not _is_allowed_debug_channel(interaction):
            await interaction.response.send_message("Run debug commands in #admin-test.", ephemeral=True)
            return False
        if not _has_permission(interaction):
            await interaction.response.send_message("Missing permission (Manage Guild).", ephemeral=True)
            return False
        return True

    # -------------------------
    # Achievements
    # -------------------------
    @achievement.command(name="grant", description="Grant an approved achievement to a user (debug).")
    @app_commands.describe(user="Target user", achievement="Achievement")
    @app_commands.choices(achievement=ACHIEVEMENT_CHOICES)
    async def achievement_grant(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        achievement: app_commands.Choice[str],
    ):
        if not await self._gate(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        achievement_id = achievement.value
        newly = await self.repo.achievement_award_once(
            guild_id=self.cfg.guild_id,
            user_id=user.id,
            achievement_id=achievement_id,
        )

        msg = (
            f"✅ Granted `{achievement_id}` to <@{user.id}>."
            if newly
            else f"ℹ️ <@{user.id}> already has `{achievement_id}`."
        )
        await interaction.followup.send(msg, ephemeral=True)

        await _audit(
            self.bot,
            f"🛠️ DEBUG grant: by <@{interaction.user.id}> → user=<@{user.id}> achievement=`{achievement_id}` newly={newly}",
        )

    @achievement.command(name="revoke", description="Revoke an approved achievement from a user (debug).")
    @app_commands.describe(user="Target user", achievement="Achievement")
    @app_commands.choices(achievement=ACHIEVEMENT_CHOICES)
    async def achievement_revoke(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        achievement: app_commands.Choice[str],
    ):
        if not await self._gate(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        achievement_id = achievement.value
        removed = await self.repo.achievement_revoke(
            guild_id=self.cfg.guild_id,
            user_id=user.id,
            achievement_id=achievement_id,
        )

        msg = (
            f"✅ Revoked `{achievement_id}` from <@{user.id}>."
            if removed
            else f"ℹ️ <@{user.id}> did not have `{achievement_id}`."
        )
        await interaction.followup.send(msg, ephemeral=True)

        await _audit(
            self.bot,
            f"🛠️ DEBUG revoke: by <@{interaction.user.id}> → user=<@{user.id}> achievement=`{achievement_id}` removed={removed}",
        )

    @achievement.command(name="list", description="List a user's achievements (debug).")
    @app_commands.describe(user="Target user")
    async def achievement_list(self, interaction: discord.Interaction, user: discord.User):
        if not await self._gate(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        rows = await self.repo.achievements_list(self.cfg.guild_id, user.id)
        if not rows:
            await interaction.followup.send(f"No achievements for <@{user.id}>.", ephemeral=True)
            return

        lines = [f"- `{aid}` (earned_at={ts})" for (aid, ts) in rows[:50]]
        await interaction.followup.send(
            f"Achievements for <@{user.id}>:\n" + "\n".join(lines),
            ephemeral=True,
        )

        await _audit(
            self.bot,
            f"🛠️ DEBUG list: by <@{interaction.user.id}> → user=<@{user.id}> count={len(rows)}",
        )

    # -------------------------
    # Inactivity nudge test
    # -------------------------
    @inactivity.command(name="send", description="Send the inactivity DM to a user (debug test).")
    @app_commands.describe(
        user="Target user",
        days_ago="Assumed inactivity days (for logging only). Default 15.",
        variant="Approved wording variant",
    )
    @app_commands.choices(variant=[
        app_commands.Choice(name="A", value="A"),
        app_commands.Choice(name="B", value="B"),
    ])
    async def inactivity_send(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        days_ago: int = 15,
        variant: app_commands.Choice[str] | None = None,
    ):
        if not await self._gate(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        chosen = (variant.value if variant else "A").strip().upper()
        message = INACTIVITY_MSG_B if chosen == "B" else INACTIVITY_MSG_A

        sent_ok = False
        try:
            await user.send(message)
            sent_ok = True
            await interaction.followup.send(
                f"✅ Sent inactivity DM variant {chosen} to <@{user.id}> (assumed {days_ago} days inactive).",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.followup.send(
                f"ℹ️ Could not DM <@{user.id}> (privacy settings).",
                ephemeral=True,
            )
        except Exception:
            await interaction.followup.send(
                "⚠️ Failed to send inactivity DM (unexpected error).",
                ephemeral=True,
            )
            log.exception("Debug inactivity DM failed user=%s variant=%s", user.id, chosen)

        try:
            await self.repo.user_state_mark_inactivity_nudge(
                self.cfg.guild_id,
                user.id,
                int(discord.utils.utcnow().timestamp()),
            )
        except Exception:
            log.exception("Failed to mark last_inactivity_nudge_at for user=%s", user.id)

        await _audit(
            self.bot,
            f"🛠️ DEBUG inactivity_send: by <@{interaction.user.id}> → user=<@{user.id}> variant=`{chosen}` assumed_days={days_ago} sent_ok={sent_ok}",
        )


async def setup(bot: commands.Bot, repo: Repo, *, enabled: bool, guild_id: int):
    await bot.add_cog(DebugCog(bot, repo, DebugConfig(enabled=enabled, guild_id=guild_id)))
