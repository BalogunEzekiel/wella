from fastapi import APIRouter
import sqlite3
from triage_engine import next_question_or_result

router = APIRouter()

# ==========================
# DATABASE SETUP
# ==========================
conn = sqlite3.connect("wella.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    symptoms TEXT,
    temp TEXT,
    heart_rate TEXT,
    resp_rate TEXT,
    recommendation TEXT,
    priority TEXT
)
""")
conn.commit()


# ==========================
# MAIN AI CHAT ENDPOINT
# ==========================
@router.post("/triage/chat")
async def triage_chat(data: dict):
    """
    AI decides:
    - Ask next question OR
    - Return final result
    """

    response = next_question_or_result(data)

    # ✅ SAVE ONLY FINAL RESULTS
    if response.get("type") == "final":
        cursor.execute("""
            INSERT INTO patients (name, symptoms, temp, heart_rate, resp_rate, priority, recommendation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("name"),
            data.get("symptoms"),
            data.get("temp"),
            data.get("heart_rate"),
            data.get("resp_rate"),
            response.get("priority"),
            response.get("recommendation")
        ))
        conn.commit()

    return response


# ==========================
# GET PATIENTS
# ==========================
@router.get("/patients")
async def get_patients():
    cursor.execute("SELECT * FROM patients ORDER BY id DESC")
    patients = cursor.fetchall()
    return {"patients": patients}