from __future__ import annotations

# jobs/welcome.py
import logging

import discord

log = logging.getLogger("jobs.welcome")

# ---- Channel IDs ----
EN_SAY_HELLO_CHANNEL_ID = 1483433017295896677   # 👋┃say-hello
NL_ZEG_HALLO_CHANNEL_ID = 1336419808811679757   # 👋┃zeg-hallo

EN_WELCOME_DM = """\
Hey, welcome to the Online English Café.

This is a place to practice speaking English — not study it. \
No tests, no grades, no pressure to be perfect.

The free live lessons run on Monday, Wednesday, Thursday, Friday and Saturday. \
Just show up. You can listen, say one sentence, or have a full conversation. \
Whatever feels right.

If you want to say hi, <#{say_hello}> is a good place to start.

See you in there.\
"""

NL_WELCOME_DM = """\
Hey, welkom bij Ondersteund Spreken.

Dit is een plek om Nederlands te oefenen, niet om het te bestuderen. \
Geen toetsen, geen beoordelingen, geen druk om perfect te zijn.

Elke maandag om 19:00 CET is er een live spreeksessie. \
Je kunt gewoon binnenkomen. Luisteren, één zin zeggen, of een heel gesprek voeren. \
Wat goed voelt.

Als je jezelf wilt voorstellen, kan dat in <#{zeg_hallo}>.

Tot dan.\
"""


async def send_welcome_dm(member: discord.Member, guild_id: int, en_guild_id: int, nl_guild_id: int) -> None:
    if member.bot:
        return

    if member.guild.id == en_guild_id:
        text = EN_WELCOME_DM.format(say_hello=EN_SAY_HELLO_CHANNEL_ID)
    elif member.guild.id == nl_guild_id:
        text = NL_WELCOME_DM.format(zeg_hallo=NL_ZEG_HALLO_CHANNEL_ID)
    else:
        return

    try:
        await member.send(text)
        log.info("Welcome DM sent user=%s guild=%s", member.id, member.guild.id)
    except discord.Forbidden:
        log.info("Welcome DM blocked by privacy settings user=%s", member.id)
    except discord.HTTPException:
        log.exception("Welcome DM failed (HTTPException) user=%s", member.id)
    except Exception:
        log.exception("Welcome DM failed user=%s", member.id)
