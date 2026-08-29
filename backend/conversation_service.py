import time
from typing import Dict, Any, Optional, List
from knowledge_service import identify_crops_in_text

# In-memory store for active conversations: session_id -> context dict
_sessions: Dict[str, Dict[str, Any]] = {}

SESSION_TIMEOUT_SECONDS = 3600  # 1 hour


def get_or_create_session(session_id: str) -> Dict[str, Any]:
    current_time = time.time()

    # Clean expired sessions
    expired_keys = [k for k, v in _sessions.items() if current_time - v.get("last_active", 0) > SESSION_TIMEOUT_SECONDS]
    for k in expired_keys:
        _sessions.pop(k, None)

    if session_id not in _sessions:
        _sessions[session_id] = {
            "session_id": session_id,
            "crop": None,
            "location": None,
            "language": "English",
            "symptoms": [],
            "history": [],
            "last_active": current_time
        }
    else:
        _sessions[session_id]["last_active"] = current_time

    return _sessions[session_id]


def update_session_context(
    session_id: str,
    user_query: str,
    ai_response: str,
    language: Optional[str] = None,
    location: Optional[str] = None,
    crop: Optional[str] = None
) -> Dict[str, Any]:
    session = get_or_create_session(session_id)

    if language:
        session["language"] = language
    if location:
        session["location"] = location

    # If crop is explicitly provided or detected in query, update memory
    if crop:
        session["crop"] = crop
    else:
        detected = identify_crops_in_text(user_query)
        if detected:
            session["crop"] = detected[0]

    # Append to message history (keep last 8 turns)
    session["history"].append({"role": "user", "content": user_query})
    session["history"].append({"role": "assistant", "content": ai_response})
    if len(session["history"]) > 16:
        session["history"] = session["history"][-16:]

    return session


def get_conversation_history_prompt(session_id: str) -> str:
    """Format recent turns for prompt injection."""
    session = get_or_create_session(session_id)
    history = session.get("history", [])
    if not history:
        return ""

    lines = ["=== RECENT CONVERSATION HISTORY ==="]
    for msg in history[-6:]:
        role = "Farmer" if msg["role"] == "user" else "Kisan AI"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)
