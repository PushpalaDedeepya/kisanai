import sys
from pathlib import Path
import io

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure backend directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from language_service import detect_language, SUPPORTED_LANGUAGES
from knowledge_service import search_knowledge, identify_crops_in_text
from weather_service import get_weather_json, get_weather
from schemes_service import get_all_schemes, search_schemes
from helplines_service import get_all_helplines
from safety_service import evaluate_pesticide_safety
from image_service import analyze_crop_image
from voice_service import generate_speech_audio_bytes
from llm_service import llm_service
from PIL import Image

print("========================================")
print("RUNNING KISAN AI BACKEND SERVICE TESTS")
print("========================================")

# 1. Test Language Detection
print("\n[TEST 1] Language Detection:")
t1 = detect_language("నా వరి పంటకు పురుగులు వచ్చాయి")
t2 = detect_language("मेरी कपास की फसल में कीट लग गए हैं")
t3 = detect_language("What fertilizer is good for tomato?")
print(f"Telugu text -> Detected: {t1} (Expected: Telugu)")
print(f"Hindi text  -> Detected: {t2} (Expected: Hindi)")
print(f"English text-> Detected: {t3} (Expected: English)")
assert t1 == "Telugu", f"Expected Telugu, got {t1}"
assert t2 == "Hindi", f"Expected Hindi, got {t2}"
assert t3 == "English", f"Expected English, got {t3}"
print("[PASS] Language Detection passed!")

# 2. Test Knowledge Retrieval (RAG)
print("\n[TEST 2] Knowledge Retrieval (RAG):")
k_rice = search_knowledge("My rice crop has blast disease")
k_cotton = search_knowledge("పత్తి పంటలో గులాబీ రంగు పురుగు")
print("Rice knowledge preview:", k_rice[:120].replace('\n', ' '))
print("Cotton knowledge preview:", k_cotton[:120].replace('\n', ' '))
assert "Rice" in k_rice or "Blast" in k_rice
assert "Cotton" in k_cotton or "పత్తి" in k_cotton or "Bollworm" in k_cotton
print("[PASS] Knowledge Retrieval passed!")

# 3. Test Weather Service (Live Open-Meteo)
print("\n[TEST 3] Live Weather Service:")
w_data = get_weather_json("Guntur")
print(f"Weather for Guntur -> Temp: {w_data.get('temperature_c')}°C, Condition: {w_data.get('condition')}, Humidity: {w_data.get('humidity_pct')}%, Rain Chance: {w_data.get('rain_probability_pct')}%")
print(f"Spraying advice: {w_data.get('agricultural_advisory', {}).get('spraying_advice')}")
assert "temperature_c" in w_data
assert "agricultural_advisory" in w_data
print("[PASS] Weather Service passed!")

# 4. Test Schemes and Helplines
print("\n[TEST 4] Schemes & Helplines:")
schemes = get_all_schemes()
helplines = get_all_helplines()
print(f"Loaded {len(schemes)} schemes and {len(helplines.get('national_helplines', []))} national helplines.")
assert len(schemes) >= 5
assert len(helplines.get("national_helplines", [])) >= 4
print("[PASS] Schemes and Helplines passed!")

# 5. Test Safety Evaluation
print("\n[TEST 5] Safety & Refusal Logic:")
safe_1, msg_1 = evaluate_pesticide_safety("Which pesticide for rice stem borer?", crop_identified=True, problem_identified=True)
safe_2, msg_2 = evaluate_pesticide_safety("What chemical medicine to spray?", crop_identified=False, problem_identified=False)
print(f"Specific query -> Safe: {safe_1}")
print(f"Vague chemical query -> Safe: {safe_2}, Refusal message: {msg_2[:80]}...")
assert safe_1 is True
assert safe_2 is False
print("[PASS] Safety Evaluation passed!")

# 6. Test Image Analysis
print("\n[TEST 6] Image Diagnostic Engine:")
test_img = Image.new("RGB", (200, 200), color=(180, 150, 40))
buf = io.BytesIO()
test_img.save(buf, format="JPEG")
img_bytes = buf.getvalue()
img_result = analyze_crop_image(img_bytes, user_query="Yellow spots on tomato leaf")
print(f"Image Diagnosis -> Crop: {img_result.get('crop_detected')}, Issue: {img_result.get('possible_issue')}, Confidence: {img_result.get('confidence_score')}%")
assert img_result.get("success") is True
print("[PASS] Image Diagnostic passed!")

# 7. Test LLM / Offline Advisory Generation
print("\n[TEST 7] Advisory Generation (Telugu):")
adv_te = llm_service.generate_advisory(
    question="వరి పంటకు ఏ ఎరువు వేయాలి?",
    language="Telugu",
    location="Guntur",
    session_id="test-session-1"
)
print(f"Mode: {adv_te.get('mode')}")
print("Telugu Advisory snippet:\n", adv_te.get("answer")[:250])
assert len(adv_te.get("answer")) > 50
print("[PASS] Advisory Generation passed!")

# 8. Test Multi-Turn Session Memory
print("\n[TEST 8] Multi-turn Crop Memory:")
adv_te2 = llm_service.generate_advisory(
    question="ఆకులు ఎండిపోతున్నాయి, ఏమి చేయాలి?",
    language="Telugu",
    location="Guntur",
    session_id="test-session-1"
)
print(f"Session remembered crop: {adv_te2.get('crop')}")
assert adv_te2.get("crop") == "rice" or adv_te2.get("crop") is not None
print("[PASS] Multi-turn Session Memory passed!")

# 9. Test Voice Synthesis (gTTS)
print("\n[TEST 9] Speech Synthesis (TTS):")
audio_bytes = generate_speech_audio_bytes("కిసాన్ AI వ్యవసాయ సలహా", language_name="Telugu")
print(f"Generated {len(audio_bytes)} audio bytes for Telugu TTS.")
assert len(audio_bytes) > 1000
print("[PASS] Voice Synthesis passed!")

print("\n========================================")
print("ALL BACKEND TESTS PASSED SUCCESSFULLY! 100%")
print("========================================")
