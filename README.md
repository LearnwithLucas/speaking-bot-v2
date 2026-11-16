# SpeakingBot V2

A Discord voice-first bot designed to make speaking feel normal instead of heavy.

## Operating Principles

SpeakingBot V2 exists to make **speaking feel normal**, not measured.

Every feature in this system is designed to **reduce hesitation**, **lower pressure**, and **protect user confidence**. If a feature risks doing the opposite, it does not belong here.

### 1) Speaking comes before metrics
We do not optimize for:
- rankings
- streaks
- comparisons between members

We care about one thing only:
> **More people feeling comfortable speaking at least once per week.**

Private milestones are the exception to "no time metrics": one DM at 1, 3
and 10 hours of unmuted voice time. Never public, never compared.

Human judgment matters more than numbers.

### 2) Private support over public pressure
All encouragement is:
- private
- optional
- non-judgmental

There are:
- no public call-outs
- no leaderboards
- no “you missed X” messages
- no performance framing

If someone disengages, the system should feel quiet, not watchful.

### 3) Gentle nudges, never obligations
Messages must:
- remove guilt
- remove the need to explain or “catch up”
- allow joining and leaving freely

Language that implies:
- consistency requirements
- comparison with others
…is explicitly avoided.

One exception: the welcome DM asks a new member for one concrete step,
a Table for 2 this week. Month 1 decides whether someone stays, so the
first message names one action and a time frame. It still carries no
guilt, no follow-up chasing and no "you missed it" message.

### 4) Features default to OFF
Any feature that could increase pressure:
- is behind a config flag
- defaults to disabled
- requires explicit human decision to enable

If a feature causes discomfort or negative feedback, it is turned off immediately.

The activation welcome DM is on by default. It is one message, sent once, on join.

### 5) One win-back DM, never a chase
After 14 days without voice time, a member gets one private DM with one
small step (a Table for 2). It is sent once per absence. There is no
second message, no reminder and no "you missed" wording.

Only members whose last voice time was 14 to 21 days ago are messaged,
so people who left long ago never get a sudden DM.

If it causes discomfort or negative feedback, it is turned off.

### 6) Calm systems scale better than clever ones
This project prioritizes:
- low cognitive load
- predictable behavior
- simple logic
- restart-safe design

We intentionally avoid:
- complex automation
- over-personalization
- “growth hacks”
- analytics-driven pressure loops

### 7) The goal is safety, not engagement
If a user ever thinks:
> “I’m not doing enough here”
then the system has failed.

SpeakingBot should always communicate:
> **You are welcome. You can join when you want. You don’t need to explain anything.**

---

## Features (current build)
- Welcome DM on join with one action: book a Table for 2 this week (button opens the partner planner)
- Voice time tracking (Speak Now category; excludes AFK). Counts unmuted time only, stored per server (EN and NL separately)
- Private milestone DMs at 1, 3 and 10 hours of unmuted voice time (counted from the deploy day). The 3-hour DM asks the testimonial questions
- Partner finder matches "free now" only with people at the same level (A2, B1, B2). Members pick their level once; **My level** changes it
- Win-back DM after 14 days without voice time (daily at 17:07 Amsterdam, once per absence)
- Admin stat in `/adminhealth`: share of new members in voice within 7 days of joining
- Mon/Fri announcements nudge at **15:00 Europe/Amsterdam**
- Weekly private DM (once per ISO week) on first qualifying voice join
- Private achievements (silent; max 1 per join; no public output)
- Debug commands exist but are **disabled by default** (`DEBUG_COMMANDS=0`)

---

## Local Setup

### 1) Install dependencies
```bash
pip install -r requirements.txt

## Deployment (Render)

SpeakingBot V2 runs as a single process for a single guild.

### Environment variables
See `.env.example` for the full list. Never commit `.env`.

### Start command
```bash
python app.py
