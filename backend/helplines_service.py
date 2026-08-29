import json
from typing import Dict, Any, List, Optional
from config import KNOWLEDGE_DIR

HELPLINES_FILE = KNOWLEDGE_DIR / "farmer_helplines.json"

_cached_helplines = None


def load_helplines() -> Dict[str, Any]:
    global _cached_helplines
    if _cached_helplines is not None:
        return _cached_helplines

    if not HELPLINES_FILE.exists():
        return {"national_helplines": [], "state_helplines": {}}

    try:
        with open(HELPLINES_FILE, "r", encoding="utf-8") as f:
            _cached_helplines = json.load(f)
            return _cached_helplines
    except Exception as e:
        print(f"Error loading helplines database: {e}")
        return {"national_helplines": [], "state_helplines": {}}


def get_all_helplines(state: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve national helplines and relevant state helplines."""
    data = load_helplines()
    national = data.get("national_helplines", [])
    state_map = data.get("state_helplines", {})

    state_list = []
    if state:
        state_clean = state.lower().replace(" ", "_")
        for key, val in state_map.items():
            if state_clean in key or key in state_clean or state.lower() in val.get("state", "").lower():
                state_list.append(val)
    else:
        state_list = list(state_map.values())

    return {
        "national_helplines": national,
        "state_helplines": state_list
    }


def get_helplines_context_for_query(query: str, state: Optional[str] = None) -> str:
    """Format helplines into a concise context for the AI."""
    data = get_all_helplines(state=state)
    national = data.get("national_helplines", [])
    state_items = data.get("state_helplines", [])

    parts = ["=== VERIFIED EMERGENCY & ADVISORY HELPLINES ==="]
    for h in national[:3]:
        parts.append(
            f"• {h.get('name')}: Phone {h.get('phone')} (Hours: {h.get('working_hours')})\n"
            f"  Purpose: {h.get('purpose')}\n"
            f"  Official Source: {h.get('official_source')}"
        )

    for sh in state_items[:2]:
        parts.append(
            f"• {sh.get('name')} ({sh.get('state')}): Phone {sh.get('phone')}\n"
            f"  Official Source: {sh.get('official_source')}"
        )

    return "\n\n".join(parts)
