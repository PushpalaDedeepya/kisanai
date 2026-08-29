# 🌾 Kisan AI (కిసాన్ AI / किसान AI)
### Smart Multilingual AI Agricultural Advisory Assistant for Indian Farmers
**Voice • Vision • Live Weather • Crop Pathology • Verified Govt Schemes • Emergency Helplines**

---

## 📖 Project Overview

**Kisan AI** is a comprehensive, production-ready AI advisory platform designed specifically for Indian farmers. It bridges the critical information gap in rural agriculture by providing timely, actionable, scientific, and safe farming guidance in **10 Indian regional languages** (Telugu, Hindi, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, and English).

Farmers can interact through **Text**, **Microphone Voice (Speech-to-Text)**, or by **Uploading Crop Photos (Computer Vision Disease Diagnostics)**.

### 🌟 Core Capabilities
1. **Multilingual Agricultural AI Advisory**: Fluent regional conversation supporting complex farming terminology (paddy, cotton, chilli, tomato, pests, blights, fertilizers, and IPM measures).
2. **Crop Disease & Pest Image Diagnostics**: Upload photos of affected leaves/crops to identify diseases (e.g. Early Blight, Pink Bollworm), assess confidence, and receive verified integrated pest management (IPM) actions.
3. **Live Meteorological & Weather-Smart Advisory**: Auto-detects location or accepts village/district search. Live temperature, humidity, wind, and 24h rain chance dynamically calculate spraying feasibility and irrigation guidance.
4. **Verified Government Schemes Explorer**: Searchable directory of central and state farmer schemes (PM-KISAN, PMFBY Crop Insurance, KCC, PM-KUSUM, PMKSY) with eligibility, benefits, and official .gov.in portals.
5. **Direct Emergency & Farmer Helplines**: Click-to-call directory for Kisan Call Centre (1800-180-1551) and crop insurance helpdesks.
6. **Voice Assistant (STT & TTS)**: Native browser speech recognition and neural audio playback (Listen Aloud) in regional languages.
7. **Offline-First Resilience**: Intelligent local RAG engine and fallback knowledge database that continues to function even without active cloud LLM credentials.
8. **Responsible Agricultural Safety**: Strict refusal policies for vague chemical pesticide requests to protect crops, soil, and farmer safety.

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, Modern CSS3 (Dark Agricultural Design System), Vanilla JavaScript (Zero npm build step needed).
- **Backend API**: Python 3.10+, FastAPI, Uvicorn, Pydantic, Starlette.
- **AI / LLM Layer**: Groq Cloud (LLaMA 3.3 70B Versatile & LLaMA 3.2 11B Vision) + Intelligent Offline Agricultural Fallback Engine.
- **Weather Services**: Open-Meteo Global High-Resolution Meteorological API + OpenStreetMap Geocoding (Zero API key required for weather).
- **Voice / Audio**: Web Speech API (STT/TTS) + Google Text-to-Speech (gTTS) MP3 streaming.
- **Knowledge Base**: Curated Indian agricultural extension dataset (agricultural_knowledge.json, government_schemes.json, farmer_helplines.json).

---

## 🚀 Quick Start Guide (For Judges & Developers)

Clone the repository and start the application in under 2 minutes on any computer (Windows, macOS, or Linux).

### 1. Clone the Repository
```ash
git clone https://github.com/PushpalaDedeepya/kisanai.git
cd kisanai
```

### 2. Install Dependencies
Ensure you have Python 3.10+ installed:
```ash
cd backend
pip install -r requirements.txt
```

### 3. Configure Local Environment Variables
Create your local .env file from the provided template:
```ash
# On Windows PowerShell:
Copy-Item .env.example .env

# On Linux / macOS:
cp .env.example .env
```
*(Optional)* Add your free Groq API key in backend/.env:
\```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```
> **Note**: Kisan AI works seamlessly **out-of-the-box in Offline RAG mode with live Open-Meteo weather** even without any API keys configured!

### 4. Start the FastAPI Backend
```ash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Open the Web Application
Open your web browser and navigate to:
```
http://127.0.0.1:8000/
```
The FastAPI server directly serves the interactive web interface, styling, scripts, and API endpoints.

---

## 🔐 Environment Variables

| Variable Name | Required | Default | Description |
|---|---|---|---|
| GROQ_API_KEY | Optional | "" | Groq API key for LLaMA 3.3 & Vision models. If omitted, uses Offline RAG. |
| OPENWEATHER_API_KEY | Optional | "" | OpenWeather API key. If omitted, uses free live Open-Meteo API. |
| GEMINI_API_KEY | Optional | "" | Google Gemini API key. |
| HOST | Optional | 127.0.0.1 | Host address (0.0.0.0 in production). |
| PORT | Optional | 8000 | Port number. |
| ENVIRONMENT | Optional | development | Environment mode (development or production). |

> ⚠️ **Security Notice**: Never commit .env or real API keys to GitHub. Real secrets should only be set in local .env or in your deployment platform's secret settings.

---

## 🧪 Automated Testing & Verification

Kisan AI includes a 15-point automated test suite covering all modules:

```ash
# Run service-level tests:
python backend/test_services.py

# Run comprehensive 15-point integration test suite:
python backend/test_full_suite.py
```

---

## 🌍 Cloud Deployment Guide

Kisan AI is 100% portable and deployment-ready for platforms like **Render**, **Railway**, **Fly.io**, or **Docker**.

### Deploy on Render / Railway:
1. Push this repository to GitHub.
2. Create a new **Web Service** connected to your repository.
3. Set the **Build Command**:
   ```ash
   pip install -r backend/requirements.txt
   ```
4. Set the **Start Command**:
   ```ash
   uvicorn main:app --host 0.0.0.0 --port $PORT --app-dir backend
   ```
5. Add your `GROQ_API_KEY`in the platform's **Environment Variables** dashboard.
6. Deploy! The full application (Frontend + Backend API) will be live at your public URL.

---

## 📄 License
Built for Indian Farmers • Open Source Hackathon Project • 2026