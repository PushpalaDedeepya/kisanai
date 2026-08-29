import json
from typing import Dict, Any, List, Optional
from config import KNOWLEDGE_DIR

SCHEMES_FILE = KNOWLEDGE_DIR / "government_schemes.json"

_cached_schemes = None


def load_schemes() -> Dict[str, Any]:
    global _cached_schemes
    if _cached_schemes is not None:
        return _cached_schemes

    if not SCHEMES_FILE.exists():
        return {"central_schemes": [], "state_schemes": []}

    try:
        with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
            _cached_schemes = json.load(f)
            return _cached_schemes
    except Exception as e:
        print(f"Error loading schemes database: {e}")
        return {"central_schemes": [], "state_schemes": []}


def get_all_schemes(state: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all available schemes, optionally filtered or sorted with state-specific ones."""
    data = load_schemes()
    central = data.get("central_schemes", [])
    state_schemes = data.get("state_schemes", [])

    results = list(central)
    if state:
        state_lower = state.lower()
        matching_state = [
            s for s in state_schemes
            if state_lower in s.get("state", "").lower() or s.get("state", "").lower() in state_lower
        ]
        results.extend(matching_state)
    else:
        results.extend(state_schemes)

    return results


def get_scheme_by_id(scheme_id: str) -> Optional[Dict[str, Any]]:
    """Lookup a single scheme by its ID."""
    data = load_schemes()
    all_schemes = data.get("central_schemes", []) + data.get("state_schemes", [])
    for scheme in all_schemes:
        if scheme.get("id", "").lower() == scheme_id.lower():
            return scheme
    return None


def search_schemes(query: str, state: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search schemes by keyword in name, description, benefits, or category."""
    schemes = get_all_schemes(state=state)
    if not query or not query.strip():
        return schemes

    q_lower = query.lower()
    matched = []
    for s in schemes:
        searchable_text = f"{s.get('scheme_name', '')} {s.get('description', '')} {s.get('benefits', '')} {s.get('category', '')} {s.get('eligibility', '')}".lower()
        if q_lower in searchable_text or any(word in searchable_text for word in q_lower.split()):
            matched.append(s)

    return matched if matched else schemes[:4]


def get_schemes_context_for_query(query: str, state: Optional[str] = None) -> str:
    """Format matching schemes into a clean context block for the AI."""
    matches = search_schemes(query, state=state)
    if not matches:
        return ""

    parts = ["=== VERIFIED GOVERNMENT SCHEMES ==="]
    for s in matches[:3]:
        doc_list = ", ".join(s.get("required_documents", []))
        parts.append(
            f"• Scheme: {s.get('scheme_name')}\n"
            f"  Category: {s.get('category')}\n"
            f"  Benefits: {s.get('benefits')}\n"
            f"  Eligibility: {s.get('eligibility')}\n"
            f"  How to Apply: {s.get('how_to_apply', 'Visit official portal')}\n"
            f"  Required Documents: {doc_list if doc_list else 'Aadhaar, Land records'}\n"
            f"  Official Portal: {s.get('official_source')} (Verified: {s.get('last_verified', '2026')})"
        )
    return "\n\n".join(parts)
