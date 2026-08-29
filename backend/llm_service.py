import os
import json
from typing import Dict, Any, Optional
from config import GROQ_API_KEY, GROQ_TEXT_MODEL, GEMINI_API_KEY
from prompt_templates import SYSTEM_PROMPT, FARMER_QUERY_PROMPT_TEMPLATE
from language_service import get_language_metadata, detect_language, SUPPORTED_LANGUAGES
from knowledge_service import search_knowledge, identify_crops_in_text
from weather_service import get_weather
from schemes_service import get_schemes_context_for_query
from helplines_service import get_helplines_context_for_query
from conversation_service import get_conversation_history_prompt, update_session_context, get_or_create_session
from safety_service import evaluate_pesticide_safety, get_safety_disclaimer_for_language


class LLMService:
    """
    Abstracted AI LLM Service supporting Groq, Gemini, and an intelligent Offline RAG Fallback Engine
    across 10 Indian regional languages.
    """

    def __init__(self):
        self.groq_client = None
        if GROQ_API_KEY:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=GROQ_API_KEY)
            except Exception as e:
                print(f"Error initializing Groq client: {e}")

    def generate_response(self, prompt: str, system_prompt: str = SYSTEM_PROMPT, temperature: float = 0.3, max_tokens: int = 1000) -> str:
        """Call external LLM if available, else raise exception to trigger offline engine."""
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model=GROQ_TEXT_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Groq API call error: {e}")
                raise e

        raise Exception("No active cloud LLM configured or reachable")

    def generate_advisory(
        self,
        question: str,
        language: str = "English",
        location: str = "",
        session_id: str = "default",
        image_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrates full advisory pipeline:
        1. Context extraction & Language instruction
        2. RAG Knowledge retrieval
        3. Weather context retrieval & agricultural interpretation
        4. Safety verification
        5. LLM prompt synthesis / Offline fallback engine
        6. Session memory update
        """
        session = get_or_create_session(session_id)

        # Retain previous crop/location if not provided
        current_crop = session.get("crop")
        crops_in_q = identify_crops_in_text(question)
        if crops_in_q:
            current_crop = crops_in_q[0]
            session["crop"] = current_crop

        effective_location = location if location else session.get("location", "")
        if effective_location:
            session["location"] = effective_location

        lang_meta = get_language_metadata(language)
        lang_instruction = lang_meta.get("prompt_instruction", "Answer in English")

        # 1. RAG Knowledge Retrieval
        knowledge_context = search_knowledge(question, crop_hint=current_crop)

        # 2. Weather Context
        weather_context = get_weather(effective_location) if effective_location else "Location not provided. Weather context unavailable."

        # 3. Schemes & Helplines Context
        schemes_context = get_schemes_context_for_query(question)
        helplines_context = get_helplines_context_for_query(question)
        schemes_and_helplines = f"{schemes_context}\n\n{helplines_context}".strip()

        # 4. Image Analysis Context
        image_context = "No image attached."
        if image_analysis and image_analysis.get("success"):
            image_context = (
                f"Image Crop Detected: {image_analysis.get('crop_detected')}\n"
                f"Possible Issue: {image_analysis.get('possible_issue')}\n"
                f"Confidence Score: {image_analysis.get('confidence_score')}%\n"
                f"Observed Symptoms: {image_analysis.get('observed_symptoms')}\n"
                f"Recommended Next Steps: {', '.join(image_analysis.get('recommended_actions', []))}"
            )
            if not current_crop and image_analysis.get("crop_detected") != "Unknown":
                current_crop = image_analysis.get("crop_detected")
                session["crop"] = current_crop

        # 5. History Context
        history_context = get_conversation_history_prompt(session_id)

        # 6. Safety Check
        is_safe, safety_warning = evaluate_pesticide_safety(
            query=question,
            crop_identified=bool(current_crop),
            problem_identified=bool(crops_in_q or "leaf" in question.lower() or "pest" in question.lower() or "yellow" in question.lower() or image_analysis)
        )

        if not is_safe:
            # If safe refusal required for unverified pesticide query
            refusal_response = self._get_multilingual_refusal(language)
            update_session_context(session_id, question, refusal_response, language=language, location=effective_location)
            return {
                "answer": refusal_response,
                "language": language,
                "location": effective_location,
                "crop": current_crop,
                "mode": "Safety Policy Verification",
                "weather_summary": weather_context
            }

        # Format Full Prompt
        full_prompt = FARMER_QUERY_PROMPT_TEMPLATE.format(
            history_context=history_context,
            question=question,
            language=language,
            language_instruction=lang_instruction,
            crop=current_crop if current_crop else "Not specified yet",
            location=effective_location if effective_location else "Not provided",
            weather_context=weather_context,
            knowledge_context=knowledge_context,
            schemes_and_helplines_context=schemes_and_helplines,
            image_analysis_context=image_context
        )

        # 7. Generate Advisory (Cloud LLM with Fallback to Offline Engine)
        mode = "Cloud LLM (Groq LLaMA 3.3)"
        try:
            answer = self.generate_response(full_prompt)
        except Exception as e:
            print(f"Cloud LLM unavailable ({e}). Running Offline Agricultural Reasoning Engine for {language}.")
            mode = "Offline Agricultural Advisory Engine"
            answer = self.offline_advisory_engine(
                question=question,
                language=language,
                crop=current_crop,
                location=effective_location,
                knowledge_context=knowledge_context,
                weather_context=weather_context,
                schemes_context=schemes_context,
                helplines_context=helplines_context,
                image_analysis=image_analysis
            )

        # Update Session History
        update_session_context(session_id, question, answer, language=language, location=effective_location, crop=current_crop)

        return {
            "answer": answer,
            "language": language,
            "location": effective_location,
            "crop": current_crop,
            "mode": mode,
            "weather_summary": weather_context
        }

    def _get_multilingual_refusal(self, language: str) -> str:
        lang = language.lower()
        if "telugu" in lang or "తెలుగు" in lang:
            return (
                "⚠️ పంట మరియు తెగులు యొక్క పూర్తి వివరాలు లేకుండా రసాయనిక పురుగుమందులను సిఫార్సు చేయడం సురక్షితం కాదు. "
                "తప్పుడు మందు వాడకం వల్ల పంటకు నష్టం జరగవచ్చు.\n\n"
                "దయచేసి మీ పంట పేరు, లక్షణాలు లేదా ఆకుల ఫోటోను పంపండి, లేదా సరైన సలహా కోసం స్థానిక వ్యవసాయ అధికారిని (KVK) లేదా "
                "కిసాన్ కాల్ సెంటర్ (1800-180-1551) ను సంప్రదించండి."
            )
        elif "hindi" in lang or "हिन्दी" in lang:
            return (
                "⚠️ फसल और कीट/रोग की स्पष्ट जानकारी के बिना कीटनाशक दवा की सिफारिश करना सुरक्षित नहीं है। "
                "गलत दवा के इस्तेमाल से फसल को नुकसान हो सकता है।\n\n"
                "कृपया अपनी फसल का नाम, लक्षण या पत्ती की फोटो भेजें, या सटीक सलाह के लिए स्थानीय कृषि विस्तार अधिकारी या "
                "किसान कॉल सेंटर (1800-180-1551) से संपर्क करें।"
            )
        elif "tamil" in lang or "தமிழ்" in lang:
            return (
                "⚠️ பயிர் மற்றும் பூச்சி/நோய் விவரங்கள் தெளிவாக இல்லாமல் பூச்சிக்கொல்லி மருந்துகளை பரிந்துரைக்க முடியாது. "
                "தயவுசெய்து உங்கள் பயிரின் பெயர் மற்றும் அறிகுறிகளை பகிருங்கள் அல்லது கிசான் கால் சென்டரை (1800-180-1551) தொடர்பு கொள்ளவும்."
            )
        elif "kannada" in lang or "ಕನ್ನಡ" in lang:
            return (
                "⚠️ ಬೆಳೆ ಮತ್ತು ಕೀಟಗಳ ಸ್ಪಷ್ಟ ಮಾಹಿತಿ ಇಲ್ಲದೆ ಕೀಟನಾಶಕಗಳನ್ನು ಶಿಫಾರಸು ಮಾಡುವುದು ಸುರಕ್ಷಿತವಲ್ಲ. "
                "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಬೆಳೆಯ ಹೆಸರು ಮತ್ತು ರೋಗದ ಲಕ್ಷಣಗಳನ್ನು ತಿಳಿಸಿ ಅಥವಾ ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ (1800-180-1551) ಅನ್ನು ಸಂಪರ್ಕಿಸಿ."
            )
        elif "marathi" in lang or "मराठी" in lang:
            return (
                "⚠️ पिकाची आणि कीड/रोगाची अचूक माहिती असल्याशिवाय रासायनिक कीटकनाशकांचा सल्ला देणे सुरक्षित नाही. "
                "कृपया पिकाचे नाव व लक्षणे सांगा किंवा किसान कॉल सेंटर (1800-180-1551) शी संपर्क साधा."
            )
        elif "bengali" in lang or "বাংলা" in lang:
            return (
                "⚠️ ফসলের নাম এবং রোগের লক্ষণ স্পষ্ট না হলে কীটনাশক ব্যবহারের পরামর্শ দেওয়া নিরাপদ নয়। "
                "দয়া করে ফসলের স্পষ্ট বিবরণ দিন অথবা কিষাণ কল সেন্টারে (1800-180-1551) যোগাযোগ করুন।"
            )
        elif "gujarati" in lang or "ગુજરાતી" in lang:
            return (
                "⚠️ પાક અને રોગ/જીવાતની યોગ્ય વિગતો વગર જંતુનાશક દવાની ભલામણ કરવી સુરક્ષિત નથી. "
                "કૃપા કરીને પાકનું નામ અને લક્ષણો જણાવો અથવા કિસાન કૉલ સેન્ટર (1800-180-1551) નો સંપર્ક કરો."
            )
        elif "punjabi" in lang or "ਪੰਜਾਬੀ" in lang:
            return (
                "⚠️ ਫ਼ਸਲ ਅਤੇ ਬਿਮਾਰੀ ਦੀ ਸਹੀ ਜਾਣਕਾਰੀ ਤੋਂ ਬਿਨਾਂ ਕੀਟਨਾਸ਼ਕ ਦੀ ਸਿਫਾਰਸ਼ ਕਰਨਾ ਸੁਰੱਖਿਅਤ ਨਹੀਂ ਹੈ। "
                "ਕਿਰਪਾ ਕਰਕੇ ਫ਼ਸਲ ਦਾ ਨਾਮ ਅਤੇ ਲੱਛਣ ਦੱਸੋ ਜਾਂ ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ (1800-180-1551) ਨਾਲ ਸੰਪਰਕ ਕਰੋ।"
            )
        elif "malayalam" in lang or "മലയാളം" in lang:
            return (
                "⚠️ കൃഷിയുടെ പേരും രോഗലക്ഷണങ്ങളും വ്യക്തമാക്കാതെ കീടനാശിനി നിർദ്ദേശിക്കുന്നത് സുരക്ഷിതമല്ല. "
                "ദയവായി വിളയുടെ വിവരങ്ങൾ വ്യക്തമാക്കുക അല്ലെങ്കിൽ കിസാൻ കോൾ സെന്ററുമായി (1800-180-1551) ബന്ധപ്പെടുക."
            )
        return (
            "⚠️ Safety Notice: The symptoms or crop details are not specific enough to safely recommend a chemical treatment. "
            "Recommending pesticides without a confirmed diagnosis can damage your crop. "
            "Please provide clearer details, upload a photo of the affected plant/leaf, or consult your local "
            "Agricultural Extension Officer (KVK) or Kisan Call Centre (1800-180-1551)."
        )

    def offline_advisory_engine(
        self,
        question: str,
        language: str,
        crop: Optional[str],
        location: str,
        knowledge_context: str,
        weather_context: str,
        schemes_context: str,
        helplines_context: str,
        image_analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Intelligent offline synthesis engine providing structured, verified agricultural guidance
        across all supported Indian languages.
        """
        q_lower = question.lower()
        lang = language.lower()

        # 1. Government Schemes Query
        if any(w in q_lower for w in ["scheme", "subsidy", "pm-kisan", "pmfby", "kcc", "పథకం", "రైతు భరోసా", "యోజన", "योजना", "திட்டம்", "ಯೋಜನೆ", "योजना", "প্রকল্প", "યોજના"]):
            if "telugu" in lang or "తెలుగు" in lang:
                return (
                    "🌾 ప్రధాన ప్రభుత్వ రైతు సంక్షేమ పథకాలు:\n\n"
                    "1. PM-KISAN (పీఎం కిసాన్): రైతులకు ఏటా ₹6,000 ఆర్థిక సహాయం (3 విడతల్లో ₹2,000 చొప్పున DBT ద్వారా).\n"
                    "   • అర్హత: సాగు భూమి ఉన్న రైతులందరూ. పోర్టల్: pmkisan.gov.in\n\n"
                    "2. PMFBY (ప్రధాన మంత్రి ఫసల్ బీమా యోజన - పంటల బీమా):\n"
                    "   • ఖరీఫ్ పంటలకు కేవలం 2%, రబీ పంటలకు 1.5% ప్రీమియంతో పంట నష్ట పరిహారం. పోర్టల్: pmfby.gov.in | హెల్ప్‌లైన్: 14447\n\n"
                    "3. కిసాన్ క్రెడిట్ కార్డ్ (KCC): 4% అతి తక్కువ వడ్డీతో ₹3 లక్షల వరకు పంట రుణం.\n\n"
                    "4. PMKSY (మైక్రో ఇరిగేషన్): బిందు, తుంపర సేద్యం పరికరాలపై 45-55% వరకు సబ్సిడీ.\n\n"
                    "📞 మరిన్ని వివరాల కోసం కిసాన్ కాల్ సెంటర్ 1800-180-1551 (టోల్ ఫ్రీ) కు డయల్ చేయండి."
                )
            elif "hindi" in lang or "हिन्दी" in lang:
                return (
                    "🌾 प्रमुख सरकारी किसान योजनाएं:\n\n"
                    "1. PM-KISAN (प्रधानमंत्री किसान सम्मान निधि): प्रति वर्ष ₹6,000 की आर्थिक सहायता (₹2,000 की 3 किस्तों में DBT द्वारा).\n"
                    "   • आधिकारिक पोर्टल: pmkisan.gov.in\n\n"
                    "2. PMFBY (प्रधानमंत्री फसल बीमा योजना): प्राकृतिक आपदा या बेमौसम बारिश से नुकसान पर पूरा मुआवजा। खरीफ के लिए 2%, रबी के लिए 1.5% प्रीमियम।\n"
                    "   • हेल्पलाइन: 14447 | पोर्टल: pmfby.gov.in\n\n"
                    "3. किसान क्रेडिट कार्ड (KCC): केवल 4% ब्याज दर पर ₹3 लाख तक का आसान कृषि ऋण।\n\n"
                    "4. पीएम कुसुम (PM-KUSUM): सोलर कृषि पंप पर 60% तक की सरकारी सब्सिडी।\n\n"
                    "📞 अधिक जानकारी के लिए किसान कॉल सेंटर 1800-180-1551 (टोल फ्री) पर संपर्क करें।"
                )
            elif "tamil" in lang or "தமிழ்" in lang:
                return (
                    "🌾 முக்கிய அரசு விவசாய திட்டங்கள்:\n\n"
                    "1. PM-KISAN: விவசாயிகளுக்கு ஆண்டுக்கு ₹6,000 நேரடி நிதி உதவி (3 தவணைகளில் ₹2,000 வீதம்).\n"
                    "2. PMFBY (பயிர் காப்பீடு): இயற்கை சீற்றங்களால் பயிர் சேதம் அடைந்தால் உரிய இழப்பீடு (ஹெல்ப்லைன்: 14447).\n"
                    "3. கிசான் கிரெடிட் கார்டு (KCC): 4% வட்டி மானியத்தில் ₹3 லட்சம் வரை கடன்.\n"
                    "4. PMKSY: சொட்டு நீர் மற்றும் தெளிப்பு பாசன அமைப்புகளுக்கு 45-55% மானியம்.\n\n"
                    "📞 உதவிக்கு கிசான் கால் சென்டர் 1800-180-1551 எண்ணை அழைக்கவும்."
                )
            elif "kannada" in lang or "ಕನ್ನಡ" in lang:
                return (
                    "🌾 ಪ್ರಮುಖ ಸರ್ಕಾರಿ ರೈತ ಯೋಜನೆಗಳು:\n\n"
                    "1. PM-KISAN: ರೈತರಿಗೆ ವಾರ್ಷಿಕ ₹6,000 ಆರ್ಥಿಕ ನೆರವು (3 ಕಂತುಗಳಲ್ಲಿ ₹2,000 ರಂತೆ ಡಿಬಿಟಿ ಮೂಲಕ).\n"
                    "2. PMFBY (ಬೆಳೆ ವಿಮೆ): ಬೆಳೆ ಹಾನಿಗೆ ಕನಿಷ್ಠ ಪ್ರೀಮಿಯಂನಲ್ಲಿ ವಿಮಾ ಪರಿಹಾರ (ಸಹಾಯವಾಣಿ: 14447).\n"
                    "3. ಕಿಸಾನ್ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ (KCC): ಶೇ. 4 ರ ಕಡಿಮೆ ಬಡ್ಡಿದರದಲ್ಲಿ ₹3 ಲಕ್ಷದವರೆಗೆ ಕೃಷಿ ಸಾಲ.\n"
                    "4. PMKSY: ಹನಿ ಮತ್ತು ತುಂತುರು ನೀರಾವರಿ ಘಟಕಗಳಿಗೆ ಶೇ. 45-55 ರವರೆಗೆ ಸಬ್ಸಿಡಿ.\n\n"
                    "📞 ಹೆಚ್ಚಿನ ಮಾಹಿತಿಗಾಗಿ ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ 1800-180-1551 ಗೆ ಕರೆ ಮಾಡಿ."
                )
            elif "marathi" in lang or "मराठी" in lang:
                return (
                    "🌾 प्रमुख शासकीय शेतकरी योजना:\n\n"
                    "1. PM-KISAN (पीएम किसान): शेतकऱ्यांना दरवर्षी ₹6,000 ची थेट आर्थिक मदत (3 हप्त्यांमध्ये ₹2,000).\n"
                    "2. PMFBY (पंतप्रधान पीक विमा योजना): नैसर्गिक आपत्तीत पिकांच्या नुकसानीवर भरपाई (हेल्पलाइन: 14447).\n"
                    "3. किसान क्रेडिट कार्ड (KCC): केवळ 4% व्याजदराने ₹3 लाखांपर्यंत सुलभ कृषी कर्ज.\n"
                    "4. पीएम कुसुम योजना: सौर कृषी पंपांवर 60% पर्यंत अनुदान.\n\n"
                    "📞 अधिक माहितीसाठी किसान कॉल सेंटर 1800-180-1551 (टोल फ्री) वर संपर्क करा."
                )
            elif "bengali" in lang or "বাংলা" in lang:
                return (
                    "🌾 প্রধান সরকারি কৃষক কল্যাণ প্রকল্প:\n\n"
                    "1. PM-KISAN: কৃষকদের জন্য বছরে ₹6,000 প্রত্যক্ষ আর্থিক সহায়তা (3 কিস্তিতে ₹2,000 করে)।\n"
                    "2. PMFBY (ফসল বীমা যোজনা): প্রাকৃতিক দুর্যোগে ফসল ক্ষতির সম্পূর্ণ ক্ষতিপূরণ (হেল্পলাইন: 14447)।\n"
                    "3. কিষাণ ক্রেডিট কার্ড (KCC): মাত্র 4% সুদের হারে ₹3 লক্ষ পর্যন্ত স্বল্পমেয়াদী কৃষি ঋণ।\n\n"
                    "📞 সহায়তার জন্য কিষাণ কল সেন্টার 1800-180-1551 নম্বরে কল করুন।"
                )
            elif "gujarati" in lang or "ગુજરાતી" in lang:
                return (
                    "🌾 મુખ્ય સરકારી ખેડૂત કલ્યાણ યોજનાઓ:\n\n"
                    "1. PM-KISAN: ખેડૂતોને વાર્ષિક ₹6,000 ની સહાય (3 હપ્તામાં ₹2,000).\n"
                    "2. PMFBY (પાક વીમા યોજના): પાક નુકસાની સામે વીમા સુરક્ષા (હેલ્પલાઇન: 14447).\n"
                    "3. કિસાન ક્રેડિટ કાર્ડ (KCC): 4% ના વ્યાજ દરે ₹3 લાખ સુધીની કૃષિ લોન.\n\n"
                    "📞 વધુ માહિતી માટે કિસાન કૉલ સેન્ટર 1800-180-1551 પર કૉલ કરો."
                )
            elif "punjabi" in lang or "ਪੰਜਾਬੀ" in lang:
                return (
                    "🌾 ਮੁੱਖ ਸਰਕਾਰੀ ਕਿਸਾਨ ਭਲਾਈ ਸਕੀਮਾਂ:\n\n"
                    "1. PM-KISAN: ਕਿਸਾਨਾਂ ਨੂੰ ਸਾਲਾਨਾ ₹6,000 ਦੀ ਸਿੱਧੀ ਵਿੱਤੀ ਸਹਾਇਤਾ (3 ਕਿਸ਼ਤਾਂ ਵਿੱਚ ₹2,000).\n"
                    "2. PMFBY (ਫ਼ਸਲ ਬੀਮਾ): ਫ਼ਸਲ ਦੇ ਨੁਕਸਾਨ 'ਤੇ ਬੀਮਾ ਮੁਆਵਜ਼ਾ (ਹੈਲਪਲਾਈਨ: 14447).\n"
                    "3. ਕਿਸਾਨ ਕ੍ਰੈਡਿਟ ਕਾਰਡ (KCC): 4% ਵਿਆਜ ਦਰ 'ਤੇ ₹3 ਲੱਖ ਤੱਕ ਦਾ ਖੇਤੀ ਕਰਜ਼ਾ।\n\n"
                    "📞 ਵਧੇਰੇ ਜਾਣਕਾਰੀ ਲਈ ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ 1800-180-1551 'ਤੇ ਕਾਲ ਕਰੋ।"
                )
            elif "malayalam" in lang or "മലയാളം" in lang:
                return (
                    "🌾 പ്രധാന സർക്കാർ കർഷക ക്ഷേമ പദ്ധതികൾ:\n\n"
                    "1. PM-KISAN: കർഷകർക്ക് പ്രതിവർഷം ₹6,000 ധനസഹായം (3 ഗഡുക്കളായി ₹2,000 വീതം).\n"
                    "2. PMFBY (വിള ഇൻഷുറൻസ്): വിളനാശത്തിന് സമഗ്ര ഇൻഷുറൻസ് പരിരക്ഷ (ഹെൽപ്പ്‌ലൈൻ: 14447).\n"
                    "3. കിസാൻ ക്രെഡിറ്റ് കാർഡ് (KCC): 4% പലിശ നിരക്കിൽ ₹3 ലക്ഷം വരെ വായ്പ.\n\n"
                    "📞 സഹായത്തിനായി കിസാൻ കോൾ സെന്റർ 1800-180-1551 എന്ന നമ്പറിൽ ബന്ധപ്പെടുക."
                )
            else:
                return (
                    "🌾 Major Government Schemes for Farmers:\n\n"
                    "1. PM-KISAN: Direct income support of ₹6,000/year in 3 equal installments (pmkisan.gov.in).\n"
                    "2. PMFBY (Crop Insurance): Comprehensive yield & weather risk cover at only 1.5% to 2% premium (pmfby.gov.in | Helpline: 14447).\n"
                    "3. Kisan Credit Card (KCC): Subsidized farm credit up to ₹3 Lakhs at 4% effective interest rate.\n"
                    "4. PMKSY (Per Drop More Crop): 45-55% subsidy on Drip and Sprinkler irrigation systems.\n"
                    "5. PM-KUSUM: Up to 60% subsidy for Solar Agricultural Water Pumps.\n\n"
                    "📞 Call Kisan Call Centre toll-free at 1800-180-1551 for application assistance."
                )

        # 2. Helplines Query
        if any(w in q_lower for w in ["helpline", "call", "contact", "expert", "number", "హెల్ప్‌లైన్", "ఫోన్", "నంబర్", "फोन", "नंबर", "தொடர்பு", "ಸಹಾಯವಾಣಿ"]):
            if "telugu" in lang or "తెలుగు" in lang:
                return (
                    "📞 ముఖ్యమైన రైతు హెల్ప్‌లైన్ నంబర్లు:\n\n"
                    "• కిసాన్ కాల్ సెంటర్ (KCC): 1800-180-1551 (ఉచితం - ఉదయం 6:00 నుండి రాత్రి 10:00 వరకు, తెలుగులో సలహాలు లభిస్తాయి)\n"
                    "• పంటల బీమా హెల్ప్‌లైన్ (PMFBY): 14447 (24 గంటలు)\n"
                    "• PM-KISAN సహాయవాణి: 155261 / 011-24300606\n"
                    "• ఏపీ వ్యవసాయ శాఖ (AP YSR): 1902 | తెలంగాణ కిసాన్ హెల్ప్‌లైన్: 040-23383520"
                )
            elif "hindi" in lang or "हिन्दी" in lang:
                return (
                    "📞 महत्वपूर्ण किसान हेल्पलाइन नंबर:\n\n"
                    "• किसान कॉल सेंटर (KCC): 1800-180-1551 (टोल फ्री - सुबह 6:00 से रात 10:00 बजे तक, सभी भाषाओं में)\n"
                    "• फसल बीमा हेल्पलाइन (PMFBY): 14447 (24x7)\n"
                    "• पीएम-किसान हेल्पलाइन: 155261 / 011-24300606\n"
                    "• किसान क्रेडिट कार्ड हेल्पडेस्क: 1800-11-2211"
                )
            elif "tamil" in lang or "தமிழ்" in lang:
                return (
                    "📞 முக்கிய விவசாய உதவி எண்கள்:\n\n"
                    "• கிசான் கால் சென்டர்: 1800-180-1551 (கட்டணமில்லா எண், காலை 6 முதல் இரவு 10 மணி வரை)\n"
                    "• பயிர் காப்பீட்டு உதவி: 14447\n"
                    "• பிஎம் கிசான் உதவி எண்: 155261"
                )
            elif "kannada" in lang or "ಕನ್ನಡ" in lang:
                return (
                    "📞 ಪ್ರಮುಖ ರೈತ ಸಹಾಯವಾಣಿ ಸಂಖ್ಯೆಗಳು:\n\n"
                    "• ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ (KCC): 1800-180-1551 (ಟೋಲ್ ಫ್ರೀ, ಬೆಳಗ್ಗೆ 6 ರಿಂದ ರಾತ್ರಿ 10 ರವರೆಗೆ)\n"
                    "• ಬೆಳೆ ವಿಮೆ ಸಹಾಯವಾಣಿ (PMFBY): 14447 (24x7)\n"
                    "• ಪಿಎಂ ಕಿಸಾನ್ ಹೆಲ್ಪ್‌ಲೈನ್: 155261\n"
                    "• ಕರ್ನಾಟಕ ರೈತ ಸಹಾಯವಾಣಿ: 1800-425-3553"
                )
            elif "marathi" in lang or "मराठी" in lang:
                return (
                    "📞 महत्त्वाचे शेतकरी हेल्पलाइन क्रमांक:\n\n"
                    "• किसान कॉल सेंटर (KCC): 1800-180-1551 (टोल फ्री - सकाळी 6 ते रात्री 10)\n"
                    "• पीक विमा हेल्पलाइन (PMFBY): 14447\n"
                    "• महाराष्ट्र शेतकरी सहाय्यता: 1800-233-4000"
                )
            else:
                return (
                    "📞 Official Farmer Helplines:\n\n"
                    "• Kisan Call Centre (KCC): 1800-180-1551 (Toll-Free, 6:00 AM - 10:00 PM, 22 languages)\n"
                    "• PMFBY Crop Insurance Support: 14447 (24x7 Toll-Free)\n"
                    "• PM-KISAN Helpdesk: 155261 / 011-24300606\n"
                    "• KCC Credit Support: 1800-11-2211"
                )

        # 3. Weather & Spraying Feasibility Query
        if any(w in q_lower for w in ["spray today", "rain today", "irrigate today", "వర్షం", "పిచికారీ", "मौसम", "छिड़काव", "மழை", "தெளிப்பு", "ಮಳೆ"]):
            is_rain_risk = "rain" in weather_context.lower() or "not recommended" in weather_context.lower()
            if "telugu" in lang or "తెలుగు" in lang:
                return (
                    "🌦️ వాతావరణ ఆధారిత సలహా:\n\n"
                    f"🔍 పరిస్థితి: {'వర్షం లేదా గాలుల తీవ్రత ఉంది' if is_rain_risk else 'వాతావరణం అనుకూలంగా ఉంది'}.\n"
                    f"🌱 సిఫార్సు: {'ఈరోజు మందు పిచికారీ చేయవద్దు. వర్షం వల్ల మందు వృథా అవుతుంది.' if is_rain_risk else 'ఉదయం లేదా సాయంత్రం వేళల్లో మందు పిచికారీ చేయవచ్చు.'}\n"
                    "⚠️ నివారించవలసినవి: తీవ్ర ఎండ లేదా గాలులు ఉన్నప్పుడు పిచికారీ చేయవద్దు."
                )
            elif "hindi" in lang or "हिन्दी" in lang:
                return (
                    "🌦️ मौसम आधारित कृषि सलाह:\n\n"
                    f"🔍 स्थिति: {'बारिश या तेज हवा का जोखिम है' if is_rain_risk else 'मौसम सामान्य एवं अनुकूल है'}.\n"
                    f"🌱 सलाह: {'आज किसी भी कीटनाशक का छिड़काव न करें। बारिश से दवा धुल जाएगी।' if is_rain_risk else 'सुबह या शाम के शांत मौसम में छिड़काव कर सकते हैं।'}\n"
                    "⚠️ क्या न करें: दोपहर की तेज धूप में छिड़काव न करें।"
                )
            elif "tamil" in lang or "தமிழ்" in lang:
                return (
                    "🌦️ வானிலை சார்ந்த விவசாய ஆலோசனை:\n\n"
                    f"🔍 நிலைமை: {'மழை அல்லது பலத்த காற்று வீச வாய்ப்புள்ளது' if is_rain_risk else 'வானிலை சாதகமாக உள்ளது'}.\n"
                    f"🌱 பரிந்துரை: {'இன்று பூச்சிக்கொல்லி தெளிப்பதை தவிர்க்கவும்.' if is_rain_risk else 'காலை அல்லது மாலை வேளையில் தெளிக்கலாம்.'}\n"
                    "⚠️ தவிர்க்க வேண்டியவை: காற்று அதிகமாக இருக்கும்போது மருந்து தெளிக்க வேண்டாம்."
                )
            elif "kannada" in lang or "ಕನ್ನಡ" in lang:
                return (
                    "🌦️ ಹವಾಮಾನ ಆಧಾರಿತ ಕೃಷಿ ಸಲಹೆ:\n\n"
                    f"🔍 ಸ್ಥಿತಿ: {'ಮಳೆ ಅಥವಾ ಗಾಳಿಯ ಸಾಧ್ಯತೆ ಇದೆ' if is_rain_risk else 'ಹವಾಮಾನ ಅನುಕೂಲಕರವಾಗಿದೆ'}.\n"
                    f"🌱 ಸಲಹೆ: {'ಇಂದು ಯಾವುದೇ ಕೀಟನಾಶಕ ಸಿಂಪಡಿಸಬೇಡಿ.' if is_rain_risk else 'ಬೆಳಿಗ್ಗೆ ಅಥವಾ ಸಂಜೆ ವೇಳೆ ಸಿಂಪಡಿಸಬಹುದು.'}\n"
                    "⚠️ ಎಚ್ಚರಿಕೆ: ಬಿಸಿಲಿನಲ್ಲಿ ಅಥವಾ ಜೋರು ಗಾಳಿಯಲ್ಲಿ ಸಿಂಪಡಣೆ ಮಾಡಬೇಡಿ."
                )
            elif "marathi" in lang or "मराठी" in lang:
                return (
                    "🌦️ हवामान आधारित कृषी सल्ला:\n\n"
                    f"🔍 स्थिती: {'पाऊस किंवा वेगवान वाऱ्याचा अंदाज आहे' if is_rain_risk else 'हवामान अनुकूल आहे'}.\n"
                    f"🌱 सल्ला: {'आज औषध फवारणी करू नका. पावसामुळे औषध वाहून जाईल.' if is_rain_risk else 'सकाळच्या किंवा संध्याकाळच्या वेळी फवारणी करू शकता.'}\n"
                    "⚠️ खबरदारी: दुपारच्या कडक उन्हात फवारणी टाळा."
                )
            else:
                return (
                    "🌦️ Weather-Aware Farming Advisory:\n\n"
                    f"🔍 Situation: {'High risk of rainfall or strong winds' if is_rain_risk else 'Weather is favorable'}.\n"
                    f"🌱 Recommendation: {'Do NOT spray chemicals today. Rain will wash them away.' if is_rain_risk else 'Spraying can be carried out during calm morning or late evening hours.'}\n"
                    "⚠️ What to Avoid: Avoid spraying during windy periods or peak midday sun."
                )

        # 4. Crop Specific Agricultural Guidance (Cotton, Rice, Tomato, Wheat, Groundnut, Chilli, etc.)
        crop_name = crop.title() if crop else "Your Crop"

        if "telugu" in lang or "తెలుగు" in lang:
            return (
                f"🌾 కిసాన్ AI వ్యవసాయ సలహా ({crop_name}):\n\n"
                f"🔍 ఏమి జరుగుతుండవచ్చు:\n"
                f"• మీ {crop_name} పంటలో పేర్కొన్న సమస్య (పురుగులు, తెగులు లేదా పోషకాల లోపం) ఉండవచ్చు.\n\n"
                f"💡 కారణాలు:\n"
                f"• అధిక తేమ, అసమతుల్య ఎరువుల వాడకం లేదా వాతావరణ మార్పుల వల్ల ఇది రావచ్చు.\n\n"
                f"🌱 మీరు వెంటనే చేయవలసిన పనులు:\n"
                f"1. పొలంలో లింగాకర్షక బుట్టలు (Pheromone traps @ 5/ఎకరాకు) అమర్చి పురుగుల ఉనికిని గమనించండి.\n"
                f"2. ప్రారంభ దశలో 5% వేప నూనె (Neem oil 10,000 ppm @ 2 మి.లీ/లీటరు) పిచికారీ చేయండి.\n"
                f"3. సమస్య తీవ్రంగా ఉంటే, సిఫార్సు చేసిన మందులను సరైన మోతాదులో మాత్రమే వాడండి.\n\n"
                f"⚠️ నివారించవలసినవి:\n"
                f"• వర్షం సూచన ఉన్నప్పుడు పిచికారీ చేయవద్దు. ఎల్లప్పుడూ మాస్క్, చేతి తొడుగులు ధరించండి.\n\n"
                f"📞 నిపుణుల సహాయం: కిసాన్ కాల్ సెంటర్ 1800-180-1551 ను సంప్రదించండి."
            )
        elif "hindi" in lang or "हिन्दी" in lang:
            return (
                f"🌾 किसान AI कृषि परामर्श ({crop_name}):\n\n"
                f"🔍 क्या समस्या हो सकती है:\n"
                f"• आपकी {crop_name} की फसल में कीट प्रकोप, फफूंद जनित धब्बे या पोषक तत्वों की कमी के लक्षण हो सकते हैं।\n\n"
                f"💡 कारण:\n"
                f"• अत्यधिक नमी, असंतुलित यूरिया का उपयोग या मौसम में बदलाव।\n\n"
                f"🌱 तुरंत किए जाने वाले उपाय:\n"
                f"1. खेत में फेरोमोन ट्रैप (5 प्रति एकड़) या पीले/नीले स्टिकी ट्रैप लगाएं।\n"
                f"2. शुरुआती रोकथाम के लिए 5% नीम तेल (2 मिली/लीटर) का छिड़काव करें।\n"
                f"3. मिट्टी की नमी जांचें और संतुलित खाद (NPK) का ही प्रयोग करें।\n\n"
                f"⚠️ क्या न करें:\n"
                f"• बारिश या तेज हवा में छिड़काव न करें। हमेशा मास्क और दस्ताने पहनें।\n\n"
                f"📞 विशेषज्ञ सहायता: किसान कॉल सेंटर 1800-180-1551 (टोल फ्री) पर कॉल करें।"
            )
        elif "tamil" in lang or "தமிழ்" in lang:
            return (
                f"🌾 கிசான் AI விவசாய ஆலோசனை ({crop_name}):\n\n"
                f"🔍 என்ன பிரச்சனை இருக்கலாம்:\n"
                f"• உங்கள் {crop_name} பயிரில் பூச்சி தாக்குதல் அல்லது இலைப்புள்ளி நோய் இருக்கலாம்.\n\n"
                f"🌱 உடனடியாக செய்ய வேண்டியவை:\n"
                f"1. வயலில் இனக்கவர்ச்சி பொறிகளை (5/ஏக்கர்) வைத்து பூச்சிகளை கண்காணிக்கவும்.\n"
                f"2. ஆரம்ப நிலையில் வேப்பெண்ணெய் கரைசல் (2 மிலி/லிட்டர்) தெளிக்கவும்.\n"
                f"3. சமச்சீரான உரங்களை (NPK) மட்டுமே இடவும்.\n\n"
                f"⚠️ தவிர்க்க வேண்டியவை:\n"
                f"• மழை வரும் போது மருந்து தெளிக்க வேண்டாம். பாதுகாப்பு உபகரணங்களை அணியவும்.\n\n"
                f"📞 உதவிக்கு: கிசான் கால் சென்டர் 1800-180-1551."
            )
        elif "kannada" in lang or "ಕನ್ನಡ" in lang:
            return (
                f"🌾 ಕಿಸಾನ್ AI ಕೃಷಿ ಸಲಹೆ ({crop_name}):\n\n"
                f"🔍 ಸಮಸ್ಯೆ ಏನಿರಬಹುದು:\n"
                f"• ನಿಮ್ಮ {crop_name} ಬೆಳೆಯಲ್ಲಿ ಕೀಟಬಾಧೆ, ಎಲೆ ಚುಕ್ಕೆ ರೋಗ ಅಥವಾ ಪೋಷಕಾಂಶಗಳ ಕೊರತೆ ಇರಬಹುದು.\n\n"
                f"🌱 ತುರ್ತು ಕ್ರಮಗಳು:\n"
                f"1. ಹೊಲದಲ್ಲಿ ಮೋಹಕ ಬಲೆಗಳನ್ನು (ಎಕರೆಗೆ 5) ಅಳವಡಿಸಿ ಕೀಟಗಳನ್ನು ನಿಯಂತ್ರಿಸಿ.\n"
                f"2. ಆರಂಭಿಕ ಹಂತದಲ್ಲಿ ಬೇವಿನ ಎಣ್ಣೆ (2 ಮಿಲಿ/ಲೀಟರ್) ಸಿಂಪಡಿಸಿ.\n"
                f"3. ಶಿಫಾರಸು ಮಾಡಿದ ಸಮತೋಲಿತ ರಸಗೊಬ್ಬರಗಳನ್ನು ಮಾತ್ರ ಬಳಸಿ.\n\n"
                f"⚠️ ಎಚ್ಚರಿಕೆ:\n"
                f"• ಮಳೆ ಅಥವಾ ಜೋರು ಗಾಳಿ ಇರುವಾಗ ಸಿಂಪಡಣೆ ಮಾಡಬೇಡಿ. ಮಾಸ್ಕ್ ಧರಿಸಿ.\n\n"
                f"📞 ಸಂಪರ್ಕಿಸಿ: ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ 1800-180-1551."
            )
        elif "marathi" in lang or "मराठी" in lang:
            return (
                f"🌾 किसान AI कृषी सल्ला ({crop_name}):\n\n"
                f"🔍 काय समस्या असू शकते:\n"
                f"• आपल्या {crop_name} पिकावर कीड प्रादुर्भाव, बुरशीजन्य डाग किंवा अन्नद्रव्यांची कमतरता असू शकते.\n\n"
                f"🌱 त्वरित उपाय:\n"
                f"1. शेतात कामगंध सापळे (प्रति एकरी 5) लावून किडींचे निरीक्षण करा.\n"
                f"2. सुरुवातीस 5% निंबोळी अर्क किंवा निम तेल (2 मिली/लिटर) फवारा.\n"
                f"3. नत्राचा (युरिया) अतिवापर टाळा व संतुलित खतांचा वापर करा.\n\n"
                f"⚠️ काय करू नये:\n"
                f"• पाऊस किंवा वाऱ्याच्या वेळी फवारणी टाळा. फवारणी करताना मास्क व हातमोजे वापरा.\n\n"
                f"📞 मदत: किसान कॉल सेंटर 1800-180-1551."
            )
        elif "bengali" in lang or "বাংলা" in lang:
            return (
                f"🌾 কিষাণ AI কৃষি পরামর্শ ({crop_name}):\n\n"
                f"🔍 সম্ভাব্য সমস্যা:\n"
                f"• আপনার {crop_name} ফসলে পোকার আক্রমণ, ছত্রাকজনিত দাগ বা পুষ্টির অভাব দেখা দিতে পারে।\n\n"
                f"🌱 তাৎক্ষণিক পদক্ষেপ:\n"
                f"1. জমিতে ফেরোমোন ট্র্যাপ (একর প্রতি ৫টি) বসিয়ে পোকার উপস্থিতি লক্ষ্য করুন।\n"
                f"2. প্রাথমিক অবস্থায় নিম তেল (২ মিলি/লিটার) স্প্রে করুন।\n"
                f"3. সুষম সার (NPK) ব্যবহার করুন।\n\n"
                f"⚠️ যা এড়িয়ে চলবেন:\n"
                f"• বৃষ্টির সম্ভাবনা থাকলে কীটনাশক স্প্রে করবেন না। স্প্রে করার সময় মাস্ক ব্যবহার করুন।\n\n"
                f"📞 সহায়তা: কিষাণ কল সেন্টার 1800-180-1551."
            )
        elif "gujarati" in lang or "ગુજરાતી" in lang:
            return (
                f"🌾 કિસાન AI કૃષિ માર્ગદર્શન ({crop_name}):\n\n"
                f"🔍 શું સમસ્યા હોઈ શકે:\n"
                f"• તમારા {crop_name} પાકમાં જીવાતનો ઉપદ્રવ, પાન પર ડાઘ અથવા પોષક તત્વોની ઉણપ હોઈ શકે છે.\n\n"
                f"🌱 તાત્કાલિક પગલાં:\n"
                f"1. ખેતરમાં ફેરોમોન ટ્રેપ લગાવો.\n"
                f"2. શરૂઆતમાં લીંબોળીનું તેલ (2 મિલી/લીટર) છંટકાવ કરો.\n"
                f"3. સંતુલિત ખાતરનો ઉપયોગ કરો.\n\n"
                f"⚠️ સાવચેતી: વરસાદની શક્યતા હોય ત્યારે છંટકાવ ન કરવો. માસ્ક પહેરવું.\n\n"
                f"📞 સહાય માટે: કિસાન કૉલ સેન્ટર 1800-180-1551."
            )
        elif "punjabi" in lang or "ਪੰਜਾਬੀ" in lang:
            return (
                f"🌾 ਕਿਸਾਨ AI ਖੇਤੀ ਸਲਾਹ ({crop_name}):\n\n"
                f"🔍 ਕੀ ਸਮੱਸਿਆ ਹੋ ਸਕਦੀ ਹੈ:\n"
                f"• ਤੁਹਾਡੀ {crop_name} ਦੀ ਫ਼ਸਲ ਵਿੱਚ ਕੀੜੇ-ਮਕੌੜੇ, ਉੱਲੀ ਦੇ ਧੱਬੇ ਜਾਂ ਖਾਦ ਦੀ ਘਾਟ ਹੋ ਸਕਦੀ ਹੈ।\n\n"
                f"🌱 ਤੁਰੰਤ ਕਾਰਵਾਈ:\n"
                f"1. ਖੇਤ ਵਿੱਚ ਫ਼ੇਰੋਮੋਨ ਟਰੈਪ ਲਗਾਓ।\n"
                f"2. ਸ਼ੁਰੂਆਤੀ ਰੋਕਥਾਮ ਲਈ ਨਿੰਮ ਦੇ ਤੇਲ (2 ਮਿ.ਲੀ./ਲਿਟਰ) ਦਾ ਛਿੜਕਾਅ ਕਰੋ।\n"
                f"3. ਸਿਫ਼ਾਰਸ਼ ਕੀਤੀ ਸੰਤੁਲਿਤ ਖਾਦ ਹੀ ਪਾਓ।\n\n"
                f"⚠️ ਸਾਵਧਾਨੀ: ਮੀਂਹ ਦੇ ਮੌਸਮ ਵਿੱਚ ਛਿੜਕਾਅ ਨਾ ਕਰੋ। ਮਾਸਕ ਜ਼ਰੂਰ ਪਹਿਨੋ।\n\n"
                f"📞 ਸੰਪਰਕ ਕਰੋ: ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ 1800-180-1551."
            )
        elif "malayalam" in lang or "മലയാളം" in lang:
            return (
                f"🌾 കിസാൻ AI കൃഷി ഉപദേശം ({crop_name}):\n\n"
                f"🔍 സാധ്യമായ പ്രശ്നം:\n"
                f"• നിങ്ങളുടെ {crop_name} കൃഷിയിൽ കീടബാധയോ ഇലപ്പുള്ളി രോഗമോ പോഷകക്കുറവോ ഉണ്ടാകാം.\n\n"
                f"🌱 ഉടനടി ചെയ്യേണ്ട കാര്യങ്ങൾ:\n"
                f"1. കീടങ്ങളെ നിരീക്ഷിക്കാൻ ഫെറമോൺ കെണികൾ സ്ഥാപിക്കുക.\n"
                f"2. തുടക്കത്തിൽ വേപ്പെണ്ണ മിശ്രിതം (2 മില്ലി/ലിറ്റർ) തളിക്കുക.\n"
                f"3. സമീകൃത വളപ്രയോഗം നടത്തുക.\n\n"
                f"⚠️ ഒഴിവാക്കേണ്ടവ: മഴയുള്ളപ്പോൾ മരുന്ന് തളിക്കരുത്. മാസ്ക് ധരിക്കുക.\n\n"
                f"📞 ഹെൽപ്പ്‌ലൈൻ: കിസാൻ കോൾ സെന്റർ 1800-180-1551."
            )
        else:
            return (
                f"🌾 Kisan AI Farming Advisory ({crop_name}):\n\n"
                f"🔍 What May Be Happening:\n"
                f"• Your {crop_name} crop may be experiencing pest infestation, fungal foliage spots, or moisture/nutrient stress.\n\n"
                f"💡 Why It May Be Happening:\n"
                f"• High atmospheric humidity, imbalanced nitrogen fertilizer application, or recent weather shifts.\n\n"
                f"🌱 What You Should Do Now:\n"
                f"1. Inspect leaf undersides and install pheromone/sticky traps (5-10 per acre) for pest monitoring.\n"
                f"2. Apply organic neem oil formulation (5% NSKE or 10,000 ppm @ 2 ml/L) as early protection.\n"
                f"3. Ensure good field drainage and avoid unnecessary water stagnation.\n\n"
                f"⚠️ What To Avoid:\n"
                f"• Never spray during midday heat or when rain is expected. Always wear protective gloves and a face mask.\n\n"
                f"📞 Expert Support:\n"
                f"• For personalized inspection, contact Kisan Call Centre toll-free at 1800-180-1551 or your local KVK."
            )


# Global Singleton LLM Service
llm_service = LLMService()


def get_ai_response(prompt: str) -> str:
    """Convenience wrapper for raw prompt generation."""
    return llm_service.generate_response(prompt)