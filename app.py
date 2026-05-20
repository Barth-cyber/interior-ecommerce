import os
import json
import logging
from datetime import datetime
from time import time

import requests
from flask import Flask, request, jsonify, session, Response, send_from_directory
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
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def is_env_value_valid(value):
    if not value:
        return False

    normalized = value.strip()
    if not normalized:
        return False

    lowered = normalized.lower()
    placeholder_prefixes = (
        "your_",
        "change",
        "replace",
        "dummy",
        "example",
        "test_",
        "none",
        "null"
    )

    if lowered.startswith(placeholder_prefixes):
        return False

    if normalized.startswith("AIza") and len(normalized) < 40:
        return False

    return True


def get_env_var(*names, default=""):
    for name in names:
        value = os.environ.get(name)
        if is_env_value_valid(value):
            return value.strip()
    return default


def first_env_name(*names):
    for name in names:
        value = os.environ.get(name)
        if is_env_value_valid(value):
            return name
    return None


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI CONFIG
# ─────────────────────────────────────────────────────────────────────────────

GEMINI_MODEL = "gemini-1.5-flash"

GEMINI_API_KEY = get_env_var(
    "GEMINI_API_KEY",
    "Gemini_API_Key",
    "GOOGLE_API_KEY",
    "GOOGLE_GEMINI_API_KEY"
)

GEMINI_API_KEY_SOURCE = first_env_name(
    "GEMINI_API_KEY",
    "Gemini_API_Key",
    "GOOGLE_API_KEY",
    "GOOGLE_GEMINI_API_KEY"
)

GEMINI_URL = None
if GEMINI_API_KEY:
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
    logger.info(f"Gemini key found in: {GEMINI_API_KEY_SOURCE}")
    logger.info(f"Key Prefix: {GEMINI_API_KEY[:8]}...")
else:
    logger.warning("⚠️ GEMINI_API_KEY NOT FOUND")

mongo_uri = get_env_var("MONGO_URI", "MONGODB_URI", "MONGO_URL", "DATABASE_URL")
mongo_source = first_env_name("MONGO_URI", "MONGODB_URI", "MONGO_URL", "DATABASE_URL")

if mongo_uri:
    logger.info(f"MONGO_URI Loaded: True")
    logger.info(f"Mongo connection string found in: {mongo_source}")
else:
    logger.warning("⚠️ MONGO_URI missing")

logger.info("=" * 60)

# ─────────────────────────────────────────────────────────────────────────────
# MONGODB CONNECTION
# ─────────────────────────────────────────────────────────────────────────────

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
        "apiKeySource": GEMINI_API_KEY_SOURCE,
        "mongoUriLoaded": bool(mongo_uri),
        "mongoUriSource": mongo_source,
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
# FRONTEND CONFIG
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/backend-config.js")
def backend_config_js():

    backend_url = os.environ.get("DUCT_AI_BACKEND_URL", "").strip()
    if not backend_url:
        backend_url = os.environ.get("BACKEND_URL", "").strip()

    js = f"window.DUCT_AI_BACKEND_URL = window.DUCT_AI_BACKEND_URL || {json.dumps(backend_url)};\n"
    js += "window.__BACKEND_URL__ = window.__BACKEND_URL__ || window.DUCT_AI_BACKEND_URL || '';\n"

    return Response(js, mimetype="application/javascript")


# ─────────────────────────────────────────────────────────────────────────────
# PROMOTIONS API (social posts + second-hand listings)
# ─────────────────────────────────────────────────────────────────────────────


@app.route('/api/promotions', methods=['GET'])
def api_promotions():
    try:
        base = os.path.abspath('.')
        social_path = os.path.join(base, 'social_posts.json')
        second_path = os.path.join(base, 'second_hand_products.json')

        social = []
        second = { 'products': [] }

        if os.path.isfile(social_path):
            try:
                with open(social_path, 'r', encoding='utf-8') as f:
                    social = json.load(f) or []
            except Exception:
                social = []

        if os.path.isfile(second_path):
            try:
                with open(second_path, 'r', encoding='utf-8') as f:
                    second = json.load(f) or { 'products': [] }
            except Exception:
                second = { 'products': [] }

        return jsonify({
            'social': social,
            'second_hand': second
        })

    except Exception as e:
        logger.error(f"Promotions API error: {e}")
        return jsonify({ 'social': [], 'second_hand': { 'products': [] } }), 500


# ─────────────────────────────────────────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def root():

    return send_from_directory('.', 'interior.html')


@app.route('/<path:path>')
def serve_static(path):

    # Serve frontend static assets from either the root or the static folder
    if path.startswith('static/'):
        return send_from_directory('static', path[len('static/'):])

    if os.path.isfile(path):
        return send_from_directory('.', path)

    static_path = os.path.join('static', path)
    if os.path.isfile(static_path):
        return send_from_directory('static', path)

    return send_from_directory('.', 'interior.html')


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