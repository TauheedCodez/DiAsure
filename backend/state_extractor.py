import json
from groq_service import groq_chat

STATE_KEYS = [
    "severity",
    "ulcer_duration_days",
    "pain_level",
    "discharge",
    "bad_smell",
    "fever",
    "redness_swelling",
    "black_tissue",
    "blood_sugar_recent",
    "hba1c",
    "diabetes_years",
    "medications",
    "smoking",
    "previous_ulcer",
    "numbness",
    "footwear",
    "notes",
]

def extract_patient_state_update(user_message: str, current_state: dict) -> dict:
    """
    Uses Groq to extract ONLY updates from the user's message.
    Returns a dict with only the fields that should be updated.
    """

    system_prompt = f"""
You are a strict medical information extractor for a diabetic foot ulcer assistant.
Your job is to extract structured patient information from user messages.

Return ONLY valid JSON.
Do not include any explanation or extra text.

Allowed keys (only these): {STATE_KEYS}

Rules:
- If user gives a number of days/weeks, set ulcer_duration_days (weeks -> days).
- blood_sugar_recent should be a string like "70 mg/dL" if value provided.
- fever/discharge/bad_smell/redness_swelling/black_tissue/smoking/previous_ulcer/numbness are boolean true/false when user clearly says yes/no.
- pain_level must be 0-10 integer.
- hba1c must be number (float).
- diabetes_years must be integer.
- If user corrects something (example: "10 days not 5"), update the value.
- If user message does not contain any patient info, return empty JSON: {{}}
"""

    user_prompt = f"""
Current patient_state:
{json.dumps(current_state, indent=2)}

User message:
{user_message}

Extract updates now as JSON only.
"""

    raw = groq_chat(system_prompt, user_prompt).strip()

    # Safety cleanup (sometimes models wrap JSON in ```json)
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {}
        # keep only allowed keys
        cleaned = {k: v for k, v in data.items() if k in STATE_KEYS}
        return cleaned
    except Exception:
        return {}