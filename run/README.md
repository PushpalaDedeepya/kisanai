# 🌾 Kisan AI (కిసాన్ AI / किसान AI)
### Multilingual AI Farmer Advisory Assistant with Voice, Vision, Weather, & Government Schemes

Kisan AI is an end-to-end intelligent agricultural advisory system built for Indian farmers. It enables communication across **Text, Voice, and Crop Images** in regional languages (**Telugu, Hindi, Tamil, Kannada, Malayalam, Marathi, Bengali, English**), providing verified, weather-aware, safe, and practical farming recommendations.

---

## 🚀 Quick Start & How to Run

### 1. Install Dependencies
Ensure you have Python 3.10+ installed. From the `backend/` directory:
```bash
cd backend
pip install -r requirements.txt
```

### 2. (Optional) Configure Cloud LLM API Keys
Kisan AI runs **out-of-the-box in offline/fallback mode with live Open-Meteo weather** even without any API keys!

If you wish to use Groq LLaMA 3.3 or Vision models:
1. Copy `.env.example` to `.env` in `backend/`:
```bash
cp .env.example .env
```
2. Open `.env` and set your key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```

### 3. Start the Backend Server
Run the FastAPI application with Uvicorn:
```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Open the Web Application
Once the backend is running, open your web browser to:
```
http://127.0.0.1:8000/
```
The FastAPI backend serves the full frontend web interface directly at `http://127.0.0.1:8000/`.

---

## 🌟 Key Modules & Capabilities

1. **Multilingual AI Pipeline**:
   - Understands native queries in Telugu, Hindi, English, etc.
   - Generates complete advisory directly in the selected output language.
   - Preserves critical agricultural terms (active ingredients, dosages, units).

2. **Voice Assistant (STT & TTS)**:
   - **Voice Input (STT)**: Speaks directly to the microphone in Telugu (`te-IN`), Hindi (`hi-IN`), etc.
   - **Voice Output (TTS)**: Every response features a **🔊 Listen Aloud** button that synthesizes audio in the farmer's language.

3. **Crop Image Scanner & Pathology**:
   - Upload or snap photos of leaves, stems, or pests.
   - Analyzes symptoms and returns Detected Crop, Possible Disease/Pest, Confidence Score (e.g. 85%), Observed Symptoms, and IPM Actions.

4. **Live Weather & Agricultural Advisories**:
   - Integrates Open-Meteo live atmospheric data with GPS or town search.
   - Dynamically calculates spraying feasibility (warns if rain > 40% or wind > 15 km/h) and irrigation guidance.

5. **Verified Government Schemes**:
   - Real-time directory for PM-KISAN, PMFBY, KCC, Soil Health Card, PMKSY, PM-KUSUM, and state schemes with direct official `.gov.in` links.

6. **Official Farmer Helplines**:
   - Instant clickable `tel:` links to call Kisan Call Centre (1800-180-1551) and crop insurance support (14447).

7. **Safety & Responsible Advisory**:
   - Strict adherence to responsible pesticide guidelines (only recommends chemicals when crop + pest are confirmed, always includes mandatory PPE warnings, refuses unverified chemical queries).

8. **Multi-Turn Context Memory**:
   - Remembers the crop and location throughout the conversation.
