const API_BASE = "http://127.0.0.1:8000";

const language = document.getElementById("language");
const locationInput = document.getElementById("location");
const questionInput = document.getElementById("question");
const askButton = document.getElementById("askButton");
const loading = document.getElementById("loading");
const answer = document.getElementById("answer");

askButton.addEventListener("click", async () => {
    const question = questionInput.value.trim();
    const selectedLanguage = language.value;
    const location = locationInput.value.trim();

    if (!question) {
        answer.textContent = "Please enter your farming question first 🌾";
        questionInput.focus();
        return;
    }

    askButton.disabled = true;
    askButton.style.opacity = "0.7";
    loading.textContent = "Kisan AI is thinking... 🤖";
    answer.textContent = "Preparing your personalized farming advice...";

    try {
        const response = await fetch(`${API_BASE}/ask`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                language: selectedLanguage,
                location: location
            })
        });

        if (!response.ok) {
            throw new Error("Backend request failed");
        }

        const data = await response.json();

        answer.textContent = data.answer || "No answer was received.";

    } catch (error) {
        console.error("Kisan AI Error:", error);

        answer.textContent =
            "Unable to connect to Kisan AI. Please make sure the backend server is running.";
    } finally {
        loading.textContent = "";
        askButton.disabled = false;
        askButton.style.opacity = "1";
    }
});

questionInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && event.ctrlKey) {
        askButton.click();
    }
});