from typing import Dict, Any, Tuple

SAFETY_DISCLAIMER_EN = (
    "\n\n⚠️ Crop Treatment Safety Notice: Always verify products with your local Agricultural Extension "
    "Officer / Krishi Vigyan Kendra (KVK). Wear mandatory Personal Protective Equipment (mask, gloves, goggles), "
    "never spray in windy or rainy weather, and strictly follow the product container label instructions."
)

SAFETY_DISCLAIMER_TE = (
    "\n\n⚠️ పంట రక్షణ సూచన: మందుల పిచికారీ చేసేటప్పుడు తప్పనిసరిగా ముఖానికి మాస్క్, చేతి తొడుగులు ధరించండి. "
    "గాలి ఎక్కువగా ఉన్నప్పుడు లేదా వర్షం సూచన ఉన్నప్పుడు పిచికారీ చేయవద్దు. ఎల్లప్పుడూ మందు డబ్బాపై ఉన్న సూచనలను పాటించండి."
)

SAFETY_DISCLAIMER_HI = (
    "\n\n⚠️ फसल सुरक्षा निर्देश: कीटनाशक छिड़काव करते समय मास्क और दस्ताने अवश्य पहनें। "
    "तेज हवा या बारिश की संभावना में छिड़काव न करें। हमेशा उत्पाद लेबल पर लिखे निर्देशों का पालन करें और स्थानीय कृषि अधिकारी से परामर्श लें।"
)


def evaluate_pesticide_safety(query: str, crop_identified: bool, problem_identified: bool, confidence_score: float = 0.8) -> Tuple[bool, str]:
    """
    Evaluates whether it is safe to provide a specific chemical crop protection recommendation.
    Returns:
        (is_safe: bool, safety_message: str)
    """
    pesticide_query_words = ["pesticide", "chemical", "spray", "medicine", "మందు", "పిచికారీ", "कीटनाशक", "दवा", "छिड़काव"]
    is_asking_chemical = any(w in query.lower() for w in pesticide_query_words)

    if not is_asking_chemical:
        return True, ""

    if not crop_identified or not problem_identified or confidence_score < 0.65:
        refusal_msg = (
            "The symptoms or crop details are not specific enough to safely recommend a chemical treatment. "
            "Recommending pesticides without a confirmed diagnosis can damage your crop. "
            "Please provide clearer details, upload a photo of the affected plant/leaf, or consult your local "
            "Agricultural Extension Officer (KVK) for an in-person field inspection."
        )
        return False, refusal_msg

    return True, ""


def get_safety_disclaimer_for_language(language: str) -> str:
    lang = language.lower()
    if "telugu" in lang or "తెలుగు" in lang:
        return SAFETY_DISCLAIMER_TE
    elif "hindi" in lang or "हिन्दी" in lang:
        return SAFETY_DISCLAIMER_HI
    return SAFETY_DISCLAIMER_EN
