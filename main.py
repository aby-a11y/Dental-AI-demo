from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import re
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------- CONFIG ----------------
INTERRUPTS = ["who are you", "what is this", "hello", "hi"]
EMERGENCY_WORDS = ["bleeding", "blood", "severe pain", "emergency"]

# Simple in-memory session (single user demo)
session = {
    "stage": "start",
    "name": None,
    "phone": None,
    "date": None,
    "time": None
}

# ---------------- ROUTES ----------------
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "").strip()
    msg = user_message.lower()

    # -------- EMERGENCY (TOP PRIORITY) --------
    if any(word in msg for word in EMERGENCY_WORDS):
        return JSONResponse({
            "reply": "🚨 This sounds urgent. Please visit the nearest dental clinic or emergency room immediately. Our team will contact you shortly."
        })

    # -------- WHO ARE YOU / GREETING --------
    if any(word in msg for word in INTERRUPTS):
        return JSONResponse({
            "reply": "😊 I am the AI assistant of our dental clinic. I can help you book appointments or guide you in emergencies."
        })

    # -------- BOOKING FLOW --------
    if session["stage"] == "start":
        session["stage"] = "name"
        return JSONResponse({
            "reply": "Sure 😊 May I have your **full name** please?"
        })

    if session["stage"] == "name":
        session["name"] = user_message
        session["stage"] = "phone"
        return JSONResponse({
            "reply": "Thank you. Please share your **mobile number** 📞"
        })

    if session["stage"] == "phone":
        if not re.fullmatch(r"\d{10}", user_message):
            return JSONResponse({
                "reply": "Please enter a valid **10-digit mobile number**."
            })
        session["phone"] = user_message
        session["stage"] = "date"
        return JSONResponse({
            "reply": "Which **date** would you like the appointment? (Today / Tomorrow)"
        })

    if session["stage"] == "date":
        session["date"] = user_message
        session["stage"] = "time"
        return JSONResponse({
            "reply": "What **time** do you prefer? (Morning / Evening)"
        })

    if session["stage"] == "time":
        session["time"] = user_message

        reply = (
            "✅ **Appointment Request Received**\n\n"
            f"👤 Name: {session['name']}\n"
            f"📞 Phone: {session['phone']}\n"
            f"📅 Date: {session['date']}\n"
            f"⏰ Time: {session['time']}\n\n"
            "Our clinic will contact you shortly. Thank you! 😊"
        )

        # Reset for next booking
        session.update({
            "stage": "start",
            "name": None,
            "phone": None,
            "date": None,
            "time": None
        })

        return JSONResponse({"reply": reply})

    # -------- FALLBACK --------
    return JSONResponse({
        "reply": "I'm here to help you book a dental appointment 😊"
    })


