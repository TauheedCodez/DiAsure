import re

# ---------------- YES / NO PARSER ----------------

def parse_yes_no(text: str):
    t = text.lower().strip()
    if t in ["yes", "y", "yeah", "yep", "haan", "ha"]:
        return True
    if t in ["no", "n", "nah", "nope", "nahi"]:
        return False
    return None


# ---------------- MAIN VALIDATOR ----------------

def validate_answer(question_key: str, user_text: str):
    """
    Returns: (is_valid: bool, value_to_store, normalized_text)
    """

    t = user_text.lower().strip()

    # ==================================================
    # UNIVERSAL SKIP / UNKNOWN (WORKS FOR ALL QUESTIONS)
    # ==================================================
    skip_phrases = [
        "i don't know", "dont know", "don't know", "no idea",
        "not sure", "i dont know", "skip", "skip this",
        "next", "next question", "move to next question", "unknown"
    ]

    if t in skip_phrases:
        return True, "unknown", "Unknown"

    # ==================================================
    # ULCER DURATION (days / weeks / months / years)
    # ==================================================
    if question_key == "ulcer_duration_days":
        # examples: "5", "5 days", "2 weeks", "3 months", "1 year"
        m = re.search(r"(\d+)\s*(day|days|week|weeks|month|months|year|years)?", t)
        if m:
            value = int(m.group(1))
            unit = m.group(2)

            if unit in [None, "day", "days"]:
                return True, value, f"{value} days"
            if unit in ["week", "weeks"]:
                return True, value * 7, f"{value} weeks"
            if unit in ["month", "months"]:
                return True, value * 30, f"{value} months"
            if unit in ["year", "years"]:
                return True, value * 365, f"{value} years"

        return False, None, None

    # ==================================================
    # BLOOD SUGAR
    # ==================================================
    if question_key == "blood_sugar_recent":
        # accept "70", "70 mg/dl", "140"
        m = re.search(r"(\d{2,3})", t)
        if m:
            val = int(m.group(1))
            if 40 <= val <= 500:
                return True, f"{val} mg/dL", f"{val} mg/dL"
        return False, None, None

    # ==================================================
    # PAIN LEVEL (0–10)
    # ==================================================
    if question_key == "pain_level":
        # examples: "7", "7/10", "pain is 6"
        m = re.search(r"(\d{1,2})", t)
        if m:
            val = int(m.group(1))
            if 0 <= val <= 10:
                return True, val, f"{val}/10"
        return False, None, None

    # ==================================================
    # YES / NO QUESTIONS
    # ==================================================
    if question_key in [
        "discharge",
        "fever",
        "redness_swelling",
        "black_tissue"
    ]:
        yn = parse_yes_no(t)
        if yn is None:
            return False, None, None
        return True, yn, "Yes" if yn else "No"

    # ==================================================
    # FALLBACK
    # ==================================================
    return False, None, None