// ==============================================================================
// KISAN AI - FRONTEND CLIENT JAVASCRIPT
// ==============================================================================

const isDifferentDevPort = (window.location.port && window.location.port !== "8000" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"));
const API_BASE = window.KISAN_API_BASE || window.API_BASE || ((!window.location.protocol.startsWith("http") || isDifferentDevPort)
    ? "http://127.0.0.1:8000"
    : window.location.origin);

let sessionId = "session-" + Math.random().toString(36).substring(2, 9);
let currentSelectedLanguage = "Telugu";
let currentDetectedLocation = "Guntur, Andhra Pradesh";
let isListeningSpeech = false;
let recognition = null;
let currentUploadedImageFile = null;

// Speech Recognition Language Codes
const SPEECH_LANG_CODES = {
    "English": "en-IN",
    "Telugu": "te-IN",
    "Hindi": "hi-IN",
    "Tamil": "ta-IN",
    "Kannada": "kn-IN",
    "Malayalam": "ml-IN",
    "Marathi": "mr-IN",
    "Bengali": "bn-IN",
    "Gujarati": "gu-IN",
    "Punjabi": "pa-IN"
};

// Multilingual Quick Prompts
const MULTILINGUAL_QUICK_PROMPTS = {
    "English": [
        { label: "🌾 Rice Fertilizer Recommendation", prompt: "What fertilizer should I use for rice?" },
        { label: "🐛 Cotton Pest Control & Spraying", prompt: "My cotton crop has pest problems. Can I spray pesticide today?" },
        { label: "🍅 Tomato Yellow Leaves with Spots", prompt: "My tomato leaves are turning yellow with dark spots. What should I do?" },
        { label: "🌦️ Can I spray pesticide today?", prompt: "Is today's weather suitable for spraying pesticides?" },
        { label: "💧 Irrigation Advice for Crops", prompt: "Should I irrigate my crop today based on weather?" },
        { label: "🏛️ Major Government Schemes", prompt: "What government schemes are available for farmers?" },
        { label: "📞 Contact Farmer Helpline", prompt: "I need agricultural expert helpline numbers" },
        { label: "📷 Scan Crop Disease", action: "open-scanner" }
    ],
    "Telugu": [
        { label: "🌾 వరి ఎరువులు (Rice Fertilizer)", prompt: "వరి పంటకు ఏ ఎరువు వేయాలి?" },
        { label: "🐛 పత్తి పురుగులు & పిచికారీ (Cotton Pests)", prompt: "నా పత్తి పంటకు పురుగులు వచ్చాయి. ఈరోజు మందు పిచికారీ చేయవచ్చా?" },
        { label: "🍅 టమోటా ఆకుమచ్చల నివారణ", prompt: "టమోటా ఆకులు పసుపు రంగులోకి మారి మచ్చలు వస్తున్నాయి. ఏమి చేయాలి?" },
        { label: "🌦️ ఈరోజు మందు పిచికారీ చేయవచ్చా?", prompt: "ఈరోజు వాతావరణం మందు పిచికారీకి అనుకూలమా?" },
        { label: "💧 నీటిపారుదల సలహా", prompt: "ఈరోజు పంటకు నీరు పెట్టవచ్చా?" },
        { label: "🏛️ ప్రభుత్వ పథకాలు (Govt Schemes)", prompt: "రైతులకు ఉన్న ప్రధాన ప్రభుత్వ పథకాలు ఏమిటి?" },
        { label: "📞 రైతు హెల్ప్‌లైన్ (Farmer Helpline)", prompt: "నాకు అత్యవసర వ్యవసాయ నిపుణుల హెల్ప్‌లైన్ నంబర్ కావాలి" },
        { label: "📷 ఆకుల ఫోటోతో తెగులు గుర్తింపు", action: "open-scanner" }
    ],
    "Hindi": [
        { label: "🌾 धान के लिए खाद (Rice Fertilizer)", prompt: "धान की फसल के लिए कौन सी खाद उपयोगी है?" },
        { label: "🐛 कपास में कीट नियंत्रण (Cotton Pests)", prompt: "मेरी कपास की फसल में कीट लग गए हैं, क्या आज दवा छिड़क सकते हैं?" },
        { label: "🍅 टमाटर के पत्तों पर पीले धब्बे", prompt: "टमाटर के पत्ते पीले पड़ रहे हैं और धब्बे हैं, क्या उपाय करें?" },
        { label: "🌦️ क्या आज कीटनाशक छिड़कें?", prompt: "क्या आज का मौसम कीटनाशक छिड़काव के लिए अनुकूल है?" },
        { label: "💧 फसल में सिंचाई की सलाह", prompt: "क्या आज फसल की सिंचाई करनी चाहिए?" },
        { label: "🏛️ सरकारी किसान योजनाएं", prompt: "किसानों के लिए प्रमुख सरकारी योजनाएं कौन सी हैं?" },
        { label: "📞 किसान हेल्पलाइन नंबर", prompt: "कृषि विशेषज्ञ हेल्पलाइन नंबर चाहिए" },
        { label: "📷 पौधे की फोटो से रोग पहचानें", action: "open-scanner" }
    ],
    "Tamil": [
        { label: "🌾 நெல் பயிர் உர மேலாண்மை", prompt: "நெல் பயிருக்கு என்ன உரம் இட வேண்டும்?" },
        { label: "🐛 பருத்தி பூச்சி கட்டுப்பாடு", prompt: "பருத்தியில் பூச்சி தாக்குதல் உள்ளது. இன்று மருந்து தெளிக்கலாமா?" },
        { label: "🍅 தக்காளி இலைப்புள்ளி நோய்", prompt: "தக்காளி இலைகள் மஞ்சளாக மாறுகின்றன, என்ன செய்வது?" },
        { label: "🌦️ இன்று மருந்து தெளிக்கலாமா?", prompt: "இன்றைய வானிலை மருந்து தெளிக்க உகந்ததா?" },
        { label: "💧 பாசன ஆலோசனை", prompt: "இன்று பயிருக்கு தண்ணீர் பாய்ச்ச வேண்டுமா?" },
        { label: "🏛️ அரசு விவசாய திட்டங்கள்", prompt: "விவசாயிகளுக்கான முக்கிய அரசு திட்டங்கள் என்ன?" },
        { label: "📞 விவசாய உதவி எண்", prompt: "வேளாண் துறை உதவி எண்கள் தேவை" },
        { label: "📷 புகைப்பட நோய் கண்டறிதல்", action: "open-scanner" }
    ],
    "Kannada": [
        { label: "🌾 ಭತ್ತದ ಬೆಳೆಗೆ ರಸಗೊಬ್ಬರ", prompt: "ಭತ್ತದ ಬೆಳೆಗೆ ಯಾವ ಗೊಬ್ಬರ ಹಾಕಬೇಕು?" },
        { label: "🐛 ಹತ್ತಿ ಕೀಟ ನಿಯಂತ್ರಣ", prompt: "ನನ್ನ ಹತ್ತಿ ಬೆಳೆಗೆ ಕೀಟಗಳು ಬಂದಿವೆ. ಇಂದು ಕೀಟನಾಶಕ ಸಿಂಪಡಿಸಬಹುದೇ?" },
        { label: "🍅 ಟೊಮ್ಯಾಟೊ ಎಲೆ ಹಳದಿ ರೋಗ", prompt: "ಟೊಮ್ಯಾಟೊ ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ, ಏನು ಮಾಡಬೇಕು?" },
        { label: "🌦️ ಇಂದು ಸಿಂಪಡಣೆ ಮಾಡಬಹುದೇ?", prompt: "ಇಂದಿನ ಹವಾಮಾನ ಕೀಟನಾಶಕ ಸಿಂಪಡಣೆಗೆ ಸೂಕ್ತವೇ?" },
        { label: "💧 ನೀರಾವರಿ ಸಲಹೆ", prompt: "ಇಂದು ಬೆಳೆಗೆ ನೀರು ಹಾಯಿಸಬೇಕೆ?" },
        { label: "🏛️ ಸರ್ಕಾರಿ ರೈತ ಯೋಜನೆಗಳು", prompt: "ರೈತರಿಗೆ ಲಭ್ಯವಿರುವ ಪ್ರಮುಖ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಯಾವುವು?" },
        { label: "📞 ರೈತ ಸಹಾಯವಾಣಿ", prompt: "ಕೃಷಿ ತಜ್ಞರ ಸಹಾಯವಾಣಿ ಸಂಖ್ಯೆ ಬೇಕು" },
        { label: "📷 ಬೆಳೆ ರೋಗ ಪತ್ತೆ", action: "open-scanner" }
    ],
    "Marathi": [
        { label: "🌾 भात पीक खत व्यवस्थापन", prompt: "भात पिकासाठी कोणते खत योग्य आहे?" },
        { label: "🐛 कापूस बोंडअळी नियंत्रण", prompt: "कापूस पिकावर कीड पडली आहे, आज फवारणी करावी का?" },
        { label: "🍅 टोमॅटो पानांवरील पिवळे डाग", prompt: "टोमॅटोची पाने पिवळी पडत आहेत, काय उपाय करावा?" },
        { label: "🌦️ आज औषध फवारणी करावी का?", prompt: "आजचे हवामान कीटकनाशक फवारणीसाठी योग्य आहे का?" },
        { label: "💧 पाणी व्यवस्थापन", prompt: "आज पिकाला पाणी द्यावे का?" },
        { label: "🏛️ शासकीय शेतकरी योजना", prompt: "शेतकऱ्यांसाठी कोणत्या शासकीय योजना आहेत?" },
        { label: "📞 शेतकरी हेल्पलाइन", prompt: "कृषी तज्ज्ञांचा हेल्पलाइन नंबर हवा आहे" },
        { label: "📷 फोटोवरून रोग ओळखा", action: "open-scanner" }
    ],
    "Bengali": [
        { label: "🌾 ধান চাষে সার প্রয়োগ", prompt: "ধানের জন্য কোন সার ব্যবহার করব?" },
        { label: "🐛 তুলা ও ফসলে পোকা দমন", prompt: "ফসলে পোকা লেগেছে, আজ কি ওষুধ স্প্রে করা যাবে?" },
        { label: "🍅 টমেটো পাতার হলুদ দাগ", prompt: "টমেটো পাতা হলুদ হয়ে যাচ্ছে, কি করব?" },
        { label: "🌦️ আজ কি স্প্রে করা যাবে?", prompt: "আজকের আবহাওয়া কি কীটনাশক স্প্রে করার উপযোগী?" },
        { label: "💧 সেচ পরামর্শ", prompt: "আজ কি জমিতে জল সেচ দেওয়া উচিত?" },
        { label: "🏛️ সরকারি কৃষক প্রকল্প", prompt: "কৃষকদের জন্য কি কি সরকারি প্রকল্প আছে?" },
        { label: "📞 কৃষক হেল্পলাইন", prompt: "কৃষি বিশেষজ্ঞ হেল্পলাইন নম্বর চাই" },
        { label: "📷 পাতার ছবি দিয়ে রোগ নির্ণয়", action: "open-scanner" }
    ],
    "Gujarati": [
        { label: "🌾 ડાંગર માટે ખાતર ભલામણ", prompt: "ડાંગરના પાક માટે કયું ખાતર આપવું?" },
        { label: "🐛 કપાસમાં જીવાત નિયંત્રણ", prompt: "કપાસમાં જીવાત આવી ગઈ છે, આજે દવાનો છંટકાવ કરી શકાય?" },
        { label: "🍅 ટામેટાના પાન પીળા પડવા", prompt: "ટામેટાના પાન પીળા પડી રહ્યા છે, શું કરવું?" },
        { label: "🌦️ શું આજે દવાનો છંટકાવ કરવો?", prompt: "શું આજનું હવામાન છંટકાવ માટે યોગ્ય છે?" },
        { label: "💧 સિંચાઈ સલાહ", prompt: "શું આજે પાકને પાણી આપવું જોઈએ?" },
        { label: "🏛️ સરકારી ખેડૂત યોજનાઓ", prompt: "ખેડૂતો માટે કઈ સરકારી યોજનાઓ છે?" },
        { label: "📞 કિસાન હેલ્પલાઇન", prompt: "કૃષિ નિષ્ણાત હેલ્પલાઇન નંબર જોઈએ છે" },
        { label: "📷 ફોટા પરથી રોગ નિદાન", action: "open-scanner" }
    ],
    "Punjabi": [
        { label: "🌾 ਝੋਨੇ/ਕਣਕ ਲਈ ਖਾਦ", prompt: "ਝੋਨੇ/ਕਣਕ ਦੀ ਫ਼ਸਲ ਲਈ ਕਿਹੜੀ ਖਾਦ ਪਾਈਏ?" },
        { label: "🐛 ਕਪਾਹ ਦੇ ਕੀੜਿਆਂ ਦੀ ਰੋਕਥਾਮ", prompt: "ਕਪਾਹ 'ਤੇ ਕੀੜੇ ਪੈ ਗਏ ਹਨ, ਕੀ ਅੱਜ ਸਪਰੇਅ ਕਰ ਸਕਦੇ ਹਾਂ?" },
        { label: "🍅 ਟਮਾਟਰ ਦੇ ਪੱਤਿਆਂ 'ਤੇ ਪੀਲੇ ਧੱਬੇ", prompt: "ਟਮਾਟਰ ਦੇ ਪੱਤੇ ਪੀਲੇ ਹੋ ਰਹੇ ਹਨ, ਕੀ ਕਰੀਏ?" },
        { label: "🌦️ ਕੀ ਅੱਜ ਸਪਰੇਅ ਕੀਤੀ ਜਾਵੇ?", prompt: "ਕੀ ਅੱਜ ਦਾ ਮੌਸਮ ਸਪਰੇਅ ਕਰਨ ਲਈ ਠੀਕ ਹੈ?" },
        { label: "💧 ਸਿੰਚਾਈ ਸਲਾਹ", prompt: "ਕੀ ਅੱਜ ਫ਼ਸਲ ਨੂੰ ਪਾਣੀ ਲਗਾਈਏ?" },
        { label: "🏛️ ਸਰਕਾਰੀ ਕਿਸਾਨ ਸਕੀਮਾਂ", prompt: "ਕਿਸਾਨਾਂ ਲਈ ਮੁੱਖ ਸਰਕਾਰੀ ਸਕੀਮਾਂ ਕਿਹੜੀਆਂ ਹਨ?" },
        { label: "📞 ਕਿਸਾਨ ਹੈਲਪਲਾਈਨ", prompt: "ਖੇਤੀ ਮਾਹਿਰਾਂ ਦਾ ਹੈਲਪਲਾਈਨ ਨੰਬਰ ਚਾਹੀਦਾ ਹੈ" },
        { label: "📷 ਫ਼ੋਟੋ ਤੋਂ ਬਿਮਾਰੀ ਦੀ ਪਛਾਣ", action: "open-scanner" }
    ],
    "Malayalam": [
        { label: "🌾 നെല്ല് വളപ്രയോഗം", prompt: "നെല്ലിന് ഏത് വളമാണ് ഉപയോഗിക്കേണ്ടത്?" },
        { label: "🐛 കീടനിയന്ത്രണവും മരുന്ന് തളിക്കലും", prompt: "വിളകളിൽ കീടബാധയുണ്ട്, ഇന്ന് മരുന്ന് തളിക്കാമോ?" },
        { label: "🍅 തക്കാളി ഇലപ്പുള്ളി രോഗം", prompt: "തക്കാളി ഇലകൾ മഞ്ഞനിറമാകുന്നു, എന്ത് ചെയ്യണം?" },
        { label: "🌦️ ഇന്ന് കീടനാശിനി തളിക്കാമോ?", prompt: "ഇന്നത്തെ കാലാവസ്ഥ മരുന്ന് തളിക്കാൻ അനുയോജ്യമാണോ?" },
        { label: "💧 ജലസേചന ഉപദേശം", prompt: "ഇന്ന് കൃഷിക്ക് നനയ്ക്കണോ?" },
        { label: "🏛️ സർക്കാർ കർഷക പദ്ധതികൾ", prompt: "കർഷകർക്കുള്ള പ്രധാന സർക്കാർ പദ്ധതികൾ ഏവ?" },
        { label: "📞 കർഷക ഹെൽപ്പ്‌ലൈൻ", prompt: "കാർഷിക വിദഗ്ദ്ധരുടെ ഹെൽപ്പ്‌ലൈൻ നമ്പർ വേണം" },
        { label: "📷 രോഗം തിരിച്ചറിയുക", action: "open-scanner" }
    ]
};

// Client-side Offline Agricultural Knowledge Engine
const clientOfflineKnowledge = [
    {
        keywords: ["వరి", "rice", "paddy", "ఎరువు", "fertilizer", "dap", "urea", "खाद", "удобрение", "உரம்", "ಗೊಬ್ಬರ", "সার"],
        answer: "🌾 Crop Fertilizer Management:\n• Recommended NPK per acre: 40-50 kg Nitrogen, 20-25 kg Phosphorus, 20-25 kg Potash.\n• Basal dose: Apply all Phosphorus, 50% Nitrogen, and 50% Potash during final land preparation.\n• Top dressing: Split remaining Nitrogen at active tillering and panicle initiation stages.\n• Apply Zinc Sulphate 10-15 kg/acre to prevent zinc deficiency."
    },
    {
        keywords: ["పత్తి", "cotton", "పురుగు", "pest", "పిచికారీ", "spray", "कीट", "छिड़काव", "பூச்சி", "ಕೀಟ"],
        answer: "🌾 Cotton Pest Control & Spraying Advisory:\n1. Install pheromone traps @ 5/acre to monitor Pink Bollworm activity.\n2. Apply 5% Neem Seed Kernel Extract (NSKE) or Neem oil 2 ml/L during early infestation.\n3. If pest exceeds threshold: Emamectin Benzoate 5% SG @ 80-100 g/acre or Spinetoram in 200L water.\n⚠️ Do not spray when rain is expected or in high winds. Always wear a mask and gloves."
    },
    {
        keywords: ["tomato", "టమోటా", "yellow", "blight", "spot", "ఆకుమచ్చ", "टमाटर", "पीला", "धब्बा", "இலை"],
        answer: "🍅 Tomato Crop Disease Advisory:\n• Leaf yellowing with brown concentric rings indicates Early Blight (Alternaria solani).\n• Recommended Action: Remove infected bottom foliage, avoid overhead sprinkler watering, and maintain airflow.\n• Safe Treatment: Spray Mancozeb 75% WP @ 2g/L or Azoxystrobin + Difenoconazole @ 1ml/L.\n⚠️ Wear protective mask and gloves. Respect 5-day pre-harvest interval."
    },
    {
        keywords: ["scheme", "పథకం", "pm-kisan", "pmfby", "యोजना", "योजना", "திட்டம்", "ಯೋಜನೆ", "প্রকল্প"],
        answer: "🏛️ Major Government Schemes for Farmers:\n1. PM-KISAN: ₹6,000/year direct financial support in 3 equal installments.\n2. PMFBY (Crop Insurance): High-subsidy crop loss coverage (Helpline: 14447).\n3. Kisan Credit Card (KCC): Subsidized farm credit up to ₹3 Lakhs at 4% interest.\n📞 Contact Kisan Call Centre toll-free at 1800-180-1551 for application support."
    },
    {
        keywords: ["helpline", "నంబర్", "హెల్ప్‌లైన్", "contact", "phone", "number", "नंबर", "உதவி", "ಸಹಾಯವಾಣಿ"],
        answer: "📞 Official Farmer Helplines:\n• Kisan Call Centre (KCC): 1800-180-1551 (Toll-Free, 6:00 AM to 10:00 PM, all Indian languages)\n• PMFBY Crop Insurance Helpline: 14447 (24x7)\n• PM-KISAN Helpdesk: 155261 / 011-24300606"
    }
];

// ==============================================================================
// INITIALIZATION ON DOM LOAD
// ==============================================================================
document.addEventListener("DOMContentLoaded", function () {
    initializeLanguage();
    initializeSpeechRecognition();
    initializeWeather();
    initializeChatEvents();
    initializeModals();
    checkSystemHealth();
});

// ------------------------------------------------------------------------------
// LANGUAGE MANAGEMENT
// ------------------------------------------------------------------------------
const INPUT_PLACEHOLDERS = {
    "English": "Ask your farming question or speak here (e.g. What fertilizer should I use for rice?)...",
    "Telugu": "మీ వ్యవసాయ సమస్యను ఇక్కడ అడగండి లేదా మాట్లాడండి (ఉదా: వరి పంటకు ఏ ఎరువు వేయాలి?)...",
    "Hindi": "अपना कृषि प्रश्न यहाँ पूछें या बोलें (उदा: धान की फसल के लिए कौन सी खाद उपयोगी है?)...",
    "Tamil": "உங்கள் விவசாய கேள்வியை இங்கே கேட்கவும் (எ.கா: நெல் பயிருக்கு என்ன உரம் இட வேண்டும்?)...",
    "Kannada": "ನಿಮ್ಮ ಕೃಷಿ ಪ್ರಶ್ನೆಯನ್ನು ಇಲ್ಲಿ ಕೇಳಿ (ಉದಾ: ಭತ್ತದ ಬೆಳೆಗೆ ಯಾವ ಗೊಬ್ಬರ ಹಾಕಬೇಕು?)...",
    "Marathi": "तुमचा शेतीविषयक प्रश्न येथे विचारा किंवा बोला (उदा: कापूस पिकावर काय फवारावे?)...",
    "Bengali": "আপনার কৃষি প্রশ্ন এখানে লিখুন বা বলুন (যেমন: ধানের জন্য কোন সার ব্যবহার করব?)...",
    "Gujarati": "તમારો ખેતી પ્રશ્ન અહીં પૂછો (ઉદા: કપાસમાં જીવાત માટે શું કરવું?)...",
    "Punjabi": "ਆਪਣਾ ਖੇਤੀ ਸਵਾਲ ਇੱਥੇ ਪੁੱਛੋ (ਜਿਵੇਂ: ਕਣਕ/ਝੋਨੇ ਲਈ ਕਿਹੜੀ ਖਾਦ ਪਾਈਏ?)...",
    "Malayalam": "നിങ്ങളുടെ കാർഷിക ചോദ്യം ഇവിടെ ചോദിക്കുക (ഉദാ: നെല്ലിന് ഏത് വളമാണ് നല്ലത്?)..."
};

function initializeLanguage() {
    const langSelect = document.getElementById("languageSelect");
    currentSelectedLanguage = langSelect.value;

    function applyLanguageChange(lang) {
        currentSelectedLanguage = lang;
        console.log("Language switched to:", currentSelectedLanguage);

        if (isListeningSpeech && recognition) {
            recognition.stop();
        }

        // Update welcome message, quick prompts, and placeholder
        updateWelcomeMessage(currentSelectedLanguage);
        renderQuickPrompts(currentSelectedLanguage);

        const textInput = document.getElementById("chatTextInput");
        if (textInput) {
            textInput.placeholder = INPUT_PLACEHOLDERS[currentSelectedLanguage] || INPUT_PLACEHOLDERS["English"];
        }
    }

    langSelect.addEventListener("change", function () {
        applyLanguageChange(this.value);
    });

    // Render initial prompts and placeholder
    applyLanguageChange(currentSelectedLanguage);
}

function renderQuickPrompts(lang) {
    const promptsContainer = document.querySelector(".prompts-scroll");
    if (!promptsContainer) return;

    const promptsList = MULTILINGUAL_QUICK_PROMPTS[lang] || MULTILINGUAL_QUICK_PROMPTS["English"];
    promptsContainer.innerHTML = promptsList.map(p => {
        if (p.action === "open-scanner") {
            return `<button type="button" class="prompt-chip" data-action="open-scanner">${p.label}</button>`;
        }
        return `<button type="button" class="prompt-chip" data-prompt="${p.prompt}">${p.label}</button>`;
    }).join("");
}

function updateWelcomeMessage(lang) {
    const welcome = document.getElementById("welcomeMessageContent");
    const subtext = document.getElementById("chatSubtext");

    if (lang === "Telugu") {
        welcome.innerHTML = "నమస్కారం! నేను మీ <strong>కిసాన్ AI (Kisan AI)</strong> వ్యవసాయ సలహాదారుని. మీ పంటలు, పురుగులు, తెగుళ్ళు, ఎరువులు, నీటిపారుదల, వాతావరణం లేదా ప్రభుత్వ పథకాల గురించి మాట్లాడి (Voice) లేదా టైప్ చేసి అడగండి.";
        subtext.textContent = "వాయిస్ • టెక్స్ట్ • ఫోటో ద్వారా వ్యవసాయ సలహా";
    } else if (lang === "Hindi") {
        welcome.innerHTML = "नमस्ते! मैं आपका <strong>किसान AI (Kisan AI)</strong> कृषि सलाहकार हूँ। आप अपनी फसलों, कीटों, रोगों, खाद, सिंचाई, मौसम या सरकारी योजनाओं के बारे में बोलकर (Voice) या लिखकर पूछ सकते हैं।";
        subtext.textContent = "बोलकर • लिखकर • फोटो से कृषि सलाह प्राप्त करें";
    } else if (lang === "Tamil") {
        welcome.innerHTML = "வணக்கம்! நான் உங்கள் <strong>கிசான் AI (Kisan AI)</strong> விவசாய உதவியாளர். பயிர்கள், பூச்சிகள், உரங்கள், வானிலை மற்றும் அரசு திட்டங்கள் பற்றி பேசலாம் அல்லது தட்டச்சு செய்யலாம்.";
        subtext.textContent = "குரல் • உரை • புகைப்படம் மூலம் விவசாய ஆலோசனை";
    } else if (lang === "Kannada") {
        welcome.innerHTML = "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ <strong>ಕಿಸಾನ್ AI (Kisan AI)</strong> ಕೃಷಿ ಸಹಾಯಕ. ನಿಮ್ಮ ಬೆಳೆಗಳು, ಕೀಟಗಳು, ಗೊಬ್ಬರ, ಹವಾಮಾನ ಮತ್ತು ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಕುರಿತು ಧ್ವನಿ ಅಥವಾ ಪಠ್ಯದ ಮೂಲಕ ಕೇಳಿ.";
        subtext.textContent = "ಧ್ವನಿ • ಪಠ್ಯ • ಫೋಟೋ ಮೂಲಕ ಕೃಷಿ ಸಲಹೆ ಪಡೆಯಿರಿ";
    } else if (lang === "Marathi") {
        welcome.innerHTML = "नमस्कार! मी तुमचा <strong>किसान AI (Kisan AI)</strong> शेती सल्लागार आहे. पिके, कीड, रोग, खते, पाणी व्यवस्थापन, हवामान आणि सरकारी योजनांबद्दल बोलून किंवा लिहून विचारू शकता.";
        subtext.textContent = "आवाज • मजकूर • फोटोद्वारे शेती सल्ला मिळवा";
    } else if (lang === "Bengali") {
        welcome.innerHTML = "নমস্কার! আমি আপনার <strong>কিষাণ AI (Kisan AI)</strong> কৃষি উপদেষ্টা। ফসল, পোকা, রোগ, সার, সেচ, আবহাওয়া এবং সরকারি প্রকল্প সম্পর্কে মুখে বলে বা লিখে প্রশ্ন করতে পারেন।";
        subtext.textContent = "ভয়েস • টেক্সট • ছবির মাধ্যমে নির্ভরযোগ্য কৃষি পরামর্শ";
    } else if (lang === "Gujarati") {
        welcome.innerHTML = "નમસ્તે! હું તમારો <strong>કિસાન AI (Kisan AI)</strong> કૃષિ સહાયક છું. પાક, જીવાત, રોગ, ખાતર, સિંચાઈ, હવામાન અને સરકારી યોજનાઓ વિશે બોલીને કે લખીને પૂછી શકો છો.";
        subtext.textContent = "બોલીને • લખીને • ફોટો દ્વારા સચોટ ખેતી માર્ગદર્શન";
    } else if (lang === "Punjabi") {
        welcome.innerHTML = "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ <strong>ਕਿਸਾਨ AI (Kisan AI)</strong> ਖੇਤੀ ਸਲਾਹਕਾਰ ਹਾਂ। ਫ਼ਸਲਾਂ, ਕੀੜੇ-ਮਕੌੜੇ, ਖਾਦਾਂ, ਸਿੰਚਾਈ, ਮੌਸਮ ਅਤੇ ਸਰਕਾਰੀ ਸਕੀਮਾਂ ਬਾਰੇ ਬੋਲ ਕੇ ਜਾਂ ਲਿਖ ਕੇ ਪੁੱਛ ਸਕਦੇ ਹੋ।";
        subtext.textContent = "ਬੋਲ ਕੇ • ਲਿਖ ਕੇ • ਫ਼ੋਟੋ ਰਾਹੀਂ ਖੇਤੀ ਸਲਾਹ ਪ੍ਰਾਪਤ ਕਰੋ";
    } else if (lang === "Malayalam") {
        welcome.innerHTML = "നമസ്കാരം! ഞാൻ നിങ്ങളുടെ <strong>കിസാൻ AI (Kisan AI)</strong> കാർഷിക ഉപദേശകനാണ്. വിളകൾ, കീടങ്ങൾ, വളം, കാലാവസ്ഥ, സർക്കാർ പദ്ധതികൾ എന്നിവയെക്കുറിച്ച് സംസാരിച്ചോ എഴുതിയോ ചോദിക്കാം.";
        subtext.textContent = "വോയ്സ് • ടെക്സ്റ്റ് • ഫോട്ടോ വഴി കാർഷിക ഉപദേശം";
    } else {
        welcome.innerHTML = "Hello! I am your <strong>Kisan AI</strong> agricultural advisor. Ask me anything about your crops, pest management, fertilizers, weather suitability, government schemes, and farmer helplines using Text, Voice, or Image upload.";
        subtext.textContent = "Voice • Text • Image in your preferred language";
    }
}

// ------------------------------------------------------------------------------
// LIVE WEATHER INTEGRATION
// ------------------------------------------------------------------------------
function initializeWeather() {
    const btnDetect = document.getElementById("btnDetectLocation");
    const btnFetch = document.getElementById("btnFetchWeather");
    const searchInput = document.getElementById("weatherSearchInput");

    btnDetect.addEventListener("click", detectGPSLocation);
    btnFetch.addEventListener("click", function () {
        const query = searchInput.value.trim();
        if (query) {
            fetchLiveWeather(query);
        }
    });

    searchInput.addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            const query = searchInput.value.trim();
            if (query) fetchLiveWeather(query);
        }
    });

    // Quick district chips
    document.querySelectorAll(".loc-chip").forEach(chip => {
        chip.addEventListener("click", function () {
            const loc = this.getAttribute("data-loc");
            if (loc) {
                searchInput.value = loc;
                fetchLiveWeather(loc);
            }
        });
    });

    // Auto-detect location on startup
    detectGPSLocation();
}

function detectGPSLocation() {
    const statusDisp = document.getElementById("weatherLocationDisplay");
    const searchInput = document.getElementById("weatherSearchInput");

    statusDisp.textContent = "📍 Detecting your live location...";

    // 1. Try Browser Geolocation first
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (pos) {
                const lat = pos.coords.latitude.toFixed(4);
                const lon = pos.coords.longitude.toFixed(4);
                currentDetectedLocation = `${lat}, ${lon}`;
                statusDisp.textContent = `📍 Locating (${lat}, ${lon})...`;
                fetchLiveWeather(currentDetectedLocation);
            },
            function (err) {
                console.warn("Browser GPS unavailable or permission denied, falling back to auto IP location:", err);
                fallbackAutoLocation();
            },
            { enableHighAccuracy: true, timeout: 5000, maximumAge: 30000 }
        );
    } else {
        fallbackAutoLocation();
    }
}

async function fallbackAutoLocation() {
    const statusDisp = document.getElementById("weatherLocationDisplay");
    const searchInput = document.getElementById("weatherSearchInput");

    statusDisp.textContent = "📍 Detecting region via Network...";
    try {
        const res = await fetch(`${API_BASE}/location/auto`);
        if (res.ok) {
            const data = await res.json();
            const locName = data.location || "Guntur, Andhra Pradesh";
            currentDetectedLocation = locName;
            searchInput.value = locName;
            fetchLiveWeather(locName);
            return;
        }
    } catch (e) {
        console.warn("Backend auto-location error:", e);
    }

    // Default agricultural district fallback
    currentDetectedLocation = "Guntur, Andhra Pradesh";
    searchInput.value = currentDetectedLocation;
    fetchLiveWeather(currentDetectedLocation);
}

async function fetchLiveWeather(locationQuery) {
    const statusDisp = document.getElementById("weatherLocationDisplay");
    const searchInput = document.getElementById("weatherSearchInput");
    const dispTemp = document.getElementById("dispTemp");
    const dispCondition = document.getElementById("dispCondition");
    const dispHumidity = document.getElementById("dispHumidity");
    const dispFeelsLike = document.getElementById("dispFeelsLike");
    const dispRainProb = document.getElementById("dispRainProb");
    const dispPrecip = document.getElementById("dispPrecip");
    const dispWind = document.getElementById("dispWind");
    const dispWindDir = document.getElementById("dispWindDir");
    const advText = document.getElementById("weatherAdvisoryText");

    try {
        statusDisp.textContent = `Fetching live weather for ${locationQuery}...`;
        const res = await fetch(`${API_BASE}/weather?location=${encodeURIComponent(locationQuery)}`);
        if (!res.ok) throw new Error("Weather API request failed");

        const data = await res.json();
        currentDetectedLocation = data.location || locationQuery;

        // Update search input to human-readable place name
        if (searchInput && data.location) {
            searchInput.value = data.location;
        }

        statusDisp.textContent = `📍 ${data.location}`;
        dispTemp.textContent = `${data.temperature_c} °C`;
        dispCondition.textContent = data.condition;
        dispHumidity.textContent = `${data.humidity_pct} %`;
        dispFeelsLike.textContent = `Feels like ${data.feels_like_c}°C`;
        dispRainProb.textContent = `${data.rain_probability_pct} %`;
        dispPrecip.textContent = `${data.precipitation_mm} mm rain`;
        dispWind.textContent = `${data.wind_speed_kmh} km/h`;
        dispWindDir.textContent = `Wind Dir: ${data.wind_direction_deg}°`;

        const adv = data.agricultural_advisory || {};
        let advisoryHTML = `<strong>Spraying:</strong> ${adv.spraying_advice || 'Check sky conditions.'}<br><strong>Irrigation:</strong> ${adv.irrigation_advice || 'Normal.'}`;
        if (adv.disease_risk_warnings && adv.disease_risk_warnings.length > 0) {
            advisoryHTML += `<br><strong>⚠️ Disease Warning:</strong> ${adv.disease_risk_warnings.join(' ')}`;
        }
        advText.innerHTML = advisoryHTML;

    } catch (err) {
        console.warn("Weather fetch error:", err);
        statusDisp.textContent = `📍 ${locationQuery} (Offline Weather Mode)`;
        dispTemp.textContent = "28.0 °C";
        dispCondition.textContent = "Partly Cloudy";
        dispHumidity.textContent = "65 %";
        dispRainProb.textContent = "20 %";
        dispWind.textContent = "10 km/h";
        advText.innerHTML = "Live weather API unavailable. Standard advice: Check local field moisture before irrigation and avoid spraying in strong winds.";
    }
}

// ------------------------------------------------------------------------------
// VOICE INPUT (SPEECH-TO-TEXT)
// ------------------------------------------------------------------------------
function initializeSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const btnVoice = document.getElementById("btnVoiceDock");
    const recordingBar = document.getElementById("voiceRecordingBar");
    const btnStopVoice = document.getElementById("btnStopVoice");
    const voiceText = document.getElementById("voiceListeningText");
    const textInput = document.getElementById("chatTextInput");

    if (!SpeechRecognition) {
        btnVoice.title = "Voice recognition not supported in this browser. Please use Google Chrome.";
        btnVoice.style.opacity = "0.5";
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = function () {
        isListeningSpeech = true;
        btnVoice.style.background = "#ff4d4d";
        recordingBar.style.display = "flex";
        voiceText.textContent = `🎙️ Listening in ${currentSelectedLanguage}... Speak your farming problem.`;
    };

    recognition.onresult = function (event) {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        textInput.value = transcript.trim();
    };

    recognition.onerror = function (event) {
        console.error("Speech Recognition Error:", event.error);
        voiceText.textContent = `⚠️ Voice error: ${event.error}. Please try again or type your question.`;
        setTimeout(stopSpeechRecognition, 2500);
    };

    recognition.onend = function () {
        stopSpeechRecognition();
        // If user spoke something non-empty, prompt user or auto-focus
        if (textInput.value.trim()) {
            textInput.focus();
        }
    };

    btnVoice.addEventListener("click", function () {
        if (isListeningSpeech) {
            recognition.stop();
        } else {
            const speechCode = SPEECH_LANG_CODES[currentSelectedLanguage] || "en-IN";
            recognition.lang = speechCode;
            try {
                recognition.start();
            } catch (e) {
                console.error("Could not start speech recognition:", e);
            }
        }
    });

    btnStopVoice.addEventListener("click", function () {
        if (recognition) recognition.stop();
    });
}

function stopSpeechRecognition() {
    isListeningSpeech = false;
    const btnVoice = document.getElementById("btnVoiceDock");
    const recordingBar = document.getElementById("voiceRecordingBar");
    if (btnVoice) btnVoice.style.background = "#143520";
    if (recordingBar) recordingBar.style.display = "none";
}

// ------------------------------------------------------------------------------
// VOICE OUTPUT (TEXT-TO-SPEECH)
// ------------------------------------------------------------------------------

// TTS Language codes for voice output (same map as speech recognition)
const TTS_LANG_CODES = {
    "English": "en-IN",
    "Telugu": "te-IN",
    "Hindi": "hi-IN",
    "Tamil": "ta-IN",
    "Kannada": "kn-IN",
    "Malayalam": "ml-IN",
    "Marathi": "mr-IN",
    "Bengali": "bn-IN",
    "Gujarati": "gu-IN",
    "Punjabi": "pa-IN"
};

// Track which button is currently active for speech
let _activeSpeakBtn = null;
let _activeSpeakUtterance = null;
let _backendAudioEl = null;

/**
 * Clean text for TTS — remove all markdown, symbols, emojis, URLs, table
 * separators, HTML tags, code blocks, and other non-speech content.
 * ONLY used for voice output — the displayed text is NOT modified.
 */
function cleanTextForTTS(rawText) {
    if (!rawText) return "";

    let t = rawText;

    // 0. Handle object or JSON string input (extract user-facing text only)
    if (typeof t === "object" && t !== null) {
        t = t.answer || t.advisory || t.text || t.message || t.response || "";
    } else if (typeof t === "string") {
        const trimmed = t.trim();
        if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
            try {
                const parsed = JSON.parse(trimmed);
                if (typeof parsed === "object" && parsed !== null) {
                    t = parsed.answer || parsed.advisory || parsed.text || parsed.message || parsed.response || trimmed;
                }
            } catch (e) {
                // Not valid JSON, proceed with string
            }
        }
    }

    if (typeof t !== "string") {
        t = String(t || "");
    }

    // 1. Decode HTML entities (data-text stores escaped HTML, e.g. &quot; &#039; &amp;)
    t = t.replace(/&quot;/g, '"')
          .replace(/&#039;/g, "'")
          .replace(/&amp;/g, "&")
          .replace(/&lt;/g, "<")
          .replace(/&gt;/g, ">")
          .replace(/&nbsp;/g, " ")
          .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)));

    // 2. Strip HTML tags
    t = t.replace(/<[^>]+>/g, " ");

    // 3. Strip URLs, file paths, IP addresses
    t = t.replace(/https?:\/\/\S+/gi, " ");
    t = t.replace(/file:\/\/\S+/gi, " ");
    t = t.replace(/\b[A-Za-z]:\\[\w\\.-]+/g, " ");
    t = t.replace(/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?\b/g, " ");

    // 4. Strip internal JSON keys, metadata, and variables
    t = t.replace(/"?(?:answer|advisory|session_id|weather_summary|confidence_score|crop_detected|observed_symptoms|recommended_actions|possible_issue|mode|language|location)"?\s*:\s*/gi, " ");
    t = t.replace(/\b(?:VERIFIED AGRICULTURAL ADVISOR|AI GENERATED|IMAGE DIAGNOSIS|OFFLINE ADVISORY|OFFLINE MODE|Listen Aloud|Stop Speaking|Copy Advisory|Copy Text)\b/gi, " ");
    t = t.replace(/\[(?:TTS|TTS Backend|DEBUG|INFO|ERROR|WARN|LOG)[^\]]*\]/gi, " ");
    t = t.replace(/\b(?:console\.(?:log|warn|error|info)|session-[a-z0-9]+)\b/gi, " ");

    // 5. Strip markdown code fences and inline code
    t = t.replace(/```[\s\S]*?```/g, " ");
    t = t.replace(/`[^`]*`/g, " ");

    // 6. Strip markdown headings (# Heading)
    t = t.replace(/^#{1,6}\s+/gm, "");

    // 7. Convert markdown bold/italic markers — extract content
    //    e.g. **Word** → Word, *Word* → Word, __Word__ → Word, _Word_ → Word
    t = t.replace(/\*\*\*([^*]+)\*\*\*/g, "$1");
    t = t.replace(/\*\*([^*]+)\*\*/g, "$1");
    t = t.replace(/\*([^*]+)\*/g, "$1");
    t = t.replace(/__([^_]+)__/g, "$1");
    t = t.replace(/_([^_]+)_/g, "$1");

    // 8. Strip table separator rows (|---|---|) and pipe delimiters
    t = t.replace(/\|[\s\-:]+\|[\s\-|:]+/g, " ");
    t = t.replace(/\|/g, " ");

    // 9. Strip bullet/list markers at line start
    t = t.replace(/^[\s]*[-*•·]\s+/gm, "");
    t = t.replace(/^\s*\d+\.\s+/gm, "");

    // 10. Strip emojis (Unicode emoji property and Unicode ranges fallback)
    try {
        t = t.replace(/\p{Extended_Pictographic}/gu, "");
        t = t.replace(/\p{Emoji}/gu, "");
    } catch (e) {
        t = t.replace(/[\u{1F000}-\u{1FFFF}\u{2600}-\u{27BF}\u{FE00}-\u{FEFF}\u{1F300}-\u{1F9FF}\u{1FA00}-\u{1FA9F}]/gu, "");
    }

    // 11. Strip remaining special symbols, brackets, braces, quotes, slashes, repeated dashes
    t = t.replace(/[\\#~=`^<>{}[\]%$@*_+]/g, " ");
    t = t.replace(/["']/g, "");
    t = t.replace(/[-=_]{2,}/g, " ");

    // 12. Collapse multiple whitespace / newlines into natural pauses
    t = t.replace(/\r?\n+/g, ". ");
    t = t.replace(/\.{2,}/g, ".");
    t = t.replace(/\s{2,}/g, " ");
    t = t.trim();

    return t;
}

/**
 * Reset the given speak button back to its default "Listen Aloud" state.
 */
function _resetSpeakButton(btn) {
    if (!btn) return;
    btn.textContent = "🔊 Listen Aloud";
    btn.title = "Listen Aloud";
}

/**
 * Stop all active TTS (browser + backend audio) and reset the active button.
 */
function stopAllTTS() {
    // Stop browser SpeechSynthesis
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }
    // Stop backend audio element safely without triggering error fallback
    if (_backendAudioEl) {
        _backendAudioEl.onended = null;
        _backendAudioEl.onerror = null;
        _backendAudioEl.pause();
        _backendAudioEl.src = "";
    }
    _resetSpeakButton(_activeSpeakBtn);
    _activeSpeakBtn = null;
    _activeSpeakUtterance = null;
}

/**
 * Main TTS entry point. Called by the Listen Aloud button click handler.
 * Handles toggle (start / stop), single-active enforcement, language, and clean text.
 */
function speakTextAloud(text, language, triggerBtn) {
    if (!text || !text.trim()) return;

    // If this button is already the active speaker → STOP
    if (_activeSpeakBtn && _activeSpeakBtn === triggerBtn) {
        stopAllTTS();
        return;
    }

    // Stop any other currently active speech first
    stopAllTTS();

    // Mark this button as active
    _activeSpeakBtn = triggerBtn || null;
    if (_activeSpeakBtn) {
        _activeSpeakBtn.textContent = "⏹️ Stop Speaking";
        _activeSpeakBtn.title = "Stop Speaking";
    }

    const cleanText = cleanTextForTTS(text);
    if (!cleanText) {
        _resetSpeakButton(_activeSpeakBtn);
        _activeSpeakBtn = null;
        return;
    }

    const speechCode = TTS_LANG_CODES[language] || "en-IN";
    console.log("[TTS] Speaking language:", language, "| code:", speechCode);
    console.log("[TTS] Clean text preview:", cleanText.substring(0, 120));

    // Snapshot the active button at this moment (avoids stale closure)
    const activeBtn = _activeSpeakBtn;

    function onSpeechEnd() {
        if (_activeSpeakBtn === activeBtn) {
            _resetSpeakButton(_activeSpeakBtn);
            _activeSpeakBtn = null;
            _activeSpeakUtterance = null;
        }
    }

    // Try backend TTS FIRST (gTTS is language-accurate).
    // Only fall back to browser SpeechSynthesis if backend fails.
    streamAudioFromBackend(cleanText, language, onSpeechEnd, function fallbackToBrowser() {
        console.warn("[TTS] Backend failed — falling back to browser SpeechSynthesis");
        _useBrowserTTS(cleanText, speechCode, onSpeechEnd);
    });
}

/**
 * Use browser SpeechSynthesis. Voice selection waits for voices to load
 * (single attempt — no duplicate-fire race condition).
 */
function _useBrowserTTS(cleanText, speechCode, onSpeechEnd) {
    if (!('speechSynthesis' in window)) {
        console.warn("[TTS] Browser SpeechSynthesis not available.");
        if (onSpeechEnd) onSpeechEnd();
        return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = speechCode;
    utterance.rate = 0.92;

    utterance.onend = onSpeechEnd;
    utterance.onerror = function (e) {
        console.warn("[TTS] Browser SpeechSynthesis error:", e.error);
        if (onSpeechEnd) onSpeechEnd();
    };

    let hasSpoken = false;
    function doSpeak() {
        if (hasSpoken) return;
        hasSpoken = true;

        const voices = window.speechSynthesis.getVoices();
        console.log("[TTS] Available voices count:", voices.length);

        // Try exact match first (e.g. "te-IN"), then language prefix (e.g. "te")
        const langPrefix = speechCode.split("-")[0];
        let chosen = voices.find(v => v.lang === speechCode);
        if (!chosen) chosen = voices.find(v => v.lang.startsWith(langPrefix));
        if (chosen) {
            console.log("[TTS] Selected voice:", chosen.name, chosen.lang);
            utterance.voice = chosen;
        } else {
            console.warn("[TTS] No matching voice for", speechCode, "— letting browser pick");
            // Do NOT set utterance.voice; let the browser use its lang= setting
        }

        _activeSpeakUtterance = utterance;
        window.speechSynthesis.speak(utterance);
    }

    const voices = window.speechSynthesis.getVoices();
    if (voices && voices.length > 0) {
        doSpeak();
    } else {
        // Voices not loaded yet — use onvoiceschanged ONCE
        window.speechSynthesis.onvoiceschanged = function () {
            window.speechSynthesis.onvoiceschanged = null;
            doSpeak();
        };
        // Fallback in case onvoiceschanged does not fire
        setTimeout(function () {
            if (!hasSpoken) {
                doSpeak();
            }
        }, 200);
    }
}

async function streamAudioFromBackend(text, language, onEndCallback, onFailCallback) {
    try {
        const audioEl = document.getElementById("ttsAudioPlayer");
        _backendAudioEl = audioEl;

        // Pause and clean up any previous handlers safely
        audioEl.onended = null;
        audioEl.onerror = null;
        audioEl.pause();
        audioEl.src = "";

        console.log("[TTS Backend] Requesting /voice/speak — lang:", language, "| chars:", text.length);

        const res = await fetch(`${API_BASE}/voice/speak`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text, language: language })
        });

        console.log("[TTS Backend] HTTP status:", res.status, "| Content-Type:", res.headers.get("content-type"));

        if (!res.ok) {
            console.error("[TTS Backend] Non-OK response:", res.status);
            _backendAudioEl = null;
            if (onFailCallback) onFailCallback();
            return;
        }

        const contentType = res.headers.get("content-type") || "";
        if (!contentType.includes("audio")) {
            // Backend returned something that isn't audio (e.g. JSON error)
            const errText = await res.text();
            console.error("[TTS Backend] Expected audio, got:", contentType, "| body:", errText.substring(0, 200));
            _backendAudioEl = null;
            if (onFailCallback) onFailCallback();
            return;
        }

        const blob = await res.blob();
        console.log("[TTS Backend] Audio blob size:", blob.size, "bytes | type:", blob.type);

        if (blob.size < 100) {
            // Suspiciously small — treat as failure
            console.error("[TTS Backend] Audio blob too small, likely an error response.");
            _backendAudioEl = null;
            if (onFailCallback) onFailCallback();
            return;
        }

        const audioUrl = URL.createObjectURL(blob);
        audioEl.src = audioUrl;

        audioEl.onended = function () {
            console.log("[TTS Backend] Audio playback ended.");
            audioEl.onended = null;
            audioEl.onerror = null;
            URL.revokeObjectURL(audioUrl);
            _backendAudioEl = null;
            if (onEndCallback) onEndCallback();
        };
        audioEl.onerror = function (e) {
            console.error("[TTS Backend] Audio element error during playback:", e);
            audioEl.onended = null;
            audioEl.onerror = null;
            URL.revokeObjectURL(audioUrl);
            _backendAudioEl = null;
            // Playback failed — fall back to browser
            if (onFailCallback) onFailCallback();
        };

        const playPromise = audioEl.play();
        if (playPromise !== undefined) {
            playPromise.then(() => {
                console.log("[TTS Backend] audio.play() started successfully.");
            }).catch(function (playErr) {
                console.error("[TTS Backend] audio.play() rejected:", playErr);
                audioEl.onended = null;
                audioEl.onerror = null;
                URL.revokeObjectURL(audioUrl);
                _backendAudioEl = null;
                if (onFailCallback) onFailCallback();
            });
        }

    } catch (e) {
        console.error("[TTS Backend] Fetch/network error:", e);
        _backendAudioEl = null;
        if (onFailCallback) onFailCallback();
    }
}

// ------------------------------------------------------------------------------
// CHAT CONVERSATION & API CLIENT
// ------------------------------------------------------------------------------
function initializeChatEvents() {
    const btnSend = document.getElementById("btnSendMessage");
    const textInput = document.getElementById("chatTextInput");
    const btnClear = document.getElementById("btnClearChat");

    btnSend.addEventListener("click", sendChatMessage);
    textInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    btnClear.addEventListener("click", function () {
        sessionId = "session-" + Math.random().toString(36).substring(2, 9);
        const messageStream = document.getElementById("messageStream");
        messageStream.innerHTML = "";
        // Re-inject welcome message
        const welcomeRow = document.createElement("div");
        welcomeRow.className = "message-row ai-row";
        welcomeRow.innerHTML = `
            <div class="avatar-bubble">🌾</div>
            <div class="message-bubble ai-bubble">
                <div class="bubble-header">
                    <span class="sender-name">Kisan AI Advisory</span>
                    <span class="badge-mode">VERIFIED AGRICULTURAL ADVISOR</span>
                </div>
                <div class="bubble-content" id="welcomeMessageContent">
                    New chat started. Ask your question in ${currentSelectedLanguage}.
                </div>
            </div>
        `;
        messageStream.appendChild(welcomeRow);
        updateWelcomeMessage(currentSelectedLanguage);
    });

    // Quick Prompts chips (Delegated click handler ensures prompt is sent exactly once)
    const promptsContainer = document.querySelector(".prompts-scroll");
    if (promptsContainer) {
        promptsContainer.addEventListener("click", function (e) {
            const chip = e.target.closest(".prompt-chip");
            if (!chip) return;
            const promptText = chip.getAttribute("data-prompt");
            const action = chip.getAttribute("data-action");
            if (action === "open-scanner") {
                openModal("imageModal");
            } else if (promptText) {
                textInput.value = promptText;
                sendChatMessage();
            }
        });
    }

    // Delegated actions for Listen / Copy buttons (used by both Online and Offline modes)
    document.getElementById("messageStream").addEventListener("click", function (e) {
        const speakBtn = e.target.closest(".btn-speak");
        const copyBtn = e.target.closest(".btn-copy");
        if (speakBtn) {
            const bubble = speakBtn.closest(".message-bubble");
            const bubbleText = bubble ? bubble.querySelector(".bubble-content").innerText : "";
            const text = speakBtn.getAttribute("data-text") || bubbleText;
            speakTextAloud(text, currentSelectedLanguage, speakBtn);
        } else if (copyBtn) {
            const bubble = copyBtn.closest(".message-bubble");
            const content = bubble ? bubble.querySelector(".bubble-content").innerText : "";
            navigator.clipboard.writeText(content).then(() => {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = "✅ Copied!";
                setTimeout(() => { copyBtn.textContent = originalText; }, 2000);
            });
        }
    });
}

async function sendChatMessage() {
    const textInput = document.getElementById("chatTextInput");
    const question = textInput.value.trim();
    if (!question) return;

    // 1. Append User Message to Stream
    appendMessageToStream("user", question, "Farmer");
    textInput.value = "";
    textInput.focus();

    // 2. Show Typing Indicator
    const typingInd = document.getElementById("typingIndicator");
    typingInd.style.display = "flex";
    scrollToBottom();

    // 3. Send to Backend
    try {
        const payload = {
            question: question,
            language: currentSelectedLanguage,
            location: currentDetectedLocation,
            session_id: sessionId
        };

        const res = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error(`Server returned HTTP ${res.status}`);

        const data = await res.json();
        typingInd.style.display = "none";

        // Append AI response
        appendMessageToStream("ai", data.answer, "Kisan AI Advisory", data.mode || "AI GENERATED");

        // Automatically speak response if voice was used or user preferred
        // speakTextAloud(data.answer, currentSelectedLanguage);

    } catch (err) {
        console.warn("Backend chat failed, switching to client offline fallback:", err);
        typingInd.style.display = "none";

        const offlineAnswer = getClientOfflineAdvice(question, currentSelectedLanguage);
        appendMessageToStream("ai", offlineAnswer, "Kisan AI (Offline Mode)", "OFFLINE ADVISORY");

        document.getElementById("connectionStatus").textContent = "OFFLINE MODE";
    }
}

function appendMessageToStream(sender, text, senderLabel, modeBadge = "") {
    const messageStream = document.getElementById("messageStream");
    const row = document.createElement("div");
    row.className = `message-row ${sender === "user" ? "user-row" : "ai-row"}`;

    const avatarIcon = sender === "user" ? "👨‍🌾" : "🌾";

    let badgeHTML = modeBadge ? `<span class="badge-mode">${modeBadge}</span>` : "";

    let actionsHTML = "";
    if (sender === "ai") {
        actionsHTML = `
            <div class="bubble-actions">
                <button type="button" class="btn-bubble-action btn-speak" data-text="${escapeHtml(text)}" title="Listen Aloud">🔊 Listen Aloud</button>
                <button type="button" class="btn-bubble-action btn-copy" title="Copy Advisory">📋 Copy</button>
            </div>
        `;
    }

    row.innerHTML = `
        <div class="avatar-bubble">${avatarIcon}</div>
        <div class="message-bubble ${sender === "user" ? "user-bubble" : "ai-bubble"}">
            <div class="bubble-header">
                <span class="sender-name">${senderLabel}</span>
                ${badgeHTML}
            </div>
            <div class="bubble-content">${formatMessageContent(text)}</div>
            ${actionsHTML}
        </div>
    `;

    messageStream.appendChild(row);
    scrollToBottom();
}

function formatMessageContent(rawText) {
    // Convert Markdown bold **text** to <strong>text</strong>
    let formatted = rawText.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    return formatted;
}

function escapeHtml(text) {
    return text.replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function scrollToBottom() {
    const stream = document.getElementById("messageStream");
    stream.scrollTop = stream.scrollHeight;
}

function getClientOfflineAdvice(question, language) {
    const qLower = question.toLowerCase();

    // Per-language translations of each offline knowledge topic
    const OFFLINE_ANSWERS = {
        fertilizer: {
            "Telugu": "🌾 పంట ఎరువుల నిర్వహణ:\n• ఎకరాకు సిఫారసు NPK: 40-50 కేజీ నత్రజని, 20-25 కేజీ భాస్వరం, 20-25 కేజీ పొటాష్.\n• బేసల్ డోస్: మొత్తం భాస్వరం, 50% నత్రజని మరియు 50% పొటాష్‌ను భూమి సిద్ధం చేసేటప్పుడు వేయండి.\n• టాప్ డ్రెస్సింగ్: మిగిలిన నత్రజనిని మొకాల దశలలో వేయండి.\n• జింక్ లోపాన్ని నివారించడానికి జింక్ సల్ఫేట్ 10-15 కేజీ/ఎకరా వేయండి.",
            "Hindi": "🌾 फसल उर्वरक प्रबंधन:\n• प्रति एकड़ अनुशंसित NPK: 40-50 किग्रा नाइट्रोजन, 20-25 किग्रा फास्फोरस, 20-25 किग्रा पोटाश.\n• बेसल डोज: अंतिम जुताई के समय सभी फास्फोरस, 50% नाइट्रोजन और 50% पोटाश डालें.\n• टॉप ड्रेसिंग: शेष नाइट्रोजन को कल्ले फूटने और बाली निकलने पर दो किश्तों में डालें.\n• जिंक की कमी रोकने हेतु जिंक सल्फेट 10-15 किग्रा/एकड़ डालें.",
            "Tamil": "🌾 பயிர் உர மேலாண்மை:\n• ஏக்கருக்கு பரிந்துரைக்கப்பட்ட NPK: 40-50 கிலோ நைட்ரஜன், 20-25 கிலோ பாஸ்பரஸ், 20-25 கிலோ பொட்டாஷ்.\n• அடி உரம்: இறுதி உழவின்போது அனைத்து பாஸ்பரஸ், 50% நைட்ரஜன் மற்றும் 50% பொட்டாஷ் இடவும்.\n• மேல் உரம்: மீதமுள்ள நைட்ரஜனை தனிக்கட்டு மற்றும் கதிர் தோற்றும் நிலையில் இடவும்.\n• துத்தநாக குறைபாட்டை தடுக்க ஏக்கருக்கு 10-15 கிலோ துத்தநாக சல்பேட் இடவும்.",
            "Kannada": "🌾 ಬೆಳೆ ಗೊಬ್ಬರ ನಿರ್ವಹಣೆ:\n• ಎಕರೆಗೆ ಶಿಫಾರಸು NPK: 40-50 ಕೆಜಿ ಸಾರಜನಕ, 20-25 ಕೆಜಿ ರಂಜಕ, 20-25 ಕೆಜಿ ಪೊಟ್ಯಾಷ್.\n• ತಳ ಗೊಬ್ಬರ: ಭೂಮಿ ಸಿದ್ಧಪಡಿಸುವಾಗ ಎಲ್ಲಾ ರಂಜಕ, 50% ಸಾರಜನಕ ಮತ್ತು 50% ಪೊಟ್ಯಾಷ್ ಹಾಕಿ.\n• ಮೇಲ್ ಗೊಬ್ಬರ: ಉಳಿದ ಸಾರಜನಕವನ್ನು ಸ್ತಂಭ ಮತ್ತು ತೆನೆ ಹಂತಗಳಲ್ಲಿ ನೀಡಿ.\n• ಸತುವಿನ ಕೊರತೆ ತಡೆಯಲು ಎಕರೆಗೆ 10-15 ಕೆಜಿ ಸತು ಸಲ್ಫೇಟ್ ಹಾಕಿ.",
            "default": "🌾 Crop Fertilizer Management:\n• Recommended NPK per acre: 40-50 kg Nitrogen, 20-25 kg Phosphorus, 20-25 kg Potash.\n• Basal dose: Apply all Phosphorus, 50% Nitrogen, and 50% Potash during final land preparation.\n• Top dressing: Split remaining Nitrogen at active tillering and panicle initiation stages.\n• Apply Zinc Sulphate 10-15 kg/acre to prevent zinc deficiency."
        },
        pest: {
            "Telugu": "🌾 పత్తి పురుగు నివారణ మరియు పిచికారీ సలహా:\n1. పింక్ బాల్ వర్మ్ కదలికను గమనించడానికి ఎకరాకు 5 ఫెరోమోన్ ట్రాప్‌లు పెట్టండి.\n2. ప్రారంభ దశలో 5% వేప విత్తన సారం లేదా వేప నూనె 2 మి.లీ/లీ వాడండి.\n3. పురుగు హద్దు దాటినట్లయితే: ఎమామెక్టిన్ బెంజోయేట్ 5% SG @ 80-100 గ్రా/ఎకరా వాడండి.\n⚠️ వర్షం ఉన్నప్పుడు లేదా గాలి వేగంగా ఉన్నప్పుడు పిచికారీ చేయకండి.",
            "Hindi": "🌾 कपास कीट नियंत्रण एवं छिड़काव सलाह:\n1. गुलाबी बोलवर्म की निगरानी के लिए प्रति एकड़ 5 फेरोमोन ट्रैप लगाएं.\n2. प्रारंभिक अवस्था में 5% नीम बीज अर्क या नीम तेल 2 मिली/लीटर का उपयोग करें.\n3. यदि कीट सीमा से अधिक हो: इमामेक्टिन बेंजोएट 5% SG @ 80-100 ग्राम/एकड़ का छिड़काव करें.\n⚠️ बारिश या तेज हवा में छिड़काव न करें। मास्क और दस्ताने पहनें.",
            "Tamil": "🌾 பருத்தி பூச்சி கட்டுப்பாடு மற்றும் தெளிப்பு ஆலோசனை:\n1. இளஞ்சிவப்பு காய் புழு கண்காணிப்புக்கு ஏக்கருக்கு 5 பெரோமோன் கவர்ச்சி பொறிகள் வைக்கவும்.\n2. ஆரம்ப தாக்குதலில் 5% வேப்பம் கொட்டை சாறு அல்லது வேப்பெண்ணெய் 2 மிலி/லிட்டர் தெளிக்கவும்.\n3. பூச்சி அளவு அதிகமானால்: எமாமெக்டின் பென்சோயேட் 5% SG @ 80-100 கிராம்/ஏக்கர் தெளிக்கவும்.\n⚠️ மழை அல்லது காற்று அதிகமாக இருக்கும்போது தெளிக்காதீர்கள்.",
            "Kannada": "🌾 ಹತ್ತಿ ಕೀಟ ನಿಯಂತ್ರಣ ಮತ್ತು ಸಿಂಪಡಣೆ ಸಲಹೆ:\n1. ಗುಲಾಬಿ ಕಾಯಿಕೊರಕ ಚಟುವಟಿಕೆ ಮೇಲ್ವಿಚಾರಣೆಗೆ ಎಕರೆಗೆ 5 ಫೆರೋಮೋನ್ ಬಲೆ ಇಡಿ.\n2. ಆರಂಭಿಕ ಹಂತದಲ್ಲಿ 5% ಬೇವಿನ ಬೀಜ ಸಾರ ಅಥವಾ ಬೇವಿನ ಎಣ್ಣೆ 2 ಮಿಲಿ/ಲೀ ಬಳಸಿ.\n3. ಕೀಟ ಮಿತಿ ಮೀರಿದರೆ: ಎಮಾಮೆಕ್ಟಿನ್ ಬೆಂಜೋಯೇಟ್ 5% SG @ 80-100 ಗ್ರಾಂ/ಎಕರೆ ಸಿಂಪಡಿಸಿ.\n⚠️ ಮಳೆ ಅಥವಾ ತೇವ ಗಾಳಿಯಲ್ಲಿ ಸಿಂಪಡಣೆ ಮಾಡಬೇಡಿ.",
            "default": "🌾 Cotton Pest Control & Spraying Advisory:\n1. Install pheromone traps @ 5/acre to monitor Pink Bollworm activity.\n2. Apply 5% Neem Seed Kernel Extract (NSKE) or Neem oil 2 ml/L during early infestation.\n3. If pest exceeds threshold: Emamectin Benzoate 5% SG @ 80-100 g/acre or Spinetoram in 200L water.\n⚠️ Do not spray when rain is expected or in high winds. Always wear a mask and gloves."
        },
        tomato: {
            "Telugu": "🍅 టమోటా పంట వ్యాధి సలహా:\n• ఆకులు పసుపు రంగుకు మారి గోధుమ వర్ణపు రింగులు వస్తే ఎర్లీ బ్లైట్ (Alternaria solani).\n• చర్య: సోకిన దిగువ ఆకులు తొలగించి, తడి నీరు పిచికారీ మానండి.\n• చికిత్స: మాంకోజెబ్ 75% WP @ 2గ్రా/లీ లేదా అజాక్సిస్ట్రోబిన్ + డిఫెనోకోనజోల్ @ 1 మి.లీ/లీ పిచికారీ చేయండి.\n⚠️ రక్షణ మాస్క్ మరియు గ్లవ్స్ ధరించండి.",
            "Hindi": "🍅 टमाटर फसल रोग सलाह:\n• पत्तों पर भूरे गोलाकार धब्बे हों तो यह अर्ली ब्लाइट (Alternaria solani) है.\n• क्रिया: संक्रमित नीचे की पत्तियां हटाएं, ऊपर से पानी छिड़काव बंद करें.\n• उपचार: मैंकोजेब 75% WP @ 2 ग्राम/लीटर या एजोक्सीस्ट्रोबिन + डाइफेनोकोनाजोल @ 1 मिली/लीटर छिड़कें.\n⚠️ सुरक्षात्मक मास्क और दस्ताने पहनें.",
            "Tamil": "🍅 தக்காளி பயிர் நோய் ஆலோசனை:\n• இலைகளில் பழுப்பு நிற வட்ட வடிவ புள்ளிகள் ஆர்லி ப்ளைட் (Alternaria solani) நோயை காட்டுகின்றன.\n• நடவடிக்கை: பாதிக்கப்பட்ட கீழ் இலைகளை அகற்றி, மேலே நீர் தெளிப்பை தவிர்க்கவும்.\n• சிகிச்சை: மாங்கோசெப் 75% WP @ 2 கிராம்/லிட்டர் அல்லது அசோக்சிஸ்ட்ரோபின் + டிஃபெனோகோனசோல் @ 1 மிலி/லிட்டர் தெளிக்கவும்.\n⚠️ முகமூடி மற்றும் கையுறை அணியவும்.",
            "Kannada": "🍅 ಟೊಮ್ಯಾಟೊ ಬೆಳೆ ರೋಗ ಸಲಹೆ:\n• ಎಲೆಗಳಲ್ಲಿ ಕಂದು ಗೋಲಾಕಾರ ಉಂಗುರಗಳಿದ್ದರೆ ಅದು ಎರ್ಲಿ ಬ್ಲೈಟ್ (Alternaria solani).\n• ಕ್ರಮ: ಸೋಂಕಿತ ಕೆಳ ಎಲೆಗಳನ್ನು ತೆಗೆದು, ತಲೆಯ ಮೇಲಿನ ನೀರಾವರಿ ಬಿಡಿ.\n• ಚಿಕಿತ್ಸೆ: ಮಾಂಕೋಜೆಬ್ 75% WP @ 2 ಗ್ರಾಂ/ಲೀ ಅಥವಾ ಅಜಾಕ್ಸಿಸ್ಟ್ರೋಬಿನ್ + ಡಿಫೆನೋಕೋನಜೋಲ್ @ 1 ಮಿಲಿ/ಲೀ ಸಿಂಪಡಿಸಿ.\n⚠️ ಮಾಸ್ಕ್ ಮತ್ತು ಕೈಚೀಲ ತೊಡಿ.",
            "default": "🍅 Tomato Crop Disease Advisory:\n• Leaf yellowing with brown concentric rings indicates Early Blight (Alternaria solani).\n• Recommended Action: Remove infected bottom foliage, avoid overhead sprinkler watering, and maintain airflow.\n• Safe Treatment: Spray Mancozeb 75% WP @ 2g/L or Azoxystrobin + Difenoconazole @ 1ml/L.\n⚠️ Wear protective mask and gloves. Respect 5-day pre-harvest interval."
        },
        scheme: {
            "Telugu": "🏛️ రైతులకు ప్రధాన ప్రభుత్వ పథకాలు:\n1. PM-KISAN: సంవత్సరానికి ₹6,000 నేరుగా 3 వాయిదాలలో.\n2. PMFBY (పంట బీమా): తక్కువ ప్రీమియంతో పంట నష్టానికి భీమా (హెల్ప్‌లైన్: 14447).\n3. కిసాన్ క్రెడిట్ కార్డ్ (KCC): 4% వడ్డీకి ₹3 లక్షల వరకు రుణం.\n📞 కిసాన్ కాల్ సెంటర్‌కు 1800-180-1551 కి ఉచితంగా కాల్ చేయండి.",
            "Hindi": "🏛️ किसानों के लिए प्रमुख सरकारी योजनाएं:\n1. PM-KISAN: ₹6,000/वर्ष सीधे 3 किश्तों में.\n2. PMFBY (फसल बीमा): कम प्रीमियम पर फसल नुकसान का बीमा (हेल्पलाइन: 14447).\n3. किसान क्रेडिट कार्ड (KCC): 4% ब्याज पर ₹3 लाख तक कृषि ऋण.\n📞 किसान कॉल सेंटर पर 1800-180-1551 (टोल-फ्री) पर कॉल करें.",
            "Tamil": "🏛️ விவசாயிகளுக்கான முக்கிய அரசு திட்டங்கள்:\n1. PM-KISAN: ஆண்டுக்கு ₹6,000 நேரடியாக 3 தவணைகளில்.\n2. PMFBY (பயிர் காப்பீடு): குறைந்த பிரீமியத்தில் பயிர் இழப்பு காப்பீடு (உதவி எண்: 14447).\n3. கிசான் கிரெடிட் கார்டு (KCC): 4% வட்டியில் ₹3 லட்சம் வரை கடன்.\n📞 கிசான் கால் சென்டர் 1800-180-1551 (இலவசம்) எண்ணை அழைக்கவும்.",
            "Kannada": "🏛️ ರೈತರಿಗಾಗಿ ಪ್ರಮುಖ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು:\n1. PM-KISAN: ₹6,000/ವರ್ಷ ನೇರವಾಗಿ 3 ಕಂತುಗಳಲ್ಲಿ.\n2. PMFBY (ಬೆಳೆ ವಿಮೆ): ಕಡಿಮೆ ಪ್ರೀಮಿಯಂನಲ್ಲಿ ಬೆಳೆ ನಷ್ಟ ಭರಿಸುವ ವಿಮೆ (ಸಹಾಯವಾಣಿ: 14447).\n3. ಕಿಸಾನ್ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ (KCC): 4% ಬಡ್ಡಿಗೆ ₹3 ಲಕ್ಷದವರೆಗೆ ಸಾಲ.\n📞 ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ 1800-180-1551 (ಟೋಲ್-ಫ್ರೀ) ಗೆ ಕರೆ ಮಾಡಿ.",
            "default": "🏛️ Major Government Schemes for Farmers:\n1. PM-KISAN: ₹6,000/year direct financial support in 3 equal installments.\n2. PMFBY (Crop Insurance): High-subsidy crop loss coverage (Helpline: 14447).\n3. Kisan Credit Card (KCC): Subsidized farm credit up to ₹3 Lakhs at 4% interest.\n📞 Contact Kisan Call Centre toll-free at 1800-180-1551 for application support."
        },
        helpline: {
            "Telugu": "📞 అధికారిక రైతు హెల్ప్‌లైన్‌లు:\n• కిసాన్ కాల్ సెంటర్ (KCC): 1800-180-1551 (ఉచితం, ఉదయం 6 నుండి రాత్రి 10 వరకు, అన్ని భాషలలో)\n• PMFBY పంట బీమా హెల్ప్‌లైన్: 14447 (24x7)\n• PM-KISAN హెల్ప్‌డెస్క్: 155261 / 011-24300606",
            "Hindi": "📞 आधिकारिक किसान हेल्पलाइन:\n• किसान कॉल सेंटर (KCC): 1800-180-1551 (टोल-फ्री, सुबह 6 से रात 10 बजे, सभी भाषाओं में)\n• PMFBY फसल बीमा हेल्पलाइन: 14447 (24x7)\n• PM-KISAN हेल्पडेस्क: 155261 / 011-24300606",
            "Tamil": "📞 அதிகாரப்பூர்வ விவசாய உதவி எண்கள்:\n• கிசான் கால் சென்டர் (KCC): 1800-180-1551 (இலவசம், காலை 6 முதல் இரவு 10 வரை, அனைத்து மொழிகளிலும்)\n• PMFBY பயிர் காப்பீடு உதவி எண்: 14447 (24x7)\n• PM-KISAN உதவி மேசை: 155261 / 011-24300606",
            "Kannada": "📞 ಅಧಿಕೃತ ರೈತ ಸಹಾಯವಾಣಿಗಳು:\n• ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ (KCC): 1800-180-1551 (ಟೋಲ್-ಫ್ರೀ, ಬೆಳಿಗ್ಗೆ 6 ರಿಂದ ರಾತ್ರಿ 10, ಎಲ್ಲಾ ಭಾಷೆಗಳಲ್ಲಿ)\n• PMFBY ಬೆಳೆ ವಿಮೆ ಸಹಾಯವಾಣಿ: 14447 (24x7)\n• PM-KISAN ಹೆಲ್ಪ್‌ಡೆಸ್ಕ್: 155261 / 011-24300606",
            "default": "📞 Official Farmer Helplines:\n• Kisan Call Centre (KCC): 1800-180-1551 (Toll-Free, 6:00 AM to 10:00 PM, all Indian languages)\n• PMFBY Crop Insurance Helpline: 14447 (24x7)\n• PM-KISAN Helpdesk: 155261 / 011-24300606"
        }
    };

    // Helper to pick the right language translation (falls back to "default")
    function pickLang(topic) {
        return OFFLINE_ANSWERS[topic][language] || OFFLINE_ANSWERS[topic]["default"];
    }

    // Match keywords and return a language-appropriate response
    const fertKeywords = ["వరి", "rice", "paddy", "ఎరువు", "fertilizer", "dap", "urea", "खाद", "உரம்", "ಗೊಬ್ಬರ", "সার"];
    const pestKeywords = ["పత్తి", "cotton", "పురుగు", "pest", "పిచికారీ", "spray", "कीट", "छिड़काव", "பூச்சி", "ಕೀಟ"];
    const tomatoKeywords = ["tomato", "టమోటా", "yellow", "blight", "spot", "ఆకుమచ్చ", "टमाटर", "पीला", "धब्बा", "இலை"];
    const schemeKeywords = ["scheme", "పథకం", "pm-kisan", "pmfby", "యోజన", "योजना", "திட்டம்", "ಯೋಜನೆ", "প্রকল্প"];
    const helplineKeywords = ["helpline", "నంబర్", "హెల్ప్‌లైన్", "contact", "phone", "number", "नंबर", "உதவி", "ಸಹಾಯವಾಣಿ"];

    if (fertKeywords.some(k => qLower.includes(k.toLowerCase()))) return pickLang("fertilizer");
    if (pestKeywords.some(k => qLower.includes(k.toLowerCase()))) return pickLang("pest");
    if (tomatoKeywords.some(k => qLower.includes(k.toLowerCase()))) return pickLang("tomato");
    if (schemeKeywords.some(k => qLower.includes(k.toLowerCase()))) return pickLang("scheme");
    if (helplineKeywords.some(k => qLower.includes(k.toLowerCase()))) return pickLang("helpline");

    // Generic fallback — all supported languages
    const genericFallback = {
        "Telugu": "🟢 ఆఫ్‌లైన్ సలహా: పంటను క్రమం తప్పకుండా పరిశీలించండి, నేల తేమను బట్టి మాత్రమే నీరు పెట్టండి మరియు తగినంత వేప నూనెను ముందస్తుగా వాడండి. వివరణాత్మక సలహా కోసం కిసాన్ కాల్ సెంటర్ 1800-180-1551 ను సంప్రదించండి.",
        "Hindi": "🟢 ऑफलाइन सलाह: फसल का नियमित निरीक्षण करें, केवल जरूरत पड़ने पर ही सिंचाई करें और संतुलित खाद डालें। सहायता के लिए किसान कॉल सेंटर 1800-180-1551 पर कॉल करें।",
        "Tamil": "🟢 ஆஃப்லைன் ஆலோசனை: பயிரை தொடர்ந்து கவனியுங்கள், மண் ஈரப்பதத்தை பொறுத்து மட்டும் நீர் பாய்ச்சுங்கள் மற்றும் வேப்பெண்ணெய் பயன்படுத்துங்கள். விரிவான உதவிக்கு கிசான் கால் சென்டர் 1800-180-1551 அழைக்கவும்.",
        "Kannada": "🟢 ಆಫ್‌ಲೈನ್ ಸಲಹೆ: ಬೆಳೆಯನ್ನು ನಿಯಮಿತವಾಗಿ ಪರೀಕ್ಷಿಸಿ, ಮಣ್ಣಿನ ತೇವಾಂಶಕ್ಕೆ ಅನುಗುಣವಾಗಿ ನೀರು ನೀಡಿ, ಮತ್ತು ಬೇವಿನ ಎಣ್ಣೆ ಬಳಸಿ. ಹೆಚ್ಚಿನ ಸಹಾಯಕ್ಕೆ ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ 1800-180-1551 ಗೆ ಕರೆ ಮಾಡಿ.",
        "Marathi": "🟢 ऑफलाइन सल्ला: पिकाची नियमित पाहणी करा, जमिनीच्या ओलाव्यानुसारच पाणी द्या आणि कडुनिंबाचे तेल वापरा. तपशीलवार मदतीसाठी किसान कॉल सेंटर 1800-180-1551 वर संपर्क करा.",
        "Bengali": "🟢 অফলাইন পরামর্শ: নিয়মিত ফসল পরীক্ষা করুন, মাটির আর্দ্রতা অনুযায়ী সেচ দিন এবং নিম তেল ব্যবহার করুন। বিস্তারিত সাহায্যের জন্য কিসান কল সেন্টার 1800-180-1551 তে কল করুন।",
        "Gujarati": "🟢 ઑફલાઇન સલાહ: પાકનું નિયમિત નિરીક્ષણ કરો, જમીનની ભેજ જોઈને જ સિંચાઈ કરો અને લીંબોળીનું તેલ વાપરો. વધુ મદદ માટે કિસાન કૉલ સેન્ટર 1800-180-1551 ઉપર ફોન કરો.",
        "Punjabi": "🟢 ਆਫ਼ਲਾਈਨ ਸਲਾਹ: ਫ਼ਸਲ ਦੀ ਨਿਯਮਿਤ ਜਾਂਚ ਕਰੋ, ਜ਼ਮੀਨ ਦੀ ਨਮੀ ਦੇ ਆਧਾਰ 'ਤੇ ਸਿੰਚਾਈ ਕਰੋ ਅਤੇ ਨਿੰਮ ਤੇਲ ਵਰਤੋ। ਵੱਧ ਜਾਣਕਾਰੀ ਲਈ ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ 1800-180-1551 ਤੇ ਕਾਲ ਕਰੋ।",
        "Malayalam": "🟢 ഓഫ്‌ലൈൻ ഉപദേശം: വിളകൾ നിരന്തരം ശ്രദ്ധിക്കുക, മണ്ണിന്റെ ഈർപ്പമനുസരിച്ച് മാത്രം ജലസേചനം നടത്തുക, വേപ്പെണ്ണ ഉപയോഗിക്കുക. കൂടുതൽ സഹായത്തിനു കിസാൻ കോൾ സെന്റർ 1800-180-1551 ൽ വിളിക്കുക.",
        "default": "🟢 Offline Mode: Inspect your crop foliage regularly, ensure proper drainage, avoid over-fertilizing with urea, and consult your local KVK or Kisan Call Centre (1800-180-1551) for expert help."
    };

    return genericFallback[language] || genericFallback["default"];
}

// ------------------------------------------------------------------------------
// MODALS MANAGEMENT (IMAGE, SCHEMES, HELPLINES)
// ------------------------------------------------------------------------------
function initializeModals() {
    // Open Nav Buttons
    const btnWeatherNav = document.getElementById("btnOpenWeather");
    if (btnWeatherNav) {
        btnWeatherNav.addEventListener("click", () => {
            const weatherSection = document.getElementById("weatherBarSection");
            if (weatherSection) {
                weatherSection.scrollIntoView({ behavior: "smooth" });
                const searchInput = document.getElementById("weatherSearchInput");
                if (searchInput) searchInput.focus();
            }
        });
    }

    document.getElementById("btnOpenImageModal").addEventListener("click", () => openModal("imageModal"));
    document.getElementById("btnUploadImageDock").addEventListener("click", () => openModal("imageModal"));
    document.getElementById("btnOpenSchemes").addEventListener("click", () => {
        openModal("schemesModal");
        loadGovernmentSchemes();
    });
    document.getElementById("btnOpenHelplines").addEventListener("click", () => {
        openModal("helplinesModal");
        loadFarmerHelplines();
    });

    // Close Buttons
    document.getElementById("btnCloseImageModal").addEventListener("click", () => closeModal("imageModal"));
    document.getElementById("btnCloseSchemesModal").addEventListener("click", () => closeModal("schemesModal"));
    document.getElementById("btnCloseHelplinesModal").addEventListener("click", () => closeModal("helplinesModal"));

    // Close on backdrop click
    document.querySelectorAll(".modal-backdrop").forEach(backdrop => {
        backdrop.addEventListener("click", function (e) {
            if (e.target === this) {
                closeModal(this.id);
            }
        });
    });

    // Image Upload Dropzone Setup
    initializeImageDropzone();
    initializeSchemesFilter();
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("show");
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("show");
}

// ------------------------------------------------------------------------------
// IMAGE SCANNER & DIAGNOSIS
// ------------------------------------------------------------------------------
function initializeImageDropzone() {
    const dropzone = document.getElementById("imageDropzone");
    const fileInput = document.getElementById("modalFileInput");
    const btnBrowse = document.getElementById("btnBrowseFile");
    const previewContainer = document.getElementById("dropzonePreview");
    const previewImg = document.getElementById("previewImg");
    const emptyContainer = document.getElementById("dropzoneEmpty");
    const btnRemove = document.getElementById("btnRemovePreview");
    const btnAnalyze = document.getElementById("btnRunImageAnalysis");
    const resultCard = document.getElementById("diagnosticResultCard");

    btnBrowse.addEventListener("click", (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    dropzone.addEventListener("click", () => {
        if (!currentUploadedImageFile) fileInput.click();
    });

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--primary)";
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.style.borderColor = "var(--border-highlight)";
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--border-highlight)";
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleImageSelected(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", function () {
        if (this.files && this.files.length > 0) {
            handleImageSelected(this.files[0]);
        }
    });

    btnRemove.addEventListener("click", (e) => {
        e.stopPropagation();
        currentUploadedImageFile = null;
        fileInput.value = "";
        previewContainer.style.display = "none";
        emptyContainer.style.display = "block";
        resultCard.style.display = "none";
    });

    function handleImageSelected(file) {
        if (!file.type.startsWith("image/")) {
            alert("Please select a valid image file (JPEG, PNG, WebP).");
            return;
        }
        currentUploadedImageFile = file;
        const reader = new FileReader();
        reader.onload = function (e) {
            previewImg.src = e.target.result;
            emptyContainer.style.display = "none";
            previewContainer.style.display = "flex";
            resultCard.style.display = "none";
        };
        reader.readAsDataURL(file);
    }

    btnAnalyze.addEventListener("click", async function () {
        if (!currentUploadedImageFile) {
            alert("Please select or drop a crop image first.");
            return;
        }

        const userQuestion = document.getElementById("imageQuestionInput").value.trim();
        btnAnalyze.disabled = true;
        btnAnalyze.innerHTML = "<span>⏳</span> Analyzing Crop Pathology...";

        const formData = new FormData();
        formData.append("file", currentUploadedImageFile);
        formData.append("question", userQuestion);
        formData.append("language", currentSelectedLanguage);
        formData.append("location", currentDetectedLocation);
        formData.append("session_id", sessionId);

        try {
            const res = await fetch(`${API_BASE}/image/analyze`, {
                method: "POST",
                body: formData
            });

            if (!res.ok) throw new Error("Image analysis request failed");

            const data = await res.json();
            const diag = data.diagnosis || {};

            // Render result card
            document.getElementById("diagCrop").textContent = diag.crop_detected || "Crop Plant";
            document.getElementById("diagIssue").textContent = diag.possible_issue || "Symptoms Detected";
            document.getElementById("diagConfidence").textContent = `${diag.confidence_score || 80}% Confidence`;
            document.getElementById("diagSymptoms").textContent = diag.observed_symptoms || "Visual symptoms noted.";

            const actionsList = document.getElementById("diagActions");
            actionsList.innerHTML = "";
            (diag.recommended_actions || []).forEach(act => {
                const li = document.createElement("li");
                li.textContent = act;
                actionsList.appendChild(li);
            });

            resultCard.style.display = "block";

            // Store advisory to send to chat if requested
            document.getElementById("btnSendDiagnosisToChat").onclick = function () {
                closeModal("imageModal");
                appendMessageToStream("user", `📷 Uploaded crop image: "${userQuestion || 'Identify crop disease'}"`, "Farmer");
                appendMessageToStream("ai", data.advisory || `Crop Diagnosis: ${diag.possible_issue}`, "Kisan AI Advisory", "IMAGE DIAGNOSIS");
            };

        } catch (err) {
            console.error("Image analysis error:", err);
            alert("Could not complete image analysis. Falling back to chat query.");
        } finally {
            btnAnalyze.disabled = false;
            btnAnalyze.innerHTML = "<span>🔍</span> Run AI Crop Diagnosis";
        }
    });
}

// ------------------------------------------------------------------------------
// GOVERNMENT SCHEMES & HELPLINES
// ------------------------------------------------------------------------------
let cachedSchemesData = [];

async function loadGovernmentSchemes() {
    const container = document.getElementById("schemesListGrid");
    container.innerHTML = "<p>Loading verified government schemes...</p>";

    try {
        const res = await fetch(`${API_BASE}/schemes`);
        const data = await res.json();
        cachedSchemesData = data.schemes || [];
        renderSchemes(cachedSchemesData);
    } catch (e) {
        container.innerHTML = "<p>Could not connect to schemes API. Contact Kisan Call Centre (1800-180-1551) for central scheme information.</p>";
    }
}

function initializeSchemesFilter() {
    const searchInput = document.getElementById("schemesSearchInput");
    const stateSelect = document.getElementById("schemeStateSelect");

    function applyFilter() {
        const query = searchInput.value.toLowerCase();
        const selectedState = stateSelect.value.toLowerCase();

        const filtered = cachedSchemesData.filter(s => {
            const matchesQuery = !query || 
                s.scheme_name.toLowerCase().includes(query) || 
                s.description.toLowerCase().includes(query) || 
                s.benefits.toLowerCase().includes(query);
            
            const matchesState = !selectedState || 
                (s.state && s.state.toLowerCase().includes(selectedState)) || 
                (!s.state); // Central schemes apply to all states

            return matchesQuery && matchesState;
        });

        renderSchemes(filtered);
    }

    searchInput.addEventListener("input", applyFilter);
    stateSelect.addEventListener("change", applyFilter);
}

function renderSchemes(schemes) {
    const container = document.getElementById("schemesListGrid");
    if (!schemes || schemes.length === 0) {
        container.innerHTML = "<p>No matching government schemes found. Try a different search term.</p>";
        return;
    }

    container.innerHTML = schemes.map(s => `
        <div class="scheme-card">
            <span class="scheme-badge">${s.category || 'Central Scheme'}</span>
            <h4>${s.scheme_name}</h4>
            <p>${s.description}</p>
            <div class="scheme-benefits">
                <strong>🎁 Benefits:</strong> ${s.benefits}
            </div>
            <p><strong>📋 Eligibility:</strong> ${s.eligibility}</p>
            <a href="${s.official_source}" target="_blank" rel="noopener" class="scheme-link">
                🔗 Official Portal (${s.official_source.replace('https://', '')}) ➔
            </a>
        </div>
    `).join("");
}

async function loadFarmerHelplines() {
    const container = document.getElementById("helplinesListContainer");
    container.innerHTML = "<p>Loading verified helplines...</p>";

    try {
        const res = await fetch(`${API_BASE}/helplines`);
        const data = await res.json();
        const national = data.national_helplines || [];
        const stateItems = data.state_helplines || [];

        let html = "";
        national.forEach(h => {
            html += `
                <div class="helpline-card">
                    <div class="helpline-info">
                        <h4>${h.name}</h4>
                        <p>${h.purpose}</p>
                        <small style="color: var(--text-dim);">⏰ ${h.working_hours}</small>
                    </div>
                    <a href="${h.call_link || 'tel:' + h.phone}" class="btn-call-helpline">
                        📞 Call ${h.phone}
                    </a>
                </div>
            `;
        });

        if (stateItems.length > 0) {
            html += `<h4 style="margin-top: 15px; color: var(--primary);">State-Specific Agricultural Helpdesks</h4>`;
            stateItems.forEach(sh => {
                html += `
                    <div class="helpline-card">
                        <div class="helpline-info">
                            <h4>${sh.name} (${sh.state})</h4>
                            <p>${sh.official_source}</p>
                        </div>
                        <a href="${sh.call_link || 'tel:' + sh.phone}" class="btn-call-helpline">
                            📞 Call ${sh.phone}
                        </a>
                    </div>
                `;
            });
        }

        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `
            <div class="helpline-card">
                <div class="helpline-info">
                    <h4>Kisan Call Centre (KCC)</h4>
                    <p>All-India Toll-Free Farmer Advisory in all regional languages</p>
                </div>
                <a href="tel:18001801551" class="btn-call-helpline">📞 Call 1800-180-1551</a>
            </div>
        `;
    }
}

// ------------------------------------------------------------------------------
// SYSTEM HEALTH CHECK
// ------------------------------------------------------------------------------
async function checkSystemHealth() {
    const statusPill = document.getElementById("systemStatusPill");
    const statusText = document.getElementById("connectionStatus");

    try {
        const res = await fetch(`${API_BASE}/health`, { timeout: 4000 });
        if (res.ok) {
            const data = await res.json();
            statusText.textContent = data.groq_configured ? "AI CLOUD ONLINE" : "AI RAG READY";
            statusPill.style.borderColor = "var(--primary)";
        }
    } catch (e) {
        console.warn("Backend offline, running in browser client fallback mode.");
        statusText.textContent = "OFFLINE READY";
    }
}