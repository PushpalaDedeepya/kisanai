import re
from typing import Dict, Any

# Supported languages configuration across Indian languages
SUPPORTED_LANGUAGES = {
    "English": {
        "native_name": "English",
        "code": "en",
        "speech_code": "en-IN",
        "gtts_code": "en",
        "prompt_instruction": "Answer clearly, simply, and practically in Indian English. Keep language farmer-friendly, avoid overly complex academic jargon.",
        "script_regex": r"[a-zA-Z]"
    },
    "Telugu": {
        "native_name": "తెలుగు (Telugu)",
        "code": "te",
        "speech_code": "te-IN",
        "gtts_code": "te",
        "prompt_instruction": "Answer completely and naturally in fluent Telugu (తెలుగు). Use proper Telugu agricultural terminology (వరి, పత్తి, పురుగులు, తెగులు, ఎరువులు, నీటిపారుదల) while keeping technical chemical/fertilizer active ingredients clear.",
        "script_regex": r"[\u0C00-\u0C7F]"
    },
    "Hindi": {
        "native_name": "हिन्दी (Hindi)",
        "code": "hi",
        "speech_code": "hi-IN",
        "gtts_code": "hi",
        "prompt_instruction": "Answer completely and naturally in fluent Hindi (हिन्दी). Use simple, respectful, and standard agricultural Hindi terms (फसल, कीट, रोग, खाद, सिंचाई) that Indian farmers understand.",
        "script_regex": r"[\u0900-\u097F]"
    },
    "Tamil": {
        "native_name": "தமிழ் (Tamil)",
        "code": "ta",
        "speech_code": "ta-IN",
        "gtts_code": "ta",
        "prompt_instruction": "Answer completely and naturally in fluent Tamil (தமிழ்). Use proper Tamil farming terms (நெல், பருத்தி, பூச்சிகள், நோய், உரம், பாசனம்).",
        "script_regex": r"[\u0B80-\u0BFF]"
    },
    "Kannada": {
        "native_name": "ಕನ್ನಡ (Kannada)",
        "code": "kn",
        "speech_code": "kn-IN",
        "gtts_code": "kn",
        "prompt_instruction": "Answer completely and naturally in fluent Kannada (ಕನ್ನಡ). Use proper Kannada farming terms (ಭತ್ತ, ಹತ್ತಿ, ಕೀಟಗಳು, ರೋಗ, ಗೊಬ್ಬರ, ನೀರಾವರಿ).",
        "script_regex": r"[\u0C80-\u0CFF]"
    },
    "Malayalam": {
        "native_name": "മലയാളം (Malayalam)",
        "code": "ml",
        "speech_code": "ml-IN",
        "gtts_code": "ml",
        "prompt_instruction": "Answer completely and naturally in fluent Malayalam (മലയാളം). Use proper Malayalam farming terms (നെല്ല്, കീടങ്ങൾ, രോഗം, വളം, ജലസേചനം).",
        "script_regex": r"[\u0D00-\u0D7F]"
    },
    "Marathi": {
        "native_name": "मराठी (Marathi)",
        "code": "mr",
        "speech_code": "mr-IN",
        "gtts_code": "mr",
        "prompt_instruction": "Answer completely and naturally in fluent Marathi (मराठी). Use proper Marathi farming terms (कापूस, कीड, रोग, खते, पाणी व्यवस्थापन).",
        "script_regex": r"[\u0900-\u097F]"
    },
    "Bengali": {
        "native_name": "বাংলা (Bengali)",
        "code": "bn",
        "speech_code": "bn-IN",
        "gtts_code": "bn",
        "prompt_instruction": "Answer completely and naturally in fluent Bengali (বাংলা). Use proper Bengali farming terms (ধান, পোকা, রোগ, সার, সেচ).",
        "script_regex": r"[\u0980-\u09FF]"
    },
    "Gujarati": {
        "native_name": "ગુજરાતી (Gujarati)",
        "code": "gu",
        "speech_code": "gu-IN",
        "gtts_code": "gu",
        "prompt_instruction": "Answer completely and naturally in fluent Gujarati (ગુજરાતી). Use proper Gujarati farming terms (કપાસ, જીવાત, રોગ, ખાતર, સિંચાઈ).",
        "script_regex": r"[\u0A80-\u0AFF]"
    },
    "Punjabi": {
        "native_name": "ਪੰਜਾਬੀ (Punjabi)",
        "code": "pa",
        "speech_code": "pa-IN",
        "gtts_code": "pa",
        "prompt_instruction": "Answer completely and naturally in fluent Punjabi (ਪੰਜਾਬੀ). Use proper Punjabi farming terms (ਕਣਕ, ਝੋਨਾ, ਕੀੜੇ, ਖਾਦ, ਸਿੰਚਾਈ).",
        "script_regex": r"[\u0A00-\u0A7F]"
    }
}


def detect_language(text: str) -> str:
    """
    Detect the primary language of the input text based on script analysis and Unicode blocks.
    Returns standard language name (e.g. 'Telugu', 'Hindi', 'Tamil', 'Kannada', 'English').
    """
    if not text or not text.strip():
        return "English"

    # Count character matches for each script
    script_counts = {}
    for lang, info in SUPPORTED_LANGUAGES.items():
        if lang == "English":
            continue
        matches = re.findall(info["script_regex"], text)
        if matches:
            script_counts[lang] = len(matches)

    if script_counts:
        best_lang = max(script_counts, key=script_counts.get)
        # Check if Devanagari could be Marathi vs Hindi
        if best_lang == "Hindi":
            marathi_keywords = ["आहे", "नाही", "पिकाला", "झाले", "औषध", "फवारणी", "शेतकरी", "कपाशी", "करू"]
            if any(kw in text for kw in marathi_keywords):
                return "Marathi"
        return best_lang

    return "English"


def get_language_metadata(language_name: str) -> Dict[str, Any]:
    """Retrieve speech code, gTTS code, and prompt instruction for a language."""
    norm_lang = language_name.capitalize().strip()
    if norm_lang in SUPPORTED_LANGUAGES:
        return SUPPORTED_LANGUAGES[norm_lang]
    # Fallback search
    for name, data in SUPPORTED_LANGUAGES.items():
        if name.lower() == language_name.lower():
            return data
    return SUPPORTED_LANGUAGES["English"]
