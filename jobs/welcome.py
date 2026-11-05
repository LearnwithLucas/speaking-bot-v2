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

This is a place to practise speaking English. \
You won't get tests or grades here, and nobody expects you to be perfect.

Start small. Read along in the community, answer the daily question \
or try one short voice conversation when you are ready.

If you want a guided path, use /guide or visit https://learnwithlucas.com/en/start/.

Want to say hi? Do it in <#{say_hello}>.

See you in there.\
"""

NL_WELCOME_DM = """\
Hey, welkom bij Learn with Lucas.

Dit is een plek om Nederlands te spreken. \
Je krijgt hier geen toetsen of cijfers, en niemand verwacht dat je perfect bent.

Begin klein. Lees mee in de spreekgroep, beantwoord de vraag van de dag \
of probeer één kort gesprek wanneer je er klaar voor bent.

Wil je een vaste route? Gebruik /guide of ga naar https://learnwithlucas.com/nl/begin/.

Wil je jezelf voorstellen? Dat kan in <#{zeg_hallo}>.

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
