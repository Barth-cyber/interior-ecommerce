"""Duct AI Backend — Interior Duct Ltd
Lightweight Flask backend used by local preview and the production site.

Endpoints:
- GET  /            -> status + model info
- GET  /health      -> simple health
- POST /ai-query    -> main chat endpoint
- POST /recommend   -> recommendation endpoint

This file uses `google-genai` (imported as `google.genai`) when a
`GEMINI_API_KEY` is present. The GenAI client is lazily initialised so
the module can still be imported in environments without the package.
"""

import os
import re
import json
import time
import datetime
from typing import Any, List, Optional
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv

# Load environment variables from the nearest .env file
load_dotenv(find_dotenv())

# GenAI globals

# Gemini globals
_gemini_model = None
_gemini_model_name = None
_gemini_initialized = False
_genai_client = None

# OpenAI config
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# Anthropic (Claude) config
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

DEFAULT_FALLBACKS = [
    "Apologies — I couldn\'t complete that request right now. Please try again in a moment or message our team on WhatsApp at +234 803 685 0229.",
    "I\'m sorry, the AI service is temporarily unavailable. I will do my best to help with a quick response or route you to support.",
    "Our design assistant had trouble responding. Could you try one more time or request a quote through WhatsApp?",
    "I couldn\'t resolve that exactly, but I can still help with product ideas, pricing, or a custom order quote."
]

def _call_openai(system_prompt, user_query):
    if not OPENAI_API_KEY:
        return None, "OpenAI API key not set"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.7
    }
    try:
        resp = requests.post(OPENAI_URL, headers=headers, json=data, timeout=20)
        resp.raise_for_status()
        result = resp.json()
        content = result["choices"][0]["message"]["content"].strip()
        return content, None
    except Exception as e:
        return None, str(e)


def _call_anthropic(system_prompt, user_query):
    if not ANTHROPIC_API_KEY:
        return None, "Anthropic API key not set"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    data = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_query}
        ]
    }
    try:
        resp = requests.post(ANTHROPIC_URL, headers=headers, json=data, timeout=20)
        resp.raise_for_status()
        result = resp.json()
        content = result["content"][0]["text"].strip()
        return content, None
    except Exception as e:
        return None, str(e)


def _init_gemini() -> None:
    """Initialise google.genai client and pick a usable Gemini model.

    This does a local import of `google.genai` to avoid hard dependency
    at module import time. It sets `_gemini_model` to `client.models` so
    call sites can use `generate_content(model=..., contents=...)`.
    """
    global _gemini_model, _gemini_model_name, _gemini_initialized
    if _gemini_initialized:
        return
    _gemini_initialized = True
    try:
        import google.genai as genai
        gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not gemini_api_key:
            _gemini_model = None
            _gemini_model_name = None
            return

        client = genai.client.Client(api_key=gemini_api_key)
        # keep a reference to the client to avoid it being closed/GC'd
        global _genai_client
        _genai_client = client
        for model_name in [
            "models/gemini-2.5-flash",
            "models/gemini-2.5-pro",
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-001",
            "models/gemini-2.0-flash-lite-001",
            "models/gemini-2.0-flash-lite",
        ]:
            try:
                client.models.get(model=model_name)
                _gemini_model = client.models
                _gemini_model_name = model_name
                print(f"GenAI init: using model {model_name}")
                return
            except Exception as e:
                print(f"GenAI model not available {model_name}: {e}")

        _gemini_model = None
        _gemini_model_name = None
        print("GenAI init: no usable model found")
    except Exception as e:
        print(f"GenAI init failed: {e}")
        _gemini_model = None
        _gemini_model_name = None


# Flask app and CORS
app = Flask(__name__)


def _parse_allowed_origins():
    raw = os.environ.get("ALLOWED_ORIGINS", "").strip()
    dev_origins = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ]
    if raw:
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        for o in dev_origins:
            if o not in origins:
                origins.append(o)
        return origins
    return [
        "https://interiorductltd.com",
        "https://www.interiorductltd.com",
        "https://api.interiorductltd.com",
        "https://interior-ecommerce.onrender.com",
        "https://interior-ecommerce-lh3e.onrender.com",
        "https://duct-ai-backend.onrender.com",
        "https://interior-ecommerce-backend.onrender.com",
        *dev_origins,
    ]


CORS(app, resources={r"/*": {"origins": _parse_allowed_origins()}})


# Paths
BASE_DIR = os.path.dirname(__file__)
KB_PATH = os.path.join(BASE_DIR, "knowledge_base.json")
PRODUCTS_PATH = os.path.join(BASE_DIR, "products.json")
CONV_LOG_PATH = os.path.join(BASE_DIR, "conversations.json")
USER_LOG_PATH = os.path.join(BASE_DIR, "user_log.json")
FEEDBACK_PATH = os.path.join(BASE_DIR, "feedback.json")
DEPLOYMENT_REVISION = os.environ.get("DEPLOYMENT_REVISION", "dev")


def _read_json(path: str, default: Any):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: str, data) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Write error {path}: {e}")
        return False


def _load_kb():
    return _read_json(KB_PATH, {})


def _load_products():
    p = _read_json(PRODUCTS_PATH, None)
    if p is not None:
        return p
    kb = _load_kb()
    return kb.get("products", [])


def _build_system_prompt():
    kb = _load_kb()
    prods = _load_products()
    faq_text = "\n".join(f"Q: {f['q']}\nA: {f['a']}" for f in kb.get("faqs", [])[:20])
    product_list = "\n".join(f"- {p.get('name','?')} | {p.get('category','')} | {p.get('price','')}" for p in prods[:30])
    return f"You are Duct AI, the intelligent luxury design assistant for Interior Duct Ltd.\n\n{faq_text}\n\n{product_list}"


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()


def _text_tokens(text: str) -> List[str]:
    return [token for token in _normalize_text(text).split() if len(token) > 2]


def _token_score(query_tokens: List[str], text: str) -> int:
    if not query_tokens:
        return 0
    return len(set(query_tokens) & set(_text_tokens(text)))


def _find_kb_response(query: str, kb: dict) -> Optional[str]:
    if not query:
        return None
    query_lower = query.lower()
    query_tokens = _text_tokens(query)

    # Simple greeting or FAQ trigger matches
    for item in kb.get("greetings", []):
        for trigger in item.get("trigger", []):
            if trigger and trigger.lower() in query_lower:
                return item.get("response")

    # Match FAQ entries by keyword overlap and direct phrase
    best_faq = None
    best_score = 0
    for faq in kb.get("faqs", []):
        source = " ".join([faq.get("q", ""), faq.get("a", ""), faq.get("category", "")])
        score = _token_score(query_tokens, source)
        if faq.get("q", "").lower() in query_lower or query_lower in faq.get("q", "").lower():
            score += 2
        if score > best_score:
            best_score = score
            best_faq = faq
    if best_faq and best_score >= 2:
        return best_faq.get("a")

    company = kb.get("company_info", {})
    contact = company.get("contact", {})
    if any(term in query_lower for term in ["email", "mail", "contact"]):
        email = contact.get("email_primary") or contact.get("email_secondary")
        if email:
            return f"You can contact us on email at {email}. For the fastest response, message us on WhatsApp at +234 803 685 0229."
    if any(term in query_lower for term in ["phone", "call", "whatsapp", "number"]):
        phone = contact.get("phone") or contact.get("alt_phone")
        if phone:
            return f"You can reach our team on WhatsApp or phone at {phone}. You can also email us at {contact.get('email_primary', 'hello@interiorductltd.com')}."
    if any(term in query_lower for term in ["location", "address", "where", "showroom", "headquarters"]):
        location = company.get("headquarters")
        showrooms = company.get("showrooms", [])
        if location or showrooms:
            showroom_text = f" Our showrooms are in {', '.join(showrooms)}." if showrooms else ""
            return f"Our headquarters is in {location}.{showroom_text} Showroom visits are by appointment."

    return None


def _extract_response_text(response) -> str:
    if response is None:
        return ""
    if hasattr(response, "text") and response.text:
        return str(response.text).strip()
    candidates = getattr(response, "candidates", None)
    if candidates:
        try:
            first = candidates[0]
            if hasattr(first, "content") and first.content:
                return str(first.content).strip()
            if isinstance(first, dict) and first.get("content"):
                return str(first["content"]).strip()
        except Exception:
            return ""
    return ""


# Simple in-memory stores and logging helpers
_sessions = {}


def _log_conversation(session_id, role, text, context=None):
    logs = _read_json(CONV_LOG_PATH, [])
    logs.append({
        "session_id": session_id,
        "role": role,
        "text": text,
        "context": context or {},
        "ts": datetime.datetime.utcnow().isoformat(),
    })
    if len(logs) > 50000:
        logs = logs[-50000:]
    _write_json(CONV_LOG_PATH, logs)


def _log_event(event_type, payload):
    logs = _read_json(USER_LOG_PATH, [])
    logs.append({"event": event_type, "data": payload, "ts": datetime.datetime.utcnow().isoformat()})
    if len(logs) > 5000:
        logs = logs[-5000:]
    _write_json(USER_LOG_PATH, logs)


# Routes
@app.route("/", methods=["GET"])
def index():
    _init_gemini()
    return jsonify({"status": "ok", "model": _gemini_model_name or "unavailable", "revision": DEPLOYMENT_REVISION})


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


@app.route("/ai-query", methods=["POST"])
def ai_query():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    session_id = data.get("session_id") or "anonymous"
    context = data.get("context") or {}
    if not query:
        return jsonify({"answer": None, "escalate": True})

    _log_conversation(session_id, "user", query, context)

    kb = _load_kb()
    handoff_triggers = kb.get("human_handoff", {}).get("triggers", [])
    if any(t.lower() in query.lower() for t in handoff_triggers):
        msg = kb.get("human_handoff", {}).get("response", "Let me connect you to our human team.")
        _log_conversation(session_id, "assistant", msg, {})
        return jsonify({"answer": msg, "escalate": True, "actions": []})

    _init_gemini()
    system_prompt = _build_system_prompt()
    full_query = f"{system_prompt}\n\nUser: {query}"
    answer = None
    error_log = None
    provider_used = None
    
    # Try Gemini first
    if _gemini_model:
        try:
            response = _gemini_model.generate_content(model=_gemini_model_name, contents=full_query)
            answer = _extract_response_text(response)
            if not answer:
                raise ValueError("empty response from GenAI")
            _log_conversation(session_id, "assistant", answer, {})
            actions = []
            return jsonify({"answer": answer, "escalate": False, "actions": actions, "provider": "gemini"})
        except Exception as e:
            print(f"Gemini error: {e}")
            error_log = str(e)

    # Fallback to OpenAI if Gemini fails or is unavailable
    if OPENAI_API_KEY:
        openai_answer, openai_error = _call_openai(system_prompt, query)
        if openai_answer:
            _log_conversation(session_id, "assistant", openai_answer, {})
            return jsonify({"answer": openai_answer, "escalate": False, "actions": [], "provider": "openai"})
        else:
            error_log = f"Gemini failed: {error_log}; OpenAI failed: {openai_error}"

    # Fallback to Anthropic (Claude) if OpenAI fails or is unavailable
    if ANTHROPIC_API_KEY:
        anthropic_answer, anthropic_error = _call_anthropic(system_prompt, query)
        if anthropic_answer:
            _log_conversation(session_id, "assistant", anthropic_answer, {})
            return jsonify({"answer": anthropic_answer, "escalate": False, "actions": [], "provider": "anthropic"})
        else:
            error_log = f"Gemini failed: {error_log}; OpenAI failed: {openai_error}; Anthropic failed: {anthropic_error}"

    # If all providers fail, try knowledge-base fallback first
    kb_answer = _find_kb_response(query, kb)
    if kb_answer:
        _log_conversation(session_id, "assistant", kb_answer, {"fallback": True})
        return jsonify({"answer": kb_answer, "escalate": False, "actions": [], "provider": "kb_fallback"})

    fallbacks = kb.get("fallback_responses", DEFAULT_FALLBACKS)
    import random
    fallback_answer = random.choice(fallbacks)
    _log_conversation(session_id, "assistant", fallback_answer, {"fallback": True})
    return jsonify({"answer": fallback_answer, "escalate": True, "error_log": error_log or "No provider available", "provider": "kb_fallback"})


@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id") or "anonymous"
    products = _load_products()

    _init_gemini()
    if not _gemini_model:
        return jsonify({"recommendations": [], "message": "AI not configured."})

    product_list = "\n".join(f"{i+1}. {p.get('name','?')} | {p.get('category','')} | {p.get('price','')}" for i, p in enumerate(products))
    prompt = f"A customer wants furniture recommendations:\n\nProducts available:\n{product_list}\n\nReturn ONLY valid JSON — a list of exactly 3 objects." 
    try:
        response = _gemini_model.generate_content(model=_gemini_model_name, contents=prompt)
        raw = _extract_response_text(response)
        # extract JSON array
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            recs_raw = json.loads(raw[start : end + 1])
        else:
            recs_raw = []

        recommendations = []
        for rec in recs_raw:
            idx = int(rec.get("id", 0)) - 1
            if 0 <= idx < len(products):
                p = products[idx]
                recommendations.append({
                    "name": p.get("name", ""),
                    "price": p.get("price", ""),
                    "image": p.get("image", ""),
                    "category": p.get("category", ""),
                    "reason": rec.get("reason", ""),
                })

        _log_event("recommendation", {"session_id": session_id, "results": [r["name"] for r in recommendations]})
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        print(f"Recommend error: {e}")
        return jsonify({"recommendations": [], "message": "Could not generate recommendations."})


@app.route("/escalate", methods=["POST"])
def escalate():
    data = request.get_json(silent=True) or {}
    _log_event("escalation", data)
    return jsonify({"escalated": True})


@app.route("/kb", methods=["GET"])
def get_kb():
    return jsonify(_load_kb())


@app.route("/products", methods=["GET"])
def get_products():
    return jsonify(_load_products())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
