import os
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import ROOT_DIR, GROQ_API_KEY, GEMINI_API_KEY, ENVIRONMENT
from language_service import detect_language, SUPPORTED_LANGUAGES, get_language_metadata
from weather_service import get_weather_json, get_weather
from schemes_service import get_all_schemes, get_scheme_by_id, search_schemes
from helplines_service import get_all_helplines
from image_service import analyze_crop_image, validate_image_bytes
from voice_service import generate_speech_audio_bytes
from llm_service import llm_service

app = FastAPI(
    title="Kisan AI API",
    description="Multilingual AI Farmer Advisory Assistant with Voice, Vision, Weather, and Government Schemes integration.",
    version="2.0.0"
)

# Enable CORS for local development and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = ROOT_DIR / "frontend"


# ------------------------------------------------------------------------------
# REQUEST MODELS
# ------------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str
    language: str = "English"
    location: str = ""
    session_id: Optional[str] = None


class LanguageDetectRequest(BaseModel):
    text: str


class SpeakRequest(BaseModel):
    text: str
    language: str = "English"


# ------------------------------------------------------------------------------
# API ENDPOINTS
# ------------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": "Kisan AI",
        "version": "2.0.0",
        "llm_provider": "Groq Cloud (LLaMA 3.3)" if GROQ_API_KEY else "Offline Agricultural RAG Engine",
        "groq_configured": bool(GROQ_API_KEY),
        "gemini_configured": bool(GEMINI_API_KEY),
        "offline_ready": True,
        "supported_languages": list(SUPPORTED_LANGUAGES.keys())
    }


@app.post("/chat")
@app.post("/ask")
def chat_advisory(request: ChatRequest):
    """
    Main Multilingual Farmer Advisory Endpoint.
    Accepts text or transcribed voice queries in any language.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    session_id = request.session_id or str(uuid.uuid4())

    result = llm_service.generate_advisory(
        question=request.question,
        language=request.language,
        location=request.location,
        session_id=session_id
    )

    return {
        "answer": result["answer"],
        "language": result["language"],
        "location": result["location"],
        "crop": result.get("crop"),
        "mode": result.get("mode"),
        "session_id": session_id,
        "weather_summary": result.get("weather_summary")
    }


@app.post("/image/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    question: str = Form(""),
    language: str = Form("English"),
    location: str = Form(""),
    session_id: Optional[str] = Form(None)
):
    """
    Multimodal crop disease image upload and diagnostic endpoint.
    Accepts an uploaded image of a plant/leaf/crop with optional farmer question.
    """
    try:
        contents = await file.read()
        sess_id = session_id or str(uuid.uuid4())

        # 1. Run image analysis
        diagnosis = analyze_crop_image(contents, user_query=question, language=language)

        # 2. Integrate with LLM advisory if farmer provided a question or wants full advisory
        query_text = question if question.strip() else f"Analyze this image showing {diagnosis.get('possible_issue', 'crop symptoms')}"
        advisory_result = llm_service.generate_advisory(
            question=query_text,
            language=language,
            location=location,
            session_id=sess_id,
            image_analysis=diagnosis
        )

        return {
            "success": True,
            "filename": file.filename,
            "diagnosis": diagnosis,
            "advisory": advisory_result["answer"],
            "language": language,
            "session_id": sess_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing error: {str(e)}")


@app.get("/weather")
def get_weather_endpoint(location: str = "Hyderabad"):
    """Fetch live weather conditions and agricultural advisories."""
    return get_weather_json(location)


@app.get("/schemes")
def list_schemes(search: Optional[str] = None, state: Optional[str] = None):
    """Search and retrieve verified central and state government schemes."""
    if search:
        return {"schemes": search_schemes(search, state=state)}
    return {"schemes": get_all_schemes(state=state)}


@app.get("/schemes/{scheme_id}")
def scheme_details(scheme_id: str):
    scheme = get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return scheme


@app.get("/helplines")
def list_helplines(state: Optional[str] = None):
    """List verified emergency and advisory farmer helplines with phone numbers."""
    return get_all_helplines(state=state)


@app.post("/voice/speak")
def voice_speak(request: SpeakRequest):
    """Generate and return MP3 audio stream for text-to-speech."""
    audio_bytes = generate_speech_audio_bytes(request.text, language_name=request.language)
    return Response(content=audio_bytes, media_type="audio/mpeg")


@app.post("/language/detect")
def detect_lang_endpoint(request: LanguageDetectRequest):
    """Detect the language of given text."""
    detected = detect_language(request.text)
    return {
        "text": request.text,
        "detected_language": detected,
        "metadata": get_language_metadata(detected)
    }


@app.get("/location/auto")
def auto_detect_location():
    """Auto-detect user's current city/region from IP address."""
    import requests

    # 1. Try ip-api.com (fast and highly reliable in India)
    try:
        res = requests.get("http://ip-api.com/json/", timeout=3)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success" and data.get("city"):
                city = data.get("city")
                region = data.get("regionName") or data.get("region")
                lat = data.get("lat")
                lon = data.get("lon")
                return {
                    "success": True,
                    "location": f"{city}, {region}",
                    "latitude": lat,
                    "longitude": lon,
                    "source": "Network IP Geolocation (ip-api)"
                }
    except Exception as e:
        print(f"ip-api error: {e}")

    # 2. Try ipapi.co with proper User-Agent
    try:
        res = requests.get("https://ipapi.co/json/", headers={"User-Agent": "KisanAI/2.0"}, timeout=3)
        if res.status_code == 200:
            data = res.json()
            city = data.get("city")
            region = data.get("region")
            lat = data.get("latitude")
            lon = data.get("longitude")
            if city:
                return {
                    "success": True,
                    "location": f"{city}, {region}",
                    "latitude": lat,
                    "longitude": lon,
                    "source": "IP Geolocation (ipapi)"
                }
    except Exception as e:
        print(f"ipapi.co error: {e}")

    return {
        "success": True,
        "location": "Guntur, Andhra Pradesh",
        "latitude": 16.3067,
        "longitude": 80.4365,
        "source": "Agricultural Hub Fallback"
    }


# ------------------------------------------------------------------------------
# SERVE FRONTEND DIRECTLY
# ------------------------------------------------------------------------------
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(FRONTEND_DIR / "index.html")