from fastapi import FastAPI, Request, Form
from fastapi.responses import Response, HTMLResponse
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

# ---------- Database ----------

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

# ---------- AI ----------

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

# ---------- Routes ----------

@app.on_event("startup")
def startup():
    init_db()
    logger.info("Database initialized successfully")

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

    unique_senders = len(set(log["sender"] for log in logs))

    rows_html = ""
    for log in logs:
        rows_html += f"""
        <div class="conversation">
            <div class="sender">From: {log['sender']}</div>
            <div class="timestamp">{log['timestamp']}</div>
            <div class="message-box user"><b>User:</b> {log['user_message']}</div>
            <div class="message-box ai"><b>AI:</b> {log['ai_reply']}</div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp AI Bot Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #f0f2f5; padding: 20px; }}
        h1 {{ color: #25D366; text-align: center; }}
        .stats {{ display: flex; gap: 20px; justify-content: center; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 20px 40px; border-radius: 10px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .stat-card h2 {{ font-size: 2rem; color: #25D366; }}
        .conversation {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .sender {{ font-weight: bold; color: #25D366; margin-bottom: 5px; }}
        .timestamp {{ font-size: 0.8rem; color: #999; margin-bottom: 10px; }}
        .message-box {{ padding: 10px; border-radius: 8px; margin-bottom: 8px; background: #f0f2f5; }}
        .user {{ border-left: 4px solid #25D366; }}
        .ai {{ border-left: 4px solid #075E54; }}
        button {{ display: block; margin: 0 auto 20px; padding: 10px 30px; background: #25D366; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1rem; }}
    </style>
</head>
<body>
    <h1>WhatsApp AI Bot Dashboard</h1>
    <div class="stats">
        <div class="stat-card"><h2>{len(logs)}</h2><p>Total Messages</p></div>
        <div class="stat-card"><h2>{unique_senders}</h2><p>Unique Users</p></div>
    </div>
    <button onclick="location.reload()">Refresh</button>
    {rows_html}
</body>
</html>"""

    return HTMLResponse(content=html)