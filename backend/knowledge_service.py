import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import KNOWLEDGE_DIR

KNOWLEDGE_FILE = KNOWLEDGE_DIR / "agricultural_knowledge.json"

# Multilingual crop aliases mapping to knowledge keys
CROP_ALIASES = {
    "rice": ["rice", "paddy", "వరి", "धान", "चावल", "nellu", "bhatta"],
    "cotton": ["cotton", "పత్తి", "కపాస్", "कपास", "paruthi", "hatti", "kapas"],
    "tomato": ["tomato", "టమోటా", "టమాట", "टमाटर", "thakkali", "tamatar"],
    "wheat": ["wheat", "గోధుమ", "గేహు", "गेहूं", "godhumai", "godhi", "gehun"],
    "chilli": ["chilli", "chili", "మిరప", "మిర్చి", "मिर्च", "milagai", "menasinakayi", "mirchi"],
    "groundnut": ["groundnut", "peanut", "వేరుశనగ", "వేరుశెనగ", "मूंगफली", "kadala", "kadalai", "shenga", "mungfali"],
    "maize": ["maize", "corn", "మొక్కజొన్న", "మక్క", "मक्का", "makka", "cholam", "musukina jola"],
    "potato": ["potato", "బంగాళాదుంప", "ఆలు", "आलू", "urulaikizhangu", "alugadde", "aloo"],
    "sugarcane": ["sugarcane", "చెరకు", "గన్న", "गन्ना", "karumbu", "kabbu", "ganna"],
    "pulses": ["pulse", "pulses", "chickpea", "pigeon pea", "gram", "dal", "పప్పు", "శనగ", "కంది", "మినుము", "పెసర", "दाल", "चना", "अरहर", "मूंग", "उड़द"]
}

_cached_knowledge = None


def load_knowledge() -> Dict[str, Any]:
    global _cached_knowledge
    if _cached_knowledge is not None:
        return _cached_knowledge

    if not KNOWLEDGE_FILE.exists():
        return {"crops": {}, "general_farming_principles": {}}

    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            _cached_knowledge = json.load(f)
            return _cached_knowledge
    except Exception as e:
        print(f"Error loading agricultural knowledge: {e}")
        return {"crops": {}, "general_farming_principles": {}}


def identify_crops_in_text(text: str) -> List[str]:
    """Identify which crops are mentioned in the query text."""
    lower_text = text.lower()
    found_crops = []

    for crop_key, aliases in CROP_ALIASES.items():
        for alias in aliases:
            # Check whole word / token match
            if re.search(r'\b' + re.escape(alias.lower()) + r'\b', lower_text) or alias in lower_text:
                if crop_key not in found_crops:
                    found_crops.append(crop_key)
                break
    return found_crops


def search_knowledge(query: str, crop_hint: Optional[str] = None) -> str:
    """
    RAG Search: Retrieve only relevant structured knowledge for the farmer's query.
    """
    knowledge = load_knowledge()
    crops_data = knowledge.get("crops", {})
    general_principles = knowledge.get("general_farming_principles", {})

    detected_crops = identify_crops_in_text(query)
    if crop_hint and crop_hint.lower() in crops_data and crop_hint.lower() not in detected_crops:
        detected_crops.append(crop_hint.lower())

    lower_query = query.lower()
    context_parts = []

    # If specific crops are identified, retrieve targeted sections
    if detected_crops:
        for crop_key in detected_crops:
            crop_info = crops_data.get(crop_key)
            if not crop_info:
                continue

            crop_name = crop_info.get("name", crop_key.capitalize())
            crop_text = [f"=== CROP: {crop_name} ==="]

            # Check if query asks for soil/sowing
            if any(k in lower_query for k in ["soil", "sow", "plant", "spacing", "నేల", "విత్తన", "నాట", "मिट्टी", "बुवाई", "बीज"]):
                crop_text.append(f"Suitable Soil: {crop_info.get('suitable_soil', 'N/A')}")
                crop_text.append(f"Sowing & Spacing: {crop_info.get('sowing_and_spacing', 'N/A')}")

            # Check if query asks for water/irrigation
            if any(k in lower_query for k in ["water", "irrigate", "irrigation", "నీరు", "నీటిపారుదల", "తడి", "पानी", "सिंचाई"]):
                crop_text.append(f"Water & Irrigation: {crop_info.get('water_and_irrigation', 'N/A')}")

            # Check if query asks for fertilizers/nutrients
            if any(k in lower_query for k in ["fertilizer", "nutrient", "urea", "dap", "npk", "dose", "dosage", "ఎరువు", "యూరియా", "ఖాత", "उर्वरक", "खाद", "यूरिया"]):
                crop_text.append(f"Nutrient & Fertilizer: {crop_info.get('nutrient_and_fertilizer', 'N/A')}")

            # Check for pests / insects
            pests = crop_info.get("common_pests", [])
            matched_pests = []
            for p in pests:
                # If query mentions specific pest symptom or generic pest word
                if any(w in lower_query for w in ["pest", "insect", "worm", "borer", "hopper", "caterpillar", "bug", "పురుగు", "దోమ", "కీటక", "कीट", "सुंडी", "कीड़ा"]) or \
                   any(pw in lower_query for pw in p.get("name", "").lower().split()):
                    matched_pests.append(
                        f"• Pest: {p.get('name')}\n"
                        f"  Symptoms: {p.get('symptoms')}\n"
                        f"  IPM / Biological Control: {p.get('ipm_practices')}\n"
                        f"  Safe Chemical Control: {p.get('safe_chemical_control')}\n"
                        f"  Safety Precautions: {p.get('safety_precautions')}"
                    )
            if matched_pests:
                crop_text.append("Common Pests & Safe IPM Controls:\n" + "\n".join(matched_pests))

            # Check for diseases
            diseases = crop_info.get("common_diseases", [])
            matched_diseases = []
            for d in diseases:
                if any(w in lower_query for w in ["disease", "blight", "rot", "spot", "yellow", "curl", "fungal", "virus", "తెగులు", "మచ్చ", "కుళ్ళు", "ఎండి", "रोग", "झुलसा", "सड़न", "धब्बा", "पीला"]) or \
                   any(dw in lower_query for dw in d.get("name", "").lower().split()):
                    matched_diseases.append(
                        f"• Disease: {d.get('name')}\n"
                        f"  Symptoms: {d.get('symptoms')}\n"
                        f"  Preventive Measures: {d.get('preventive_measures')}\n"
                        f"  Safe Treatment: {d.get('safe_treatment')}\n"
                        f"  Safety Precautions: {d.get('safety_precautions')}"
                    )
            if matched_diseases:
                crop_text.append("Common Diseases & Safe Treatments:\n" + "\n".join(matched_diseases))

            # Weather sensitivity
            if crop_info.get("weather_sensitivity"):
                crop_text.append(f"Weather Sensitivity: {crop_info.get('weather_sensitivity')}")

            # If no sub-field matched, provide full crop overview
            if len(crop_text) == 1:
                crop_text.append(f"Suitable Soil: {crop_info.get('suitable_soil', 'N/A')}")
                crop_text.append(f"Water Management: {crop_info.get('water_and_irrigation', 'N/A')}")
                crop_text.append(f"Fertilizers: {crop_info.get('nutrient_and_fertilizer', 'N/A')}")

            context_parts.append("\n".join(crop_text))

    # Add general principles if applicable
    if any(k in lower_query for k in ["spray", "pesticide", "safety", "ipm", "chemical", "పిచికారీ", "మందు", "జాగ్రత్త", "छिड़काव", "दवाई", "सुरक्षा"]):
        safety_rules = general_principles.get("chemical_pesticide_safety_rules", [])
        if safety_rules:
            context_parts.append("=== MANDATORY PESTICIDE SAFETY RULES ===\n" + "\n".join([f"- {r}" for r in safety_rules]))

    if any(k in lower_query for k in ["rain", "weather", "spray today", "irrigate today", "వర్షం", "వాతావరణం", "मौसम", "बारिश"]):
        weather_rules = general_principles.get("weather_smart_irrigation", [])
        if weather_rules:
            context_parts.append("=== WEATHER SMART FARMING PRINCIPLES ===\n" + "\n".join([f"- {r}" for r in weather_rules]))

    if context_parts:
        return "\n\n".join(context_parts)

    # Fallback to general principles overview if query has no specific match
    general_summary = []
    for section, tips in general_principles.items():
        general_summary.append(f"[{section.replace('_', ' ').title()}]:\n" + "\n".join([f"• {t}" for t in tips[:2]]))
    return "\n\n".join(general_summary)