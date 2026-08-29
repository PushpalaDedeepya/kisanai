// ============================================
// KISAN AI - FRONTEND JAVASCRIPT
// ============================================


// --------------------------------------------
// BACKEND
// --------------------------------------------

const API_BASE = "http://127.0.0.1:8000";


// --------------------------------------------
// GET HTML ELEMENTS
// --------------------------------------------

const language = document.getElementById("language");

const locationInput =
    document.getElementById("location");

const locationButton =
    document.getElementById("locationButton");

const locationStatus =
    document.getElementById("locationStatus");

const questionInput =
    document.getElementById("question");

const voiceButton =
    document.getElementById("voiceButton");

const voiceStatus =
    document.getElementById("voiceStatus");

const askButton =
    document.getElementById("askButton");

const loading =
    document.getElementById("loading");

const answer =
    document.getElementById("answer");

const prescriptionPage =
    document.getElementById("prescriptionPage");

const prescriptionLocation =
    document.getElementById("prescriptionLocation");

const prescriptionLanguage =
    document.getElementById("prescriptionLanguage");

const prescriptionAdvice =
    document.getElementById("prescriptionAdvice");

const advisoryMode =
    document.getElementById("advisoryMode");

const connectionStatus =
    document.getElementById("connectionStatus");


// --------------------------------------------
// LANGUAGE → SPEECH CODE
// --------------------------------------------

const speechLanguages = {

    English: "en-IN",

    Telugu: "te-IN",

    Hindi: "hi-IN",

    Tamil: "ta-IN",

    Kannada: "kn-IN"

};


// ============================================
// VOICE INPUT
// ============================================

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


let recognition = null;

let isListening = false;


// --------------------------------------------
// CHECK VOICE SUPPORT
// --------------------------------------------

if (SpeechRecognition) {

    recognition = new SpeechRecognition();

    recognition.continuous = false;

    recognition.interimResults = true;

    recognition.maxAlternatives = 1;


    // ----------------------------------------
    // START
    // ----------------------------------------

    recognition.onstart = function () {

        isListening = true;

        voiceButton.classList.add("recording");

        voiceButton.textContent =
            "🔴 Listening...";

        voiceStatus.textContent =
            "🎙️ Speak your farming problem...";

    };


    // ----------------------------------------
    // RESULT
    // ----------------------------------------

    recognition.onresult = function (event) {

        let transcript = "";

        for (
            let i = event.resultIndex;
            i < event.results.length;
            i++
        ) {

            transcript +=
                event.results[i][0].transcript;

        }

        questionInput.value =
            transcript.trim();

    };


    // ----------------------------------------
    // ERROR
    // ----------------------------------------

    recognition.onerror = function (event) {

        console.error(
            "Speech recognition error:",
            event.error
        );


        if (event.error === "not-allowed") {

            voiceStatus.textContent =
                "❌ Microphone permission denied. Allow microphone access in your browser.";

        }

        else if (event.error === "no-speech") {

            voiceStatus.textContent =
                "⚠️ No speech detected. Please try again.";

        }

        else if (event.error === "audio-capture") {

            voiceStatus.textContent =
                "❌ Microphone could not be accessed.";

        }

        else {

            voiceStatus.textContent =
                "❌ Voice input failed. Please try again.";

        }

        stopVoice();

    };


    // ----------------------------------------
    // END
    // ----------------------------------------

    recognition.onend = function () {

        stopVoice();

    };

}
else {

    voiceButton.disabled = true;

    voiceButton.textContent =
        "🎙️ Not supported";

    voiceStatus.textContent =
        "Voice recognition is not supported in this browser. Try Google Chrome.";

}


// --------------------------------------------
// VOICE BUTTON
// --------------------------------------------

voiceButton.addEventListener(
    "click",
    function () {

        if (!recognition) {

            return;

        }


        if (isListening) {

            recognition.stop();

            return;

        }


        const selectedLanguage =
            speechLanguages[language.value] ||
            "en-IN";


        recognition.lang =
            selectedLanguage;


        try {

            recognition.start();

        }

        catch (error) {

            console.error(error);

        }

    }
);


// --------------------------------------------
// STOP VOICE
// --------------------------------------------

function stopVoice() {

    isListening = false;

    voiceButton.classList.remove("recording");

    voiceButton.textContent =
        "🎙️ Speak";

}


// ============================================
// LOCATION
// ============================================

locationButton.addEventListener(
    "click",
    function () {

        detectLocation();

    }
);


function detectLocation() {

    if (!navigator.geolocation) {

        locationStatus.textContent =
            "❌ Geolocation is not supported by this browser.";

        return;

    }


    locationButton.disabled = true;

    locationStatus.textContent =
        "📍 Detecting your location...";


    navigator.geolocation.getCurrentPosition(

        function (position) {

            const latitude =
                position.coords.latitude;

            const longitude =
                position.coords.longitude;


            console.log(
                "GPS:",
                latitude,
                longitude
            );


            locationStatus.textContent =
                "📍 GPS detected. Finding your area...";


            reverseGeocode(
                latitude,
                longitude
            );

        },


        function (error) {

            console.error(
                "Location error:",
                error
            );


            locationButton.disabled = false;


            if (error.code === 1) {

                locationStatus.textContent =
                    "❌ Location permission denied. Please allow location access.";

            }

            else if (error.code === 2) {

                locationStatus.textContent =
                    "❌ Location unavailable.";

            }

            else if (error.code === 3) {

                locationStatus.textContent =
                    "⏳ Location request timed out. Try again.";

            }

            else {

                locationStatus.textContent =
                    "❌ Unable to detect location.";

            }

        },

        {

            enableHighAccuracy: true,

            timeout: 15000,

            maximumAge: 300000

        }

    );

}


// --------------------------------------------
// REVERSE GEOCODING
// --------------------------------------------

async function reverseGeocode(
    latitude,
    longitude
) {

    try {

        const url =
            "https://nominatim.openstreetmap.org/reverse" +
            "?format=json" +
            "&lat=" +
            encodeURIComponent(latitude) +
            "&lon=" +
            encodeURIComponent(longitude) +
            "&zoom=10" +
            "&addressdetails=1";


        const response =
            await fetch(url);


        if (!response.ok) {

            throw new Error(
                "Reverse geocoding failed"
            );

        }


        const data =
            await response.json();


        console.log(
            "Location data:",
            data
        );


        const address =
            data.address || {};


        const place =

            address.city ||

            address.town ||

            address.village ||

            address.municipality ||

            address.county ||

            address.state ||

            "Current location";


        locationInput.value =
            place;


        locationStatus.textContent =
            "📍 " + place + " detected";


        locationButton.disabled = false;

    }

    catch (error) {

        console.error(error);


        locationInput.value =
            latitude.toFixed(4) +
            ", " +
            longitude.toFixed(4);


        locationStatus.textContent =
            "📍 GPS coordinates detected";


        locationButton.disabled = false;

    }

}


// ============================================
// OFFLINE FARMING KNOWLEDGE
// ============================================

const offlineKnowledge = [

    {
        keywords: ["tomato", "yellow"],
        answer:
            "For tomato plants with yellow leaves, first check soil moisture, drainage and sunlight. Inspect the leaves and stems for pests or disease symptoms. Avoid excessive watering. If nutrient deficiency is suspected, consider a soil test before applying fertilizer."
    },


    {
        keywords: ["tomato", "water"],
        answer:
            "Tomatoes need consistent soil moisture, but excessive watering can cause root problems. Check the soil before watering and make sure the field or container has good drainage."
    },


    {
        keywords: ["rice", "water"],
        answer:
            "Rice requires careful water management. Irrigation needs depend on crop stage, soil condition and rainfall. Avoid unnecessary water use and adjust irrigation according to field conditions."
    },


    {
        keywords: ["cotton", "pest"],
        answer:
            "Inspect cotton plants regularly for insect pests and leaf damage. Identify the pest before choosing a control method. Integrated pest management can help reduce unnecessary pesticide use."
    },


    {
        keywords: ["groundnut", "water"],
        answer:
            "Groundnut performs best in well-drained soil. Maintain adequate moisture during germination, flowering and pod development while avoiding waterlogging."
    },


    {
        keywords: ["chilli", "pest"],
        answer:
            "Inspect chilli plants regularly for sucking pests and leaf damage. Remove heavily affected plant material where appropriate and identify the pest before choosing a control method."
    },


    {
        keywords: ["fertilizer"],
        answer:
            "Avoid applying fertilizer blindly. Soil testing can help determine nutrient requirements. Use fertilizer according to crop needs, soil condition and locally recommended practices."
    },


    {
        keywords: ["pest"],
        answer:
            "Inspect the crop carefully and identify the pest before taking action. Integrated pest management includes field sanitation, monitoring and appropriate control methods. Follow product labels and local agricultural guidance."
    },


    {
        keywords: ["rain"],
        answer:
            "Check local weather conditions before irrigation or spraying. Heavy rainfall can increase waterlogging and disease risk, so adjust farm activities according to field conditions."
    },


    {
        keywords: ["leaf", "spot"],
        answer:
            "Leaf spots can have several causes, including fungal or bacterial diseases, pests or environmental stress. Inspect the pattern of spots and affected plant parts before choosing a treatment."
    },


    {
        keywords: ["weed"],
        answer:
            "Control weeds early because they compete with crops for water, nutrients and sunlight. Choose weed-management practices suitable for the crop and growth stage."
    }

];


// --------------------------------------------
// GET OFFLINE ADVICE
// --------------------------------------------

function getOfflineAdvice(question) {

    const lowerQuestion =
        question.toLowerCase();


    for (
        const item of offlineKnowledge
    ) {

        let matchCount = 0;


        for (
            const keyword of item.keywords
        ) {

            if (
                lowerQuestion.includes(keyword)
            ) {

                matchCount++;

            }

        }


        if (matchCount >= 2) {

            return item.answer;

        }

    }


    return (
        "Offline mode is active. Basic advice: " +
        "inspect your crop regularly, check soil moisture, " +
        "avoid unnecessary irrigation or fertilizer, and " +
        "identify pests or diseases before taking action. " +
        "For crop-specific problems, consult a local agricultural expert."
    );

}


// ============================================
// ASK KISAN AI
// ============================================

askButton.addEventListener(
    "click",
    askKisanAI
);


async function askKisanAI() {

    const question =
        questionInput.value.trim();


    const selectedLanguage =
        language.value;


    const farmLocation =
        locationInput.value.trim();


    // ----------------------------------------
    // VALIDATE
    // ----------------------------------------

    if (!question) {

        answer.textContent =
            "🌾 Please speak or type your farming question first.";

        questionInput.focus();

        return;

    }


    // ----------------------------------------
    // UI LOADING
    // ----------------------------------------

    askButton.disabled = true;

    loading.textContent =
        "🤖 Kisan AI is thinking...";


    answer.textContent =
        "Preparing your farming advice...";


    prescriptionPage.classList.remove(
        "show"
    );


    try {

        console.log(
            "Sending request to backend..."
        );


        const response =
            await fetch(
                API_BASE + "/ask",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        question: question,

                        language:
                            selectedLanguage,

                        location:
                            farmLocation

                    })

                }
            );


        if (!response.ok) {

            throw new Error(
                "Backend returned " +
                response.status
            );

        }


        const data =
            await response.json();


        console.log(
            "Backend response:",
            data
        );


        const aiAnswer =
            data.answer ||
            data.response ||
            "No answer received from AI.";


        answer.textContent =
            aiAnswer;


        connectionStatus.textContent =
            "AI SYSTEM ONLINE";


        advisoryMode.textContent =
            "AI GENERATED";


        showPrescription(

            aiAnswer,

            selectedLanguage,

            farmLocation

        );

    }


    catch (error) {

        console.error(
            "Backend connection error:",
            error
        );


        // ------------------------------------
        // OFFLINE FALLBACK
        // ------------------------------------

        const offlineAnswer =
            getOfflineAdvice(question);


        answer.textContent =
            offlineAnswer;


        connectionStatus.textContent =
            "OFFLINE MODE";


        advisoryMode.textContent =
            "OFFLINE ADVISORY";


        showPrescription(

            offlineAnswer,

            selectedLanguage,

            farmLocation

        );

    }


    finally {

        loading.textContent = "";

        askButton.disabled = false;

    }

}


// ============================================
// PRESCRIPTION
// ============================================

function showPrescription(

    advice,

    selectedLanguage,

    farmLocation

) {

    prescriptionLocation.textContent =
        farmLocation ||
        "Location not provided";


    prescriptionLanguage.textContent =
        selectedLanguage;


    prescriptionAdvice.textContent =
        advice;


    prescriptionPage.classList.add(
        "show"
    );


    setTimeout(
        function () {

            prescriptionPage.scrollIntoView({

                behavior: "smooth",

                block: "nearest"

            });

        },
        100
    );

}


// ============================================
// LANGUAGE CHANGE
// ============================================

language.addEventListener(
    "change",
    function () {

        if (
            isListening &&
            recognition
        ) {

            recognition.stop();

        }


        voiceStatus.textContent =
            "🎙️ Voice language: " +
            language.value;

    }
);


// ============================================
// STARTUP
// ============================================

console.log(
    "🌾 KISAN AI frontend loaded successfully!"
);

console.log(
    "Backend:",
    API_BASE
);