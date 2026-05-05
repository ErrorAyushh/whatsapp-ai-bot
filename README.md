# WhatsApp AI Chatbot

A WhatsApp chatbot powered by Groq LLM (Llama 3.3) and built with FastAPI. It receives real WhatsApp messages via Twilio, generates intelligent AI replies, remembers conversation history, and logs everything to a visual dashboard.

---

## Features

- Receives real WhatsApp messages via Twilio Sandbox
- AI replies powered by Groq (Llama 3.3-70b)
- Conversation memory (remembers last 5 messages per user)
- Logs all conversations to SQLite database
- Visual web dashboard to monitor conversations
- Fast and lightweight FastAPI backend

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| FastAPI | Python web framework |
| Groq API | LLM (Llama 3.3-70b-versatile) |
| Twilio | WhatsApp messaging |
| SQLite | Conversation logging |
| ngrok | Expose localhost to internet |
| Jinja2 | Dashboard templating |

---

## Project Structure
whatsapp-ai-bot/

├── main.py

├── requirements.txt

├── .env.example

├── .gitignore

└── templates/

└── dashboard.html

---

## Setup and Installation

### 1. Clone the repository
git clone https://github.com/ErrorAyushh/whatsapp-ai-bot.git
cd whatsapp-ai-bot

### 2. Create virtual environment
python -m venv venv
Windows
venv\Scripts\activate
Mac/Linux
source venv/bin/activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Set up environment variables
cp .env.example .env

Edit .env and add your key:
GROQ_API_KEY=your_groq_key_here

### 5. Run the server
uvicorn main:app --reload --port 8000

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Server status |
| POST | `/webhook` | Receives WhatsApp messages |
| GET | `/logs` | JSON conversation logs |
| GET | `/dashboard` | Visual dashboard |

---

## Twilio and ngrok Setup

1. Sign up at https://twilio.com for free
2. Go to Messaging → Try it out → Send a WhatsApp message
3. Join the sandbox from your phone by sending the join code to +14155238886
4. Run ngrok:
ngrok http 8000
5. Copy the ngrok URL and set it as your Twilio webhook:
https://your-ngrok-url.ngrok-free.app/webhook

---

## Getting a Free Groq API Key

1. Go to https://console.groq.com
2. Sign up for free
3. Go to API Keys and create a new key
4. Paste it in your .env file

---

## How It Works
User sends WhatsApp message
↓
Twilio receives it

↓

Twilio sends POST request to /webhook

↓

FastAPI processes the message

↓

Last 5 messages loaded from SQLite (memory)

↓

Groq LLM generates a reply

↓

Reply saved to SQLite

↓

TwiML response sent back to Twilio

↓

User receives AI reply on WhatsApp


---

## Dashboard

Visit http://localhost:8000/dashboard to see:
- Total messages count
- Unique users count
- Full conversation history with AI replies

---

## Built By

Ayush - B.Tech AI/ML Student at VIPS Delhi

GitHub: https://github.com/ErrorAyushh


