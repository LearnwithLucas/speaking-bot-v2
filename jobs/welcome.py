from __future__ import annotations

# jobs/welcome.py
import logging

import discord

from jobs.partner_planner import EN_LOOKING_CHANNEL_ID, NL_LOOKING_CHANNEL_ID, PartnerPlanStartView

log = logging.getLogger("jobs.welcome")

# Activation: the welcome DM pushes one action, a Table for 2 this week.
# A Table for 2 is a short voice chat with one other member, booked through
# the partner planner. Month 1 decides churn, so the first DM asks for that
# one step and nothing else.

EN_WELCOME_DM = """\
Hey, welcome to the Online English Café.

Your first step: one Table for 2 this week. \
That's a short voice chat with one other member. Just you and one person, no group.

Press the button and pick a day and a time. \
I'll post it in <#{looking}>. When someone joins, you both get a DM.

Mistakes are fine. One or two sentences is enough.\
"""

NL_WELCOME_DM = """\
Hey, welkom bij Learn with Lucas.

Je eerste stap: deze week één Tafel voor 2. \
Dat is een kort gesprek in voice met één ander lid. Alleen jij en één persoon, geen groep.

Druk op de knop en kies een dag en een tijd. \
Ik zet het in <#{looking}>. Doet iemand mee? Dan krijgen jullie allebei een DM.

Fouten maken mag. Een of twee zinnen is genoeg.\
"""


class WelcomeTableView(discord.ui.View):
    """Persistent button under the welcome DM. Opens the partner planner (no 'next week')."""

    def __init__(self, *, is_nl: bool) -> None:
        super().__init__(timeout=None)
        self.is_nl = is_nl
        button = discord.ui.Button(
            label="Plan mijn Tafel voor 2" if is_nl else "Book my Table for 2",
            style=discord.ButtonStyle.success,
            custom_id=f"welcome:table2:{'nl' if is_nl else 'en'}:v1",
        )
        button.callback = self._open_planner
        self.add_item(button)

    async def _open_planner(self, interaction: discord.Interaction) -> None:
        bot = interaction.client
        guild_id = getattr(bot, "dutch_guild_id", None) if self.is_nl else getattr(bot, "guild_id", None)
        if not guild_id:
            await interaction.response.send_message(
                "Dat lukt nu even niet. Probeer het zo opnieuw." if self.is_nl
                else "That didn't work right now. Try again in a moment."
            )
            return
        await interaction.response.send_message(
            "Welke dag past jou?" if self.is_nl else "Which day works for you?",
            view=PartnerPlanStartView(bot=bot, is_nl=self.is_nl, guild_id=guild_id, include_next_week=False),
        )
        log.info("Welcome Table for 2 opened user=%s nl=%s", interaction.user.id, self.is_nl)


async def send_welcome_dm(member: discord.Member, guild_id: int, en_guild_id: int, nl_guild_id: int) -> None:
    if member.bot:
        return

    if member.guild.id == en_guild_id:
        is_nl = False
        text = EN_WELCOME_DM.format(looking=EN_LOOKING_CHANNEL_ID)
    elif member.guild.id == nl_guild_id:
        is_nl = True
        text = NL_WELCOME_DM.format(looking=NL_LOOKING_CHANNEL_ID)
    else:
        return

    try:
        await member.send(text, view=WelcomeTableView(is_nl=is_nl))
        log.info("Welcome DM sent user=%s guild=%s", member.id, member.guild.id)
    except discord.Forbidden:
        log.info("Welcome DM blocked by privacy settings user=%s", member.id)
    except discord.HTTPException:
        log.exception("Welcome DM failed (HTTPException) user=%s", member.id)
    except Exception:
        log.exception("Welcome DM failed user=%s", member.id)
