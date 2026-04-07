const API = "http://127.0.0.1:8000";

let currentPatient = {};
let conversation = {}; // stores Q&A

// ==========================
// START TRIAGE
// ==========================
async function submitData() {
    const data = {
        name: document.getElementById("name").value.trim(),
        symptoms: document.getElementById("symptoms").value.trim(),
        temp: document.getElementById("temp").value.trim(),
        heart_rate: document.getElementById("heart_rate").value.trim(),
        resp_rate: document.getElementById("resp_rate").value.trim()
    };

    // ==========================
    // NORMALIZE MULTIPLE SYMPTOMS
    // ==========================
    data.symptoms = data.symptoms
        .split(/,|\n|;| and /i)   // supports comma, newline, semicolon, "and"
        .map(s => s.trim())
        .filter(Boolean)
        .join(", ");

    // ==========================
    // REQUIRED FIELD VALIDATION
    // ==========================
    if (
        !data.name ||
        !data.symptoms ||
        !data.temp ||
        !data.heart_rate ||
        !data.resp_rate
    ) {
        alert("Please fill in all fields before starting triage.");
        return;
    }

    // ==========================
    // NUMERIC VALIDATION
    // ==========================
    if (
        isNaN(data.temp) ||
        isNaN(data.heart_rate) ||
        isNaN(data.resp_rate)
    ) {
        alert("Temperature, Heart Rate, and Respiratory Rate must be valid numbers.");
        return;
    }

    // ==========================
    // CLINICAL RANGE VALIDATION
    // ==========================
    if (data.temp < 30 || data.temp > 45) {
        alert("Enter a valid body temperature (30–45°C).");
        return;
    }

    if (data.heart_rate < 30 || data.heart_rate > 200) {
        alert("Enter a valid heart rate (30–200 bpm).");
        return;
    }

    if (data.resp_rate < 5 || data.resp_rate > 60) {
        alert("Enter a valid respiratory rate (5–60 breaths/min).");
        return;
    }

    // ==========================
    // CONTINUE TRIAGE FLOW
    // ==========================
    currentPatient = data;
    conversation = {};

    clearAllInputs();   // ✅ ADD THIS LINE

    clearChat();
    showChatInput();

    addBotMessage("👋 Hello, I’m your clinical assistant. Let’s assess the patient.");

    startChatFlow(); // ✅ NEW ENGINE
}

// ===================================
// CLEAR ALL INPUT FIELDS AFTER SUBMIT
// ===================================
function clearAllInputs() {
    document.getElementById("name").value = "";
    document.getElementById("symptoms").value = "";
    document.getElementById("temp").value = "";
    document.getElementById("heart_rate").value = "";
    document.getElementById("resp_rate").value = "";
}

// ==========================
// TRUE CHAT LOOP (FIX 2)
// ==========================
async function startChatFlow() {
    let payload = {
        ...currentPatient,
        followups: {}
    };

    while (true) {
        try {
            const res = await fetch(`${API}/triage/chat`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("Server error");

            const data = await res.json();

            // ==========================
            // AI ASKS QUESTION
            // ==========================
            if (data.type === "question") {
                addBotMessage(data.question);

                const answer = await waitForUserInput(); // ⛔ waits here

                addUserMessage(answer);

                payload.followups[data.question] = answer;
            }

            // ==========================
            // AI RETURNS FINAL RESULT
            // ==========================
            else if (data.type === "final") {
                addBotMessage(`🧠 Final Assessment:\n${data.priority} - ${data.recommendation}`);

                showResult(data);
                addPatientToList(data, currentPatient.name);

                hideChatInput();
                break;
            }

        } catch (err) {
            console.error("Chat error:", err);
            saveOffline(currentPatient);
            alert("⚠️ Backend not reachable. Saved offline.");
            break;
        }
    }
}

// ==========================
// WAIT FOR USER INPUT (KEY)
// ==========================
function waitForUserInput() {
    return new Promise((resolve) => {
        const input = document.getElementById("chat-input");
        const button = document.getElementById("chat-send");

        function handler() {
            const value = input.value.trim();
            if (!value) return;

            input.value = "";
            button.removeEventListener("click", handler);
            resolve(value);
        }

        button.addEventListener("click", handler);
    });
}

// ==========================
// CHAT UI
// ==========================
function addBotMessage(text) {
    const chat = document.getElementById("chatbox");
    const div = document.createElement("div");
    div.className = "bot";
    div.innerText = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function addUserMessage(text) {
    const chat = document.getElementById("chatbox");
    const div = document.createElement("div");
    div.className = "user";
    div.innerText = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function clearChat() {
    document.getElementById("chatbox").innerHTML = "";
}

function showChatInput() {
    document.getElementById("chat-input-container").style.display = "flex";
}

function hideChatInput() {
    document.getElementById("chat-input-container").style.display = "none";
}

// ==========================
// RESULT UI
// ==========================
function showResult(data) {
    const div = document.getElementById("result");
    div.innerHTML = `
        <b>Priority:</b> ${data.priority}<br>
        <b>Action:</b> ${data.recommendation}
    `;

    div.style.background =
        data.priority === "RED" ? "#ff4d4d" :
        data.priority === "YELLOW" ? "#ffcc00" :
        data.priority === "GREEN" ? "#66cc66" :
        "#cccccc";
}

// ==========================
// PATIENT LIST
// ==========================
function addPatientToList(result, name) {
    const list = document.getElementById("list");

    const li = document.createElement("li");
    li.innerHTML = `<b>${name}</b> - ${result.priority} - ${result.recommendation}`;

    li.style.color =
        result.priority === "RED" ? "red" :
        result.priority === "YELLOW" ? "orange" :
        result.priority === "GREEN" ? "green" :
        "gray";

    list.prepend(li);
}

// ==========================
// LOAD PATIENTS
// ==========================
async function loadPatients() {
    try {
        const res = await fetch(`${API}/patients`);
        const data = await res.json();

        const list = document.getElementById("list");
        list.innerHTML = "";

        data.patients.forEach(p => {
            const li = document.createElement("li");
            li.innerHTML = `<b>${p[1]}</b> - ${p[6]} - ${p[5]}`;
            list.appendChild(li);
        });
    } catch {
        document.getElementById("list").innerHTML = "<li>Error loading patients</li>";
    }
}

// ==========================
// UTILITIES
// ==========================
function saveOffline(data) {
    let patients = JSON.parse(localStorage.getItem("patients")) || [];
    patients.push(data);
    localStorage.setItem("patients", JSON.stringify(patients));
}

// ==========================
loadPatients();