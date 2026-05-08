import os
import json
import logging
from datetime import datetime
from time import time

import requests
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash

# ─────────────────────────────────────────────────────────────────────────────
# LOAD ENV VARIABLES
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv(find_dotenv())

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# FLASK APP
# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# SECRET KEY
# ─────────────────────────────────────────────────────────────────────────────

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-in-production"
)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION CONFIG
# ─────────────────────────────────────────────────────────────────────────────

app.config.update({
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SAMESITE": "Lax",
    "SESSION_COOKIE_SECURE": False
})

# ─────────────────────────────────────────────────────────────────────────────
# CORS CONFIG
# ─────────────────────────────────────────────────────────────────────────────

raw_origins = os.environ.get("ALLOWED_ORIGINS", "")

ALLOWED_ORIGINS = (
    [o.strip() for o in raw_origins.split(",") if o.strip()]
    if raw_origins else
    [
        "https://interiorductltd.com",
        "https://www.interiorductltd.com",
        "https://duct-ai-backend.onrender.com",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "null"
    ]
)

CORS(
    app,
    origins=ALLOWED_ORIGINS,
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"]
)

# ─────────────────────────────────────────────────────────────────────────────
# GEMINI CONFIG
# ─────────────────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# USE ONE MODEL ONLY
# Prevents SDK/API confusion
GEMINI_MODEL = "gemini-1.5-flash"

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

# ─────────────────────────────────────────────────────────────────────────────
# STARTUP LOGS
# ─────────────────────────────────────────────────────────────────────────────

logger.info("=" * 60)
logger.info("DUCT AI BACKEND STARTING")
logger.info(f"Gemini Model: {GEMINI_MODEL}")
logger.info(f"GEMINI_API_KEY Loaded: {bool(GEMINI_API_KEY)}")

if GEMINI_API_KEY:
    logger.info(f"Key Prefix: {GEMINI_API_KEY[:8]}...")
else:
    logger.warning("⚠️ GEMINI_API_KEY NOT FOUND")

logger.info("=" * 60)

# ─────────────────────────────────────────────────────────────────────────────
# MONGODB CONNECTION
# ─────────────────────────────────────────────────────────────────────────────

mongo_uri = os.environ.get("MONGO_URI")

chats = None
users = None
products = None

if mongo_uri:
    try:
        client = MongoClient(mongo_uri)

        db = client["ductai"]

        chats = db["chats"]
        users = db["users"]
        products = db["products"]

        logger.info("✅ MongoDB connected")

    except Exception as e:
        logger.error(f"MongoDB error: {e}")

else:
    logger.warning("⚠️ MONGO_URI missing")

# ─────────────────────────────────────────────────────────────────────────────
# OPTIONAL S3 STORAGE
# ─────────────────────────────────────────────────────────────────────────────

try:
    from s3_storage import init_s3

    s3_storage = init_s3()

    logger.info("✅ S3 initialized")

except Exception as e:
    logger.warning(f"S3 init warning: {e}")
    s3_storage = None

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are Duct AI — the luxury interior design assistant
for Interior Duct Ltd.

You are sophisticated, professional, warm, and concise.

Expertise:
- Luxury furniture
- Interior design
- Bespoke décor
- Dining tables
- Premium chairs
- Space planning
- Material selection
- Quiet luxury trends
- Earth-tone aesthetics

Rules:
- Keep responses short and elegant
- Always be helpful
- Never mention AI model names
- Ask follow-up questions naturally
"""

# ─────────────────────────────────────────────────────────────────────────────
# SIMPLE RATE LIMITER
# ─────────────────────────────────────────────────────────────────────────────

rate_map = {}

def is_rate_limited(ip):

    now = time()

    data = rate_map.get(ip, {
        "count": 0,
        "start": now
    })

    if now - data["start"] > 60:
        rate_map[ip] = {
            "count": 1,
            "start": now
        }
        return False

    data["count"] += 1
    rate_map[ip] = data

    return data["count"] > 30

# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok",
        "service": "Duct AI Backend",
        "model": GEMINI_MODEL,
        "apiKeyLoaded": bool(GEMINI_API_KEY),
        "time": datetime.utcnow().isoformat() + "Z"
    }), 200

# ─────────────────────────────────────────────────────────────────────────────
# CHAT ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():

    if request.method == "OPTIONS":
        return "", 204

    ip = (
        request.headers.get("X-Forwarded-For")
        or request.remote_addr
        or ""
    ).split(",")[0].strip()

    if is_rate_limited(ip):

        return jsonify({
            "error": "Too many requests. Please wait."
        }), 429

    if not GEMINI_API_KEY:

        logger.error("Missing GEMINI_API_KEY")

        return jsonify({
            "error": "AI service is not configured."
        }), 500

    try:

        body = request.get_json(silent=True) or {}

        messages = body.get("messages", [])

        if not isinstance(messages, list) or not messages:

            return jsonify({
                "error": "messages array is required"
            }), 400

        history = []

        for m in messages:

            role = m.get("role")

            parts = m.get("parts", [])

            if role not in ["user", "model"]:
                continue

            if not isinstance(parts, list):
                continue

            clean_parts = []

            for p in parts:

                text = str(p.get("text", "")).strip()

                if text:
                    clean_parts.append({
                        "text": text[:3000]
                    })

            if clean_parts:
                history.append({
                    "role": role,
                    "parts": clean_parts
                })

        history = history[-20:]

        if not history:

            return jsonify({
                "error": "No valid messages"
            }), 400

        # Inject system prompt
        if history[0]["role"] == "user":

            original = history[0]["parts"][0]["text"]

            history[0]["parts"][0]["text"] = (
                f"[SYSTEM]\n{SYSTEM_PROMPT}\n\n"
                f"[USER]\n{original}"
            )

        payload = {
            "contents": history,
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 512
            }
        }

        response = requests.post(
            GEMINI_URL,
            json=payload,
            headers={
                "Content-Type": "application/json"
            },
            timeout=30
        )

        if not response.ok:

            try:
                err = response.json()
            except Exception:
                err = {}

            logger.error(f"Gemini API error: {err}")

            return jsonify({
                "error": err.get(
                    "error",
                    {}
                ).get(
                    "message",
                    "Gemini API request failed"
                )
            }), 502

        data = response.json()

        reply = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        if not reply:

            logger.error(f"Empty Gemini response: {data}")

            return jsonify({
                "error": "Empty AI response"
            }), 502

        # Optional MongoDB save
        if chats is not None:

            try:
                chats.insert_one({
                    "messages": history,
                    "reply": reply,
                    "createdAt": datetime.utcnow()
                })

            except Exception as db_error:
                logger.warning(f"Mongo save warning: {db_error}")

        return jsonify({
            "reply": reply
        })

    except requests.exceptions.Timeout:

        logger.error("Gemini timeout")

        return jsonify({
            "error": "AI timeout. Please retry."
        }), 504

    except Exception as e:

        logger.error(f"Unexpected server error: {e}")

        return jsonify({
            "error": "Internal server error"
        }), 500

# ─────────────────────────────────────────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def root():

    return jsonify({
        "status": "online",
        "service": "Duct AI Backend"
    })

# ─────────────────────────────────────────────────────────────────────────────
# LOCAL DEV ENTRY
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )