# SpeakingBot V2

A Discord voice-first bot designed to make speaking feel normal instead of heavy.

## Operating Principles

SpeakingBot V2 exists to make **speaking feel normal**, not measured.

Every feature in this system is designed to **reduce hesitation**, **lower pressure**, and **protect user confidence**. If a feature risks doing the opposite, it does not belong here.

### 1) Speaking comes before metrics
We do not optimize for:
- total speaking time
- rankings
- streaks
- comparisons between members

We care about one thing only:
> **More people feeling comfortable speaking at least once per week.**

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
- expectations
- comparison with others
…is explicitly avoided.

### 4) Features default to OFF
Any feature that could increase pressure:
- is behind a config flag
- defaults to disabled
- requires explicit human decision to enable

If a feature causes discomfort or negative feedback, it is turned off immediately.

### 5) Inactivity nudges are optional, not assumed
The inactivity DM feature exists but is disabled by default.

Activation criteria are strict:
- weekly encouragement must already work
- a real re-entry problem must be observed
- no negative feedback may exist

If these conditions are not met:
> **The feature stays off forever.**

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
- Voice presence tracking (Speak Now category; excludes AFK)
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
