from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.mount("/static", StaticFiles(directory="static"), name="static")


SYSTEM_PROMPT = """
You are a friendly dental clinic receptionist AI.
Speak in simple Hinglish.
Ask max 2 short questions at a time.
Never give medical advice or diagnosis.
Your goal is to understand the patient problem and detect appointment intent.
Gently encourage appointment booking.
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.4,
        max_tokens=150
    )

    reply = response.choices[0].message.content
    return JSONResponse({"reply": reply})
