from uuid import uuid4
from dfu_state import default_patient_state

# In-memory volatile storage
GUEST_SESSIONS = {}


def create_guest_session():
    session_id = str(uuid4())
    GUEST_SESSIONS[session_id] = {
        "state": default_patient_state(),
        "messages": []
    }
    return session_id


def get_guest_session(session_id: str):
    return GUEST_SESSIONS.get(session_id)


def delete_guest_session(session_id: str):
    GUEST_SESSIONS.pop(session_id, None)