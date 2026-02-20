def default_patient_state():
    return {
        # --- workflow control ---
        "qa_active": False,        # starts AFTER image upload
        "qa_completed": False,
        "current_question_key": None,
        "retry_count": 0,

        # --- cnn info ---
        "severity": None,

        # --- patient info ---
        "ulcer_duration_days": None,
        "discharge": None,
        "fever": None,
        "black_tissue": None,
        "blood_sugar_recent": None,
        "redness_swelling": None,
        "pain_level": None,

        # optional
        "notes": ""
    }