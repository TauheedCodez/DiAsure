def merge_state(current_state: dict, updates: dict) -> dict:
    """
    Merge updates into current_state safely.
    If value is None, ignore it (prevents overwriting real data with null).
    """
    new_state = dict(current_state)

    for k, v in updates.items():
        if v is None:
            continue
        new_state[k] = v

    return new_state