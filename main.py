from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------
# SIMPLE IN-MEMORY SESSION
# (demo ke liye enough)
# -------------------------
session = {
    "name": None,
    "phone": None,
    "date": None,
    "time": None,
    "urgency": None
}

# -------------------------
# SYSTEM PROMPT (AI BRAIN)
# -------------------------
SYSTEM_PROMPT = """
You are an AI Dental Receptionist for a dental clinic.

Language rules:
- Reply in the same language as the user (English / Hindi / Hinglish)
- Keep replies short, polite, and clear

Your role:
- You are NOT a doctor
- Do NOT give medical advice
- Your ONLY job is appointment booking

Urgent symptoms:
- bleeding, heavy bleeding, blood, severe pain, swelling, sujan, bahut dard

If symptoms are urgent:
- Say it is urgent
- Immediately move to booking
- Do NOT ask medical questions repeatedly

Booking flow (STRICT):
Ask ONE question at a time in this order:
1. Full Name
2. Phone Number
3. Preferred Date (today / tomorrow / specific date)
4. Preferred Time (morning / evening / anytime)

Rules:
- Do NOT repeat questions already answered
- Do NOT loop
- Once all details are collected, confirm booking and STOP
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "").lower()

    # -------------------------
    # URGENCY DETECTION
    # -------------------------
    urgent_keywords = [
        "bleeding", "heavy bleeding", "blood",
        "severe pain", "bahut dard", "sujan", "swelling"
    ]

    if session["urgency"] is None:
        if any(word in user_message for word in urgent_keywords):
            session["urgency"] = "urgent"

    # -------------------------
    # BOOKING STATE LOGIC
    # -------------------------
    if session["urgency"] == "urgent" and session["name"] is None:
        return JSONResponse({
            "reply": "This sounds urgent. Main aapki appointment turant book kar deta hoon. Pehle apna **full name** batayiye."
        })

    if session["name"] is None:
        session["name"] = user_message
        return JSONResponse({
            "reply": "Thank you. Ab apna **mobile number** batayiye jisme clinic aapse contact kare."
        })

    if session["phone"] is None:
        session["phone"] = user_message
        return JSONResponse({
            "reply": "Perfect. Aap kis **date** ke liye appointment chahte hain? (today / tomorrow / specific date)"
        })

    if session["date"] is None:
        session["date"] = user_message
        return JSONResponse({
            "reply": "Got it. Aapko **kaunsa time** preferred hai? (morning / evening / anytime)"
        })

    if session["time"] is None:
        session["time"] = user_message
        return JSONResponse({
            "reply": f"""
✅ **Appointment Request Confirmed**

Name: {session['name']}
Phone: {session['phone']}
Date: {session['date']}
Time: {session['time']}

Clinic aapse jaldi hi call karegi. Thank you!
"""
        })

    # -------------------------
    # FALLBACK (LLM)
    # -------------------------
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.3,
        max_tokens=120
    )

    reply = response.choices[0].message.content
    return JSONResponse({"reply": reply})
