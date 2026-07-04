from __future__ import annotations

import logging
from typing import Any

from commands import ask_jerry

log = logging.getLogger(__name__)


def _replace_answer(
    faq: dict[str, dict[str, Any]],
    category: str,
    question_label: str,
    answer: str,
) -> bool:
    category_data = faq.get(category)
    if not category_data:
        return False

    questions = list(category_data.get("questions", []))
    for index, (question, _old_answer) in enumerate(questions):
        if question == question_label:
            questions[index] = (question, answer)
            category_data["questions"] = questions
            return True
    return False


def apply_ask_jerry_summer_copy() -> None:
    """Keep Ask Jerry FAQ copy aligned with current summer lessons and voice behavior."""

    replacements = [
        _replace_answer(
            ask_jerry.FAQ,
            "supported_speaking",
            "How much does it cost?",
            "Supported Speaking costs **EUR 7.99 per month**, **EUR 39.95 for 6 months** "
            "(1 month free), or **EUR 79.90 per year** (2 months free).\n\n"
            "For comparison: the current summer private trial session is EUR 24 for 30 minutes. "
            "Supported Speaking is weekly practice for less than one coffee a week.\n\n"
            "100% refund within 24 hours if it is not what you expected. No questions asked.\n\n"
            f"[Start today]({ask_jerry.EN_SUPPORTED_SPEAKING_URL})",
        ),
        _replace_answer(
            ask_jerry.FAQ,
            "private_lessons",
            "How much do private lessons cost?",
            "**Summer offer - limited spots**\n\n"
            "**Trial session** - 30 minutes - **EUR 24** (one time)\n"
            "**Speaking Builder** - 4 x 60 minutes - **EUR 189** "
            "(EUR 47.25/hour, save 10%)\n"
            "Summer split: **EUR 95 now**, **EUR 94 before session 3**\n\n"
            "**Confidence Intensive** - 10 x 60 minutes - **EUR 389** "
            "(EUR 38.90/hour, save 20%)\n"
            "Summer split: **EUR 195 now**, **EUR 194 before session 6**\n\n"
            "Private tutors elsewhere often charge EUR 50-80 per hour.\n\n"
            "Not sure which fits? Start with the trial. "
            f"[View all packages]({ask_jerry.EN_PRIVATE_LESSONS_URL})",
        ),
        _replace_answer(
            ask_jerry.FAQ,
            "private_lessons",
            "Is there space right now?",
            "Private lessons are kept limited so they stay calm and focused.\n\n"
            "Current summer availability:\n"
            "- Speaking Builder: **10 spots left**\n"
            "- Confidence Intensive: **7 spots left**\n\n"
            f"Check current availability at {ask_jerry.EN_PRIVATE_LESSONS_URL}",
        ),
        _replace_answer(
            ask_jerry.FAQ,
            "bot_features",
            "Why do I get messages in the voice channel?",
            "Jerry may occasionally post a general conversation starter after people have been "
            "in a voice channel for about an hour.\n\n"
            "It is not a personal reminder, score, or public progress message. It is just a gentle "
            "prompt in case the conversation has gone quiet.\n\n"
            "If you are not sure what to talk about, use `/topics`, `/guide`, or the vocabulary channel.",
        ),
        _replace_answer(
            ask_jerry.NL_FAQ,
            "priveles",
            "Is er nu plek?",
            "Privelessen zijn beperkt zodat ze rustig en gefocust blijven.\n\n"
            "Huidige zomerbeschikbaarheid:\n"
            "- Speaking Builder: **nog 10 beschikbaar**\n"
            "- Confidence Intensive: **nog 7 beschikbaar**\n\n"
            "Bekijk huidige beschikbaarheid op https://learnwithlucas.com/priveles-nederlands/",
        ),
        _replace_answer(
            ask_jerry.NL_FAQ,
            "server_functies",
            "Waarom krijg ik berichten in het spraakkanaal?",
            "Jerry kan af en toe een algemene gespreksstarter plaatsen nadat mensen ongeveer "
            "een uur in een spraakkanaal zijn.\n\n"
            "Het is geen persoonlijke herinnering, score of openbaar voortgangsbericht. Het is alleen "
            "een rustige prompt voor als het gesprek stilvalt.\n\n"
            "Als je niet weet waarover te praten, gebruik `/onderwerpen`, `/guide` of het woordenboekkanaal.",
        ),
    ]

    missing = len([ok for ok in replacements if not ok])
    if missing:
        log.warning("Ask Jerry summer copy patch missed %s FAQ entries", missing)
