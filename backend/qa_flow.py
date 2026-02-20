QA_ORDER = [
    "ulcer_duration_days",
    "discharge",
    "fever",
    "black_tissue",
    "blood_sugar_recent",
    "redness_swelling",
    "pain_level"
]

QUESTION_TEXT = {
    "ulcer_duration_days": "Since when do you have this ulcer?",
    "discharge": "Is there any pus or discharge from the wound?",
    "fever": "Do you have fever or feel sick?",
    "black_tissue": "Do you see any black tissue on the wound?",
    "blood_sugar_recent": "What is your recent blood sugar level (if known)?",
    "redness_swelling": "Is there redness or swelling around the ulcer?",
    "pain_level": "How painful is the ulcer on a scale of 0–10?"
}

EXAMPLES = {
    "ulcer_duration_days": "Example: 5 days / 2 weeks",
    "discharge": "Example: Yes / No",
    "fever": "Example: Yes / No",
    "black_tissue": "Example: Yes / No",
    "blood_sugar_recent": "Example: 70 mg/dL / I don’t know",
    "redness_swelling": "Example: Yes / No",
    "pain_level": "Example: 0 / 5 / 8"
}