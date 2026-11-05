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
    """Keep Ask Jerry FAQ copy aligned with current lessons and voice behavior."""

    replacements = [
        _replace_answer(
            ask_jerry.FAQ,
            "supported_speaking",
            "How much does it cost?",
            "Supported Speaking costs **€7.99 a month**, **€39.95 for 6 months** "
            "(1 month free) or **€79.90 a year** (2 months free).\n\n"
            "A private trial session costs €24 for 30 minutes. "
            "Supported Speaking is practice every week for €7.99 a month.\n\n"
            "Not what you expected? You get your money back within 14 days. Cancel anytime.\n\n"
            f"[Start today]({ask_jerry.EN_SUPPORTED_SPEAKING_URL})",
        ),
        _replace_answer(
            ask_jerry.FAQ,
            "private_lessons",
            "How much do private lessons cost?",
            "**Trial session**, 30 minutes: **€24** (one time)\n"
            "**Speaking Builder**, 4 x 60 minutes: **€189** (€47.25/hour)\n"
            "**Confidence Intensive**, 10 x 60 minutes: **€389** (€38.90/hour)\n\n"
            "You can pay in parts. Use them for work calls, small talk, presentations "
            "or exam speaking.\n\n"
            "Not sure which fits? Start with the trial. "
            f"[View all packages]({ask_jerry.EN_PRIVATE_LESSONS_URL})",
        ),
        _replace_answer(
            ask_jerry.FAQ,
            "private_lessons",
            "Is there space right now?",
            "I keep the number of private students small.\n\n"
            f"The private lessons page shows when there is space: {ask_jerry.EN_PRIVATE_LESSONS_URL}",
        ),
        _replace_answer(
            ask_jerry.FAQ,
            "bot_features",
            "Why do I get messages in the voice channel?",
            "After people have been in a voice channel for about an hour, Jerry sometimes posts "
            "a question to talk about. It is for everyone in the channel, in case the conversation goes quiet.\n\n"
            "Not sure what to talk about? Use `/topics`, `/guide` or the vocabulary channel.",
        ),
        _replace_answer(
            ask_jerry.NL_FAQ,
            "priveles",
            "Hoeveel kosten privélessen?",
            "**Proefsessie**, 30 minuten: **€28** (eenmalig)\n"
            "**Speaking Builder**, 4 x 60 minuten: **€219** (+ 3 maanden Ondersteund Spreken)\n"
            "**Confidence Intensive**, 10 x 60 minuten: **€469** (+ 6 maanden Ondersteund Spreken)\n\n"
            "Examentraining voor Inburgering, KNM, ONA, NT2 en CNaVT zit in de gewone pakketten.\n\n"
            "Niet zeker welk pakket past? Begin met de proefsessie. "
            f"Alle info: {ask_jerry.NL_PRIVATE_LESSONS_URL}",
        ),
        _replace_answer(
            ask_jerry.NL_FAQ,
            "priveles",
            "Is er nu plek?",
            "Ik houd het aantal privéleerlingen klein.\n\n"
            f"Op de privélespagina zie je wanneer er plek is: {ask_jerry.NL_PRIVATE_LESSONS_URL}",
        ),
        _replace_answer(
            ask_jerry.NL_FAQ,
            "server_functies",
            "Waarom krijg ik berichten in het spraakkanaal?",
            "Als mensen ongeveer een uur in een spraakkanaal zitten, stelt Jerry soms een vraag "
            "om over te praten. Die is voor iedereen in het kanaal, voor als het gesprek stilvalt.\n\n"
            "Weet je niet waarover je wilt praten? Gebruik `/onderwerpen`, `/guide` of het woordenboekkanaal.",
        ),
    ]

    missing = len([ok for ok in replacements if not ok])
    if missing:
        log.warning("Ask Jerry summer copy patch missed %s FAQ entries", missing)
