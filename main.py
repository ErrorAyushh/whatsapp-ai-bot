from fastapi import FastAPI, Request, Form
from fastapi.responses import Response, HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from groq import Groq
from typing import Optional
import logging, os, sqlite3
from datetime import datetime

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
app = FastAPI()
templates = Jinja2Templates(directory="templates")


def init_db():
    conn = sqlite3.connect("conversations.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            user_message TEXT,
            ai_reply TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_conversation(sender: str, user_message: str, ai_reply: str):
    conn = sqlite3.connect("conversations.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversations (sender, user_message, ai_reply, timestamp)
        VALUES (?, ?, ?, ?)
    """, (sender, user_message, ai_reply, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_conversation_history(sender: str):
    conn = sqlite3.connect("conversations.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_message, ai_reply FROM conversations
        WHERE sender = ?
        ORDER BY timestamp DESC
        LIMIT 5
    """, (sender,))
    rows = cursor.fetchall()
    conn.close()
    rows.reverse()
    history = []
    for user_msg, ai_msg in rows:
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": ai_msg})
    return history



def get_ai_reply(sender: str, user_message: str) -> str:
    history = get_conversation_history(sender)
    messages = [
        {"role": "system", "content": "You are a helpful WhatsApp assistant. Keep replies short and friendly. Remember details the user shares with you."}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    return response.choices[0].message.content



@app.on_event("startup")
def startup():
    init_db()
    logger.info("Database initialized")

@app.get("/")
def root():
    return {"status": "WhatsApp AI Bot is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(
    From: Optional[str] = Form(None),
    Body: Optional[str] = Form(None)
):
    sender = From or "unknown"
    message = Body or ""

    logger.info(f"Message from {sender}: {message}")

    ai_reply = get_ai_reply(sender, message)
    save_conversation(sender, message, ai_reply)

    logger.info(f"AI reply: {ai_reply}")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{ai_reply}</Message>
</Response>"""

    return Response(content=twiml, media_type="application/xml")

@app.get("/logs")
def get_logs():
    conn = sqlite3.connect("conversations.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "sender": row[1],
            "user_message": row[2],
            "ai_reply": row[3],
            "timestamp": row[4]
        }
        for row in rows
    ]

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    conn = sqlite3.connect("conversations.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()

    logs = [
        {
            "id": row[0],
            "sender": row[1],
            "user_message": row[2],
            "ai_reply": row[3],
            "timestamp": row[4]
        }
        for row in rows
    ]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "logs": logs,
            "total": len(logs),
            "unique_senders": len(set(l["sender"] for l in logs))
        }
    )