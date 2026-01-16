from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os, re
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.mount("/static", StaticFiles(directory="static"), name="static")

# ---- SESSION (demo purpose) ----
session = {
    "stage": "start",
    "name": None,
    "phone": None,
    "date": None,
    "time": None
}

SYSTEM_PROMPT = """
You are a polite AI dental clinic receptionist.
Your ONLY task is to help with appointment booking.
Do not repeat questions.
Reply in the user's language.
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return open("static/index.html", encoding="utf-8").read()

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    raw_message = data.get("message", "").strip()
    msg = raw_message.lower()

    # ---------- START ----------
    if session["stage"] == "start":
        session["stage"] = "name"
        return JSONResponse({"reply": "Sure 🙂 May I have your **full name** please?"})

    # ---------- NAME ----------
    if session["stage"] == "name":
        if len(raw_message) < 3:
            return JSONResponse({"reply": "Please enter a valid full name."})
        session["name"] = raw_message
        session["stage"] = "phone"
        return JSONResponse({"reply": "Thank you. Please share your **mobile number**."})

    # ---------- PHONE ----------
    if session["stage"] == "phone":
        phone = re.sub(r"\D", "", raw_message)
        if len(phone) < 10:
            return JSONResponse({"reply": "Please enter a valid 10-digit mobile number."})
        session["phone"] = phone
        session["stage"] = "date"
        return JSONResponse({"reply": "Which **date** would you like the appointment? (Today / Tomorrow)"})

    # ---------- DATE ----------
    if session["stage"] == "date":
        session["date"] = raw_message
        session["stage"] = "time"
        return JSONResponse({"reply": "What **time** do you prefer? (Morning / Evening)"})

    # ---------- TIME ----------
    if session["stage"] == "time":
        session["time"] = raw_message

        confirmation = f"""
✅ **Appointment Request Received**

👤 Name: {session['name']}
📞 Phone: {session['phone']}
📅 Date: {session['date']}
⏰ Time: {session['time']}

Our clinic will contact you shortly.
Thank you!
"""

        # RESET SESSION
        session.update({
            "stage": "start",
            "name": None,
            "phone": None,
            "date": None,
            "time": None
        })

        return JSONResponse({"reply": confirmation})

    # ---------- FALLBACK (LLM ONLY BEFORE BOOKING) ----------
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_message}
        ],
        temperature=0.3,
        max_tokens=100
    )

    return JSONResponse({"reply": response.choices[0].message.content})

