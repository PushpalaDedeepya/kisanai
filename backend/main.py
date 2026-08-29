from fastapi import FastAPI
from pydantic import BaseModel
from prompt_templates import SYSTEM_PROMPT, FARMER_QUERY_PROMPT
from knowledge_service import search_knowledge
from llm_service import get_ai_response
from weather_service import get_weather

app = FastAPI()


class FarmerRequest(BaseModel):
    question: str
    language: str = "English"
    location: str = ""


@app.get("/")
def home():
    return {"message": "Kisan AI Backend is running"}


@app.post("/ask")
def ask_farmer(request: FarmerRequest):
    context = search_knowledge(request.question)

    weather = "Not provided"

    if request.location:
        weather = get_weather(request.location)

    prompt = SYSTEM_PROMPT + "\n\n" + FARMER_QUERY_PROMPT.format(
        question=request.question,
        context=context,
        location=request.location,
        weather=weather,
        language=request.language
    )

    answer = get_ai_response(prompt)

    return {
        "answer": answer,
        "language": request.language,
        "location": request.location
    }