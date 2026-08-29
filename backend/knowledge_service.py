from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def get_knowledge():
    knowledge = []

    if not KNOWLEDGE_DIR.exists():
        return ""

    for file_path in KNOWLEDGE_DIR.glob("*.txt"):
        try:
            content = file_path.read_text(encoding="utf-8")
            knowledge.append(content)
        except Exception:
            continue

    return "\n\n".join(knowledge)


def search_knowledge(query):
    knowledge = get_knowledge()

    if not knowledge:
        return "No farming knowledge is currently available."

    query_words = query.lower().split()
    lines = knowledge.splitlines()

    matching_lines = []

    for line in lines:
        line_lower = line.lower()

        if any(word in line_lower for word in query_words):
            matching_lines.append(line)

    if matching_lines:
        return "\n".join(matching_lines[:10])

    return knowledge[:5000]