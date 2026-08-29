import io
from typing import Optional
from gtts import gTTS
from language_service import get_language_metadata


def generate_speech_audio_bytes(text: str, language_name: str = "English") -> bytes:
    """
    Synthesize audio speech for the given text in the appropriate regional Indian language.
    Returns MP3 audio bytes.
    """
    if not text or not text.strip():
        text = "Hello from Kisan AI"

    meta = get_language_metadata(language_name)
    gtts_lang = meta.get("gtts_code", "en")

    # Clean markdown / emojis from text for clean speech synthesis
    clean_text = text.replace("*", "").replace("#", "").replace("•", "").replace("`", "")
    # Shorten if extremely long to avoid timeout
    if len(clean_text) > 800:
        clean_text = clean_text[:800] + "..."

    try:
        tts = gTTS(text=clean_text, lang=gtts_lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        print(f"TTS synthesis error with lang '{gtts_lang}': {e}. Falling back to English TTS.")
        tts = gTTS(text=clean_text, lang="en", slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
