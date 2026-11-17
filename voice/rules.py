from discord import VoiceState


def is_in_speak_now_category(channel, speak_now_category_id: int) -> bool:
    if channel is None:
        return False
    cat = getattr(channel, "category", None)
    return bool(cat and cat.id == speak_now_category_id)


def should_count_state(state: VoiceState) -> bool:
    # Count only unmuted time: the member's mic is on and they can hear.
    # Muted or deafened (by themselves or by a moderator) does not count.
    return not (
        bool(state.self_mute)
        or bool(state.self_deaf)
        or bool(state.mute)
        or bool(state.deaf)
    )


def qualifies_first_voice_attempt(state: VoiceState) -> bool:
    """
    Minimal safe heuristic for "first voice attempt":
    - NOT server-muted (state.mute)
    - NOT self-deafened (state.self_deaf)

    No audio detection. No self-mute requirement (people may speak later).
    """
    return (not bool(state.mute)) and (not bool(state.self_deaf))
