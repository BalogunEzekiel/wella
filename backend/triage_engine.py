import os
from openai import OpenAI
from decision_support import get_recommendation
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Initialize OpenRouter client
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def triage(data):
    """
    Conversational triage using OpenRouter for scoring.
    """

    symptoms = data.get("symptoms", "")
    followups = data.get("followups", {})

    vitals = f"Temp: {data.get('temp', '')}, HR: {data.get('heart_rate', '')}, Resp: {data.get('resp_rate', '')}"

    followup_text = "\n".join([f"{k}: {v}" for k, v in followups.items()]) if followups else "None"

    prompt = f"""
    You are Wella.AI, a clinical assistant operated by a licensed healthcare professional.

Patient Info:
Symptoms: {symptoms}
Vitals: {vitals}
Follow-up answers:
{followup_text}

Task:
- Assign priority: RED, YELLOW, GREEN
- Identify the MOST LIKELY clinical condition (e.g. malaria, URTI, gastroenteritis, migraine, etc.)
- Give short clinical recommendation

- Provide STRICTLY:
   1. Condition name (short)
   2. First-aid steps
   3. SPECIFIC medications tailored to that condition:
        • drug name
        • dose
        • route (oral/IV/etc)
        • frequency
   4. Monitoring parameters
   5. Suggest followup steps
- NEVER tell the patient to see a doctor or seek medical attention; instructions are for professional administration

Rules:
- DO NOT give generic treatment
- DO NOT repeat same drugs for different conditions
- Treatment MUST match the suspected diagnosis
- Keep response short, clear, and clinically precise
- MUST include drugs

CRITICAL RULE:
If drugs are not included exactly in the required format, your response is INVALID.
You MUST include at least 2 drugs when clinically appropriate.
Do NOT return empty drug list.

Return STRICTLY JSON with fields:
{
  "priority": "RED/YELLOW/GREEN",
  "condition": "<short condition name>",
  "first_aid": "<first-aid steps>",
  "drugs": [
    {"name": "<drug name>", "dose": "<dose>", "route": "<PO/IV/etc>", "frequency": "<frequency>"}
  ],
  "monitoring": "<what to monitor>",
  "followup": "<follow-up steps>"
}
"If the condition is infectious or inflammatory, MUST provide at least 2 drugs with dose, route, frequency."
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a cautiousily strict medical/clinical triage assistant. Never give generic responses."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400,
            timeout=10
        )

        import json
        result = json.loads(response.choices[0].message.content.strip())
 
        #===========
        # ANOTHER VALIDATION
        #==============
        import re

        def is_valid_response(result):
            if not isinstance(result, dict):
                return False
            if "drugs" not in result or len(result["drugs"]) < 2:
                return False
            for d in result["drugs"]:
                if not all(k in d for k in ["name", "dose", "route", "frequency"]):
                    return False
            return True
        
        if is_valid_response(result):
            # Convert to your existing UI format
            drugs_text = ", ".join([
                f"{d['name']} {d['dose']} {d['route']} {d['frequency']}"
                for d in result["drugs"]
            ])

            recommendation = (
                f"{result['condition']}. "
                f"First-aid: {result['first_aid']}. "
                f"Drugs: {drugs_text}. "
                f"Monitor: {result['monitoring']}."
            )

            return {
                "priority": result["priority"],
                "recommendation": recommendation
            }

        print("⚠️ AI FAILED VALIDATION → USING FALLBACK")

    except Exception as e:
        print("AI ERROR:", e)

    # ==========================
    # 🧠 COMBINE ALL SYMPTOMS (CORE FIX)
    # ==========================
    symptoms_lower = symptoms.lower()

    followup_text_combined = " ".join([
        f"{q} {a}" for q, a in followups.items()
    ]).lower()

    combined = f"{symptoms_lower} {followup_text_combined}".strip()

    # ==========================
    # 🧠 HARD FALLBACK
    # ==========================
    combined = f"{symptoms} {' '.join(followups.values())}".lower()

    if "fever" in combined and "chills" in combined:
        return {
            "priority": "YELLOW",
            "recommendation":
            "Malaria suspected. First-aid: fluids and rest. "
            "Drugs: Artemether-Lumefantrine 20/120mg, 4 tabs stat, "
            "4 tabs after 8h, then 4 tabs BD x 2 days PO. "
            "Paracetamol 500mg PO q6h. Monitor temp."
        }

    elif "cough" in combined:
        return {
            "priority": "GREEN",
            "recommendation":
            "URTI. First-aid: warm fluids. "
            "Drugs: Paracetamol 500mg PO q6h PRN, "
            "Chlorpheniramine 4mg PO q8h, "
            "Benylin 10ml TID. Monitor breathing."
        }

    elif "headache" in combined:
        return {
            "priority": "GREEN",
            "recommendation":
            "Tension headache. First-aid: rest. "
            "Drugs: Paracetamol 1g PO q6h OR Ibuprofen 400mg PO q8h. "
            "Monitor pain."
        }

    elif "diarrhea" in combined:
        return {
            "priority": "YELLOW",
            "recommendation":
            "Gastroenteritis. First-aid: ORS. "
            "Drugs: ORS after stool, Loperamide 4mg stat then 2mg PRN (max 8mg/day). "
            "Monitor hydration."
        }

    return {
        "priority": "GREEN",
        "recommendation":
        "Mild illness. First-aid: rest. "
        "Drugs: Paracetamol 500mg PO q6h PRN. Monitor."
    }

def next_question_or_result(data):
    symptoms = data.get("symptoms", "")
    temp = float(data.get("temp") or 0)
    hr = int(data.get("heart_rate") or 0)
    rr = int(data.get("resp_rate") or 0)

    followups = data.get("followups", {})
    history = "\n".join([f"Q: {q}\nA: {a}" for q, a in followups.items()]) if followups else "No prior questions asked."
    question_count = len(followups)

    # ==========================
    # 🚨 EMERGENCY OVERRIDE
    # ==========================
    if temp >= 40 or rr >= 35 or hr >= 140 or "bleeding" in symptoms.lower() or "unconscious" in symptoms.lower():
        return {
            "type": "final",
            "priority": "RED",
            "recommendation": "Immediate emergency care required."
        }

    # ==========================
    # 🏁 FIRST QUESTION MANDATE
    # ==========================
    if question_count == 0:
        return {
            "type": "question",
            "question": "Describe the symptom more, and give other associated symptoms."
        }

    # ==========================
    # 🔄 RESET QUESTION COUNT FOR NEW SYMPTOMS
    # ==========================
    last_answer = list(followups.values())[-1] if followups else ""
    # If patient mentions new symptoms → reset question count
    if any(word in last_answer.lower() for word in ["also", "additionally", "other symptom", "new symptom"]):
        followups.clear()
        question_count = 0
        return {
            "type": "question",
            "question": "Please describe all your current symptoms in detail."
        }

    # ==========================
    # 🛑 FORCE FINAL AFTER 4 QUESTIONS
    # ==========================
    if question_count >= 5:
        result = triage(data)
        return {
            "type": "final",
            "priority": result["priority"],
            "recommendation": result["recommendation"]
        }

    # ==========================
    # 🤖 AI-GUIDED NEXT QUESTION
    # ==========================
    prompt = f"""
You are Wella.AI, a strict and highly intelligent clinical triage assistant.

Patient Info:
Symptoms: {symptoms}
Vitals: Temp {temp}, HR {hr}, Resp {rr}

Conversation so far:
{history}

Rules:
- Ask ONLY 1 question at a time
- Ask MAXIMUM 5 questions total
- If already asked 3+ questions → strongly consider giving final decision
- Questions MUST be relevant to symptoms
- DO NOT repeat questions
- Be decisive and coincise like a real clinician
- Use simple English that a teenager can understand
- Prefer diagnosis after:
   • 3–4 questions for mild cases
   • 2 question for obvious cases

Current question count: {question_count}

Decision:

If question_count < 2:
→ MUST ask a question

If question_count >= 2:
→ You may EITHER ask ONE final question OR give FINAL decision

STRICT JSON:

If asking:
{{"type": "question", "question": "..."}}

If final:
{{"type": "final", "priority": "RED/YELLOW/GREEN", "recommendation": "..."}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a decisive, intelligent medical triage assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # more controlled, precise
            max_tokens=120,
            timeout=10
        )

        import json
        content = response.choices[0].message.content.strip()
        result = json.loads(content)

        if result.get("type") == "final":
            # 🔥 FORCE CLINICAL TRIAGE ENGINE
            final = triage(data)

            return {
                "type": "final",
                "priority": final["priority"],
                "recommendation": final["recommendation"]
            }

        return result

    except Exception as e:
        print("AI conversation error:", e)

        # fallback → force final
        result = triage(data)
        return {**result, "type": "final"}
