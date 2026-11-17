import os
import sqlite3

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from google import genai

load_dotenv()

DB_PATH = "rafiki.db"
MODEL_NAME = "gemini-3.1-flash-lite"
SYSTEM_PROMPT = "SMS AI assistant for rural Africa. Plain text only, no markdown, max 300 chars."

app = Flask(__name__)


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT,
                role TEXT,
                text TEXT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_history(phone):
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT role, text FROM messages WHERE phone = ? ORDER BY id DESC LIMIT 6",
            (phone,),
        ).fetchall()
    return [
        {"role": row["role"], "text": row["text"]}
        for row in reversed(rows)
    ]


def save_message(phone, role, text):
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO messages (phone, role, text) VALUES (?, ?, ?)",
            (phone, role, text),
        )
        conn.commit()


def clear_memory(phone):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM messages WHERE phone = ?", (phone,))
        conn.commit()


def build_contents(history, prompt):
    contents = []
    for item in history:
        contents.append({"role": item["role"], "parts": [{"text": item["text"]}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    return contents


def generate_reply(history, prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=build_contents(history, prompt),
        config={"system_instruction": SYSTEM_PROMPT},
    )

    text = getattr(response, "text", None)
    if not text:
        text = str(response)
    return text.strip()[:300]


def send_sms(sender, message):
    api_key = os.getenv("TEXTBEE_API_KEY")
    device_id = os.getenv("TEXTBEE_DEVICE_ID")
    if not api_key or not device_id:
        raise RuntimeError("TEXTBEE credentials are not set")

    response = requests.post(
        f"https://api.textbee.dev/api/v1/gateway/devices/{device_id}/send-sms",
        headers={"x-api-key": api_key},
        json={"recipients": [sender], "message": message},
        timeout=15,
    )
    response.raise_for_status()
    return True


@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(silent=True) or {}
    sender = str(payload.get("sender", "") or "").strip()
    message = str(payload.get("message", "") or "").strip()

    if not sender or not message:
        return jsonify({"ok": True}), 200

    if message.upper() == "RESET":
        clear_memory(sender)
        try:
            send_sms(sender, "Memory cleared.")
        except Exception:
            app.logger.exception("Failed to send reset SMS")
        return jsonify({"ok": True}), 200

    history = fetch_history(sender)
    save_message(sender, "user", message)

    try:
        reply = generate_reply(history, message)
    except Exception:
        app.logger.exception("Gemini generation failed")
        reply = "Sorry, I could not respond right now."

    save_message(sender, "model", reply)

    try:
        send_sms(sender, reply)
    except Exception:
        app.logger.exception("Failed to send outbound SMS")

    return jsonify({"ok": True}), 200


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
