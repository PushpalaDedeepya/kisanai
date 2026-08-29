import sys
import io
from pathlib import Path
from PIL import Image

# Force UTF-8 stdout
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("=" * 60)
print("RUNNING KISAN AI 15-POINT COMPREHENSIVE TEST SUITE")
print("=" * 60)

# TEST 1: English question -> English response
print("\n[TEST 1] English Question -> English Response")
r1 = client.post("/chat", json={"question": "What fertilizer should I use for rice?", "language": "English", "location": "Guntur"})
assert r1.status_code == 200
data1 = r1.json()
print("Response snippet:", data1["answer"][:100].replace('\n', ' '))
assert data1["language"] == "English"
assert len(data1["answer"]) > 20
print("[PASS] Test 1 Passed!")

# TEST 2: English question -> Telugu response
print("\n[TEST 2] English Question -> Telugu Response")
r2 = client.post("/chat", json={"question": "What fertilizer should I use for rice?", "language": "Telugu", "location": "Guntur"})
assert r2.status_code == 200
data2 = r2.json()
print("Response snippet:", data2["answer"][:100].replace('\n', ' '))
assert data2["language"] == "Telugu"
assert any(char in data2["answer"] for char in ["వ", "ర", "ప", "ఎ", "స"])
print("[PASS] Test 2 Passed!")

# TEST 3: Telugu question -> Telugu response
print("\n[TEST 3] Telugu Question -> Telugu Response")
r3 = client.post("/chat", json={"question": "నా వరి పంటకు పురుగులు వచ్చాయి. ఏమి చేయాలి?", "language": "Telugu", "location": "Guntur"})
assert r3.status_code == 200
data3 = r3.json()
print("Response snippet:", data3["answer"][:100].replace('\n', ' '))
assert data3["language"] == "Telugu"
print("[PASS] Test 3 Passed!")

# TEST 4: Telugu question -> English response
print("\n[TEST 4] Telugu Question -> English Response")
r4 = client.post("/chat", json={"question": "నా వరి పంటకు పురుగులు వచ్చాయి. ఏమి చేయాలి?", "language": "English", "location": "Guntur"})
assert r4.status_code == 200
data4 = r4.json()
print("Response snippet:", data4["answer"][:100].replace('\n', ' '))
assert data4["language"] == "English"
print("[PASS] Test 4 Passed!")

# TEST 5: Hindi question -> Hindi response
print("\n[TEST 5] Hindi Question -> Hindi Response")
r5 = client.post("/chat", json={"question": "टमाटर के पत्तों पर पीले धब्बे दिख रहे हैं, क्या करें?", "language": "Hindi", "location": "Varanasi"})
assert r5.status_code == 200
data5 = r5.json()
print("Response snippet:", data5["answer"][:100].replace('\n', ' '))
assert data5["language"] == "Hindi"
print("[PASS] Test 5 Passed!")

# TEST 6: Voice / Speech Telugu
print("\n[TEST 6] Voice / Speech Telugu Audio Endpoint")
r6 = client.post("/voice/speak", json={"text": "వరి పంట సలహా", "language": "Telugu"})
assert r6.status_code == 200
assert r6.headers["content-type"] == "audio/mpeg"
assert len(r6.content) > 1000
print(f"Generated {len(r6.content)} audio bytes for Telugu speech.")
print("[PASS] Test 6 Passed!")

# TEST 7: Voice / Speech English
print("\n[TEST 7] Voice / Speech English Audio Endpoint")
r7 = client.post("/voice/speak", json={"text": "Rice crop fertilizer recommendation", "language": "English"})
assert r7.status_code == 200
assert r7.headers["content-type"] == "audio/mpeg"
assert len(r7.content) > 1000
print(f"Generated {len(r7.content)} audio bytes for English speech.")
print("[PASS] Test 7 Passed!")

# TEST 8: Image upload -> agricultural analysis
print("\n[TEST 8] Crop Image Upload & Diagnosis")
test_img = Image.new("RGB", (300, 300), color=(120, 80, 20))
buf = io.BytesIO()
test_img.save(buf, format="JPEG")
buf.seek(0)
r8 = client.post(
    "/image/analyze",
    files={"file": ("leaf.jpg", buf, "image/jpeg")},
    data={"question": "Identify leaf disease", "language": "English", "location": "Guntur"}
)
assert r8.status_code == 200
data8 = r8.json()
print("Image Diagnosis:", data8["diagnosis"]["possible_issue"], f"(Confidence: {data8['diagnosis']['confidence_score']}%)")
assert data8["success"] is True
print("[PASS] Test 8 Passed!")

# TEST 9: Weather location -> Live Weather
print("\n[TEST 9] Weather Location -> Live Weather")
r9 = client.get("/weather?location=Guntur")
assert r9.status_code == 200
data9 = r9.json()
print(f"Guntur Weather: {data9['temperature_c']}°C, Humidity: {data9['humidity_pct']}%, Rain: {data9['rain_probability_pct']}%")
assert "temperature_c" in data9
assert "agricultural_advisory" in data9
print("[PASS] Test 9 Passed!")

# TEST 10: Weather unavailable -> Graceful Fallback
print("\n[TEST 10] Weather Unavailable -> Graceful Fallback")
r10 = client.get("/weather?location=NonExistentPlaceXYZ999")
assert r10.status_code == 200
data10 = r10.json()
print("Fallback location:", data10["location"])
assert "temperature_c" in data10
print("[PASS] Test 10 Passed!")

# TEST 11: Government Scheme Query
print("\n[TEST 11] Government Scheme Query")
r11 = client.get("/schemes?search=PM-KISAN")
assert r11.status_code == 200
data11 = r11.json()
assert len(data11["schemes"]) > 0
print("Found scheme:", data11["schemes"][0]["scheme_name"])
print("Official link:", data11["schemes"][0]["official_source"])
print("[PASS] Test 11 Passed!")

# TEST 12: Farmer Helpline Query
print("\n[TEST 12] Farmer Helpline Query")
r12 = client.get("/helplines?state=Andhra Pradesh")
assert r12.status_code == 200
data12 = r12.json()
national_h = data12["national_helplines"]
assert len(national_h) > 0
print(f"Helpline: {national_h[0]['name']} -> Phone: {national_h[0]['phone']}")
print("[PASS] Test 12 Passed!")

# TEST 13: Offline Agricultural Question
print("\n[TEST 13] Offline Agricultural Question")
r13 = client.post("/chat", json={"question": "What is integrated pest management for groundnut?", "language": "English"})
assert r13.status_code == 200
data13 = r13.json()
assert len(data13["answer"]) > 50
print("Advisory preview:", data13["answer"][:100].replace('\n', ' '))
print("[PASS] Test 13 Passed!")

# TEST 14: Pesticide recommendation with insufficient information -> SAFE REFUSAL
print("\n[TEST 14] Pesticide query without crop/problem -> Safe Refusal")
r14 = client.post("/chat", json={"question": "What chemical pesticide should I spray on my field?", "language": "English"})
assert r14.status_code == 200
data14 = r14.json()
print("Safety Refusal Message:", data14["answer"][:120].replace('\n', ' '))
assert "not specific enough to safely recommend" in data14["answer"] or "⚠️" in data14["answer"]
print("[PASS] Test 14 Passed!")

# TEST 15: Conversation remembers crop from previous message
print("\n[TEST 15] Multi-Turn Session Crop Memory")
session_id = "mem-test-99"
# Turn 1: Farmer mentions growing cotton
r15_1 = client.post("/chat", json={"question": "I grow cotton in Guntur.", "language": "English", "session_id": session_id})
assert r15_1.status_code == 200

# Turn 2: Farmer reports symptoms without mentioning crop name
r15_2 = client.post("/chat", json={"question": "My leaves are curling with small sucking bugs. What should I do?", "language": "English", "session_id": session_id})
assert r15_2.status_code == 200
data15_2 = r15_2.json()
print("Turn 2 remembered crop:", data15_2.get("crop"))
assert data15_2.get("crop") == "cotton"
print("[PASS] Test 15 Passed!")

print("\n" + "=" * 60)
print("🎉 ALL 15 INTEGRATION TESTS COMPLETED SUCCESSFULLY! (100%)")
print("=" * 60)
