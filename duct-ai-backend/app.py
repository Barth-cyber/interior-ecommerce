"""
Duct AI Backend — Interior Duct Ltd
Serves: https://interiorductltd.com  (embedded chat widget)
Model:  Google Gemini 1.5 Flash
"""

import os
import json
import time
import datetime
from typing import Any, List, Optional
from flask import Flask, request, jsonify, send_from_directory
import requests
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# Explicit startup logging for Railway
_gemini_key_for_logging = os.environ.get("GOOGLE_GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
import sys
sys.stderr.write(f"[RAILWAY-INIT] GOOGLE_GEMINI_API_KEY present: {bool(os.environ.get('GOOGLE_GEMINI_API_KEY'))}\n")
sys.stderr.write(f"[RAILWAY-INIT] Any Gemini key present: {bool(_gemini_key_for_logging)}\n")

DEPLOYMENT_REVISION = 'gemini-2.0-fix-v2'


def _get_env_var(*names):
    for name in names:
        value = os.environ.get(name, "")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""

OPENAI_API_KEY = _get_env_var('OPENAI_API_KEY', 'OPENAI_KEY', 'OPENAI_API')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
OPENAI_URL = 'https://api.openai.com/v1/chat/completions'
ANTHROPIC_API_KEY = _get_env_var('ANTHROPIC_API_KEY', 'ANTHROPIC_KEY', 'ANTHROPIC_API')
ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'

# ── Gemini setup ──────────────────────────────────────────────────────────────
_gemini_model = None
_gemini_initialized = False


def _init_gemini():
    global _gemini_model, _gemini_initialized
    if _gemini_initialized:
        return
    _gemini_initialized = True
    try:
        import google.generativeai as genai
        gemini_api_key = _get_env_var("GOOGLE_GEMINI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY")
        import sys
        if gemini_api_key:
            # Log which variable name was used
            if os.environ.get("GOOGLE_GEMINI_API_KEY"):
                sys.stderr.write("[INIT] Using GOOGLE_GEMINI_API_KEY\n")
            elif os.environ.get("GEMINI_API_KEY"):
                sys.stderr.write("[INIT] Using GEMINI_API_KEY\n")
            elif os.environ.get("GOOGLE_API_KEY"):
                sys.stderr.write("[INIT] Using GOOGLE_API_KEY\n")
        sys.stderr.write(f"[DEBUG] Checking API keys: GOOGLE_GEMINI_API_KEY={bool(os.environ.get('GOOGLE_GEMINI_API_KEY'))}, GEMINI_API_KEY={bool(os.environ.get('GEMINI_API_KEY'))}, GOOGLE_API_KEY={bool(os.environ.get('GOOGLE_API_KEY'))}\n")
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            for model_name in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5"]:
                try:
                    _gemini_model = genai.GenerativeModel(model_name)
                    pass
                    break
                except Exception as model_error:
                    pass
            if not _gemini_model:
                pass
        else:
            _gemini_model = None
    except Exception as _e:
        pass
        _gemini_model = None

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=None)

# Log configuration on startup
def log_startup():
    gemini_key = _get_env_var("GOOGLE_GEMINI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY")
    key_name = "NONE"
    if os.environ.get("GOOGLE_GEMINI_API_KEY"):
        key_name = "GOOGLE_GEMINI_API_KEY"
    elif os.environ.get("GEMINI_API_KEY"):
        key_name = "GEMINI_API_KEY"
    elif os.environ.get("GOOGLE_API_KEY"):
        key_name = "GOOGLE_API_KEY"
    print(f"[STARTUP] Gemini API Key: {key_name} Available: {bool(gemini_key)}")

with app.app_context():
    log_startup()

# Allow requests from your live domain AND localhost for development
_ALLOWED_ORIGINS_RAW = os.environ.get("ALLOWED_ORIGINS", "https://interiorductltd.com,https://www.interiorductltd.com,http://localhost:5000,http://127.0.0.1:5000,http://localhost:3000")
if _ALLOWED_ORIGINS_RAW.strip() == "*":
    _CORS_ORIGINS = "*"
else:
    _CORS_ORIGINS = [o.strip() for o in _ALLOWED_ORIGINS_RAW.split(",") if o.strip()]

CORS(app, resources={r"/*": {"origins": _CORS_ORIGINS}})

# Simple in-memory rate limiter (per-IP, per-minute).
# Config: RATE_LIMIT_PER_MIN env var (default 120 requests/min)
_RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "120"))
_rate_state = {}
_rate_lock = __import__("threading").Lock()


@app.before_request
def enforce_rate_limit():
    # Skip rate limiting for health checks and static assets
    path = request.path or ""
    if path.startswith("/health") or path.startswith("/static"):
        return None

    # Identify client by forwarded header or remote_addr
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    try:
        now = int(time.time())
        window = 60
        with _rate_lock:
            state = _rate_state.get(ip)
            if not state or now - state.get("start", 0) >= window:
                # start new window
                _rate_state[ip] = {"count": 1, "start": now}
            else:
                state["count"] += 1
                if state["count"] > _RATE_LIMIT:
                    return jsonify({"error": "rate_limited", "limit": _RATE_LIMIT}), 429
    except Exception:
        # On any error, do not block the request; fail-open
        return None

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(__file__)
KB_PATH        = os.path.join(BASE_DIR, "knowledge_base.json")
PRODUCTS_PATH  = os.path.join(BASE_DIR, "products.json")
CONV_LOG_PATH  = os.path.join(BASE_DIR, "conversations.json")
USER_LOG_PATH  = os.path.join(BASE_DIR, "user_log.json")
FEEDBACK_PATH  = os.path.join(BASE_DIR, "feedback.json")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path, data):
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
    # Try products.json first, fall back to knowledge_base products key
    products = _read_json(PRODUCTS_PATH, None)
    if products is not None:
        return products
    kb = _load_kb()
    return kb.get("products", [])


def _render_context(context: dict) -> str:
    if not isinstance(context, dict):
        return ""
    parts = []
    if context.get("page"):
        parts.append(f"Page: {context['page']}")
    if context.get("product"):
        parts.append(f"Product: {context['product']}")
    if context.get("user_agent"):
        parts.append(f"User agent: {context['user_agent']}")
    return "\n".join(parts)


def _load_session_history(session_id: str) -> List[dict]:
    conversations = _read_json(CONV_LOG_PATH, [])
    return [item for item in conversations if item.get("session_id") == session_id][-20:]


def _render_session_history(history: List[dict]) -> str:
    if not history:
        return ""
    lines = []
    for entry in history:
        role = entry.get("role", "user")
        text = entry.get("text", "")
        if role and text:
            lines.append(f"{role.capitalize()}: {text}")
    return "\n".join(lines)


def _extract_response_text(response) -> str:
    if response is None:
        return ""
    if isinstance(response, str):
        return response.strip()
    if isinstance(response, dict):
        for key in ("text", "content", "message", "completion", "output_text", "response"):
            if key in response and isinstance(response[key], str) and response[key].strip():
                return response[key].strip()
        for key in ("choices", "candidates", "items", "messages"):
            if key in response:
                sub = response[key]
                if isinstance(sub, list) and sub:
                    return _extract_response_text(sub[0])
                if isinstance(sub, dict):
                    return _extract_response_text(sub)
        for value in response.values():
            text = _extract_response_text(value)
            if text:
                return text
        return ""
    if hasattr(response, "text") and isinstance(response.text, str) and response.text.strip():
        return response.text.strip()
    if hasattr(response, "content") and isinstance(response.content, str) and response.content.strip():
        return response.content.strip()
    if hasattr(response, "response") and isinstance(response.response, str) and response.response.strip():
        return response.response.strip()
    if hasattr(response, "candidates"):
        candidates = getattr(response, "candidates")
        if isinstance(candidates, list) and candidates:
            return _extract_response_text(candidates[0])
    return ""


def _call_openai(system_prompt, user_query):
    if not OPENAI_API_KEY:
        return None, "OpenAI API key not set"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.7,
    }
    try:
        resp = requests.post(OPENAI_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return _extract_response_text(resp.json()), None
    except Exception as e:
        return None, str(e)


def _call_anthropic(system_prompt, user_query):
    if not ANTHROPIC_API_KEY:
        return None, "Anthropic API key not set"
    headers = {
        "Authorization": f"Bearer {ANTHROPIC_API_KEY}",
        "Anthropic-Version": "2023-06-01",
        "Content-Type": "application/json"
    }
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_query}
        ]
    }
    try:
        resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return _extract_response_text(resp.json()), None
    except Exception as e:
        return None, str(e)


def _find_kb_response(query: str, kb: dict) -> Optional[str]:
    if not query:
        return None
    q = query.lower()
    for faq in kb.get("faqs", []):
        if faq.get("q", "").lower() in q or q in faq.get("q", "").lower():
            return faq.get("a")
    return None


def _build_system_prompt():
    """Build a rich system prompt from the knowledge base."""
    kb    = _load_kb()
    prods = _load_products()

    company = kb.get("company_info", {})
    contact = company.get("contact", {})
    faqs    = kb.get("faqs", [])

    faq_text = "\n".join(
        f"Q: {f['q']}\nA: {f['a']}" for f in faqs[:20]
    )

    product_list = "\n".join(
        f"- {p.get('name','?')} | {p.get('category','')} | "
        f"{p.get('price','')} | {p.get('description','')}"
        for p in prods[:30]
    )

    rec_prompts = kb.get("recommendation_engine_prompts", [])
    rec_text = "\n".join(
        f"Scenario: {r.get('scenario','')} → {r.get('response','')[:200]}"
        for r in rec_prompts[:5]
    )

    return f"""You are Duct AI, the intelligent luxury design assistant for Interior Duct Ltd.

== COMPANY ==
Name: {company.get('name','Interior Duct Ltd')}
Tagline: {company.get('tagline','Functionality, Durability & Aesthetics')}
Founder: {company.get('founder','Benedict Omoregbe Onaiwu')}
HQ: {company.get('headquarters','Benin City, Edo State, Nigeria')}
Showrooms: {', '.join(company.get('showrooms', ['Benin City','Abuja','Port Harcourt']))}
Delivery: {company.get('delivery_coverage','Nationwide across all 36 states')}
International: {company.get('international_presence','4 countries served')}
Experience: {company.get('experience','15+ years')}
Mission: {company.get('mission','')}

== CONTACT ==
Phone/WhatsApp: {contact.get('phone','+234 803 685 0229')}
Email: {contact.get('email_primary','hello@interiorductltd.com')}
Hours: {contact.get('business_hours','Mon-Sat 8am-6pm WAT')}

== PAYMENT ==
Nigeria: Paystack — bank transfer, USSD, card, mobile money (NGN ₦)
International: Stripe — Visa, Mastercard, Apple Pay, Google Pay (USD, GBP, EUR)
Security: TLS 1.3, 3D Secure, PCI-DSS Level 1

== PRODUCTS (sample) ==
{product_list}

== COMMON FAQs ==
{faq_text}

== RECOMMENDATION SCENARIOS ==
{rec_text}

== YOUR BEHAVIOUR RULES ==
1. Be warm, professional, and luxury-brand appropriate at all times.
2. Keep answers concise (2-4 sentences) unless detail is genuinely needed.
3. Never invent prices — reference the catalogue above or ask them to request a quote.
4. For custom orders, measurements, or site visits → invite WhatsApp: +234 803 685 0229
5. If the user wants a human, say you're connecting them and provide WhatsApp link.
6. If asked to show a category (sofas, tables, doors, etc.) respond with the category
   name in this format so the website can act on it: [SCROLL:section_name]
   Valid sections: seating, dining, doors, collection, bedroom, living, office, 3d-viewer
7. If you recommend specific products, format them as [PRODUCT:product_name] so the
   website can highlight them.
8. If payment is mentioned, explain both Paystack (NGN) and Stripe (international) options.
9. Always end responses that don't have a clear next step with a helpful follow-up question.
"""


# ── In-memory conversation store (per session_id) ─────────────────────────────
_sessions = {}   # { session_id: [{"role":..., "parts":[...]}, ...] }


def _get_history(session_id):
    return _sessions.get(session_id, [])


def _save_to_history(session_id, role, text):
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({"role": role, "parts": [text]})
    # Keep last 30 turns to avoid context overflow
    if len(_sessions[session_id]) > 30:
        _sessions[session_id] = _sessions[session_id][-30:]


def require_env_token(env_var_name: str):
    """Decorator to protect endpoints with a token stored in environment.
    Checks `X-API-KEY` header or `token` query param. If the env var is unset,
    the endpoint remains public to avoid breaking existing integrations.
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            expected = os.environ.get(env_var_name, "").strip()
            if not expected:
                return func(*args, **kwargs)
            token = request.headers.get("X-API-KEY") or request.args.get("token", "")
            if token != expected:
                return jsonify({"error": "Unauthorized"}), 401
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    html_file = os.path.join(BASE_DIR, "interior.html")
    if not os.path.isfile(html_file):
        return (
            "<h1>Interior Duct Ltd</h1><p>Welcome. The site is loading.</p>",
            200,
            {"Content-Type": "text/html; charset=utf-8"},
        )
    try:
        response = send_from_directory(BASE_DIR, "interior.html")
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response
    except Exception as e:
        return (
            f"<h1>Error</h1><p>Could not load interior.html: {e}</p>",
            500,
            {"Content-Type": "text/html; charset=utf-8"},
        )


@app.route("/debug", methods=["GET"])
def debug():
    summary = _validate_env()
    summary["allowed_origins"] = _ALLOWED_ORIGINS_RAW
    return jsonify(summary)


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


@app.route("/api/health", methods=["GET"])
def api_health():
    providers = {
        "gemini": bool(_get_env_var("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY")),
        "openai": bool(_get_env_var("OPENAI_API_KEY", "OPENAI_KEY", "OPENAI_API")),
        "anthropic": bool(_get_env_var("ANTHROPIC_API_KEY", "ANTHROPIC_KEY", "ANTHROPIC_API")),
    }
    return jsonify({
        "status": "ok",
        "service": "duct-ai-backend",
        "model": "gemini-1.5-flash",
        "ai_enabled": any(providers.values()),
        "providers": providers,
        "revision": DEPLOYMENT_REVISION,
        "allowed_origins": _ALLOWED_ORIGINS_RAW,
    })


@app.route("/ai-query", methods=["POST"])
def ai_query():
    """
    Main chat endpoint.
    Body: { "query": "...", "session_id": "...", "context": {...} }
    Returns: { "answer": "...", "escalate": false, "actions": [...] }
    """
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    session_id = (data.get("session_id") or "anonymous")
    context = data.get("context", {})

    result = process_query(query, session_id, context)
    return jsonify(result)


def process_query(query: str, session_id: str = "anonymous", context: dict = None) -> dict:
    """Core query processing extracted so other endpoints can reuse it.
    Returns a dict matching the old /ai-query JSON structure.
    """
    context = context or {}
    if not query:
        return {"answer": None, "escalate": True}

    _log_conversation(session_id, "user", query, context)

    kb = _load_kb()
    handoff_triggers = kb.get("human_handoff", {}).get("triggers", [])
    if any(t.lower() in query.lower() for t in handoff_triggers):
        handoff_msg = kb.get("human_handoff", {}).get("response",
            "Let me connect you to our human team. WhatsApp: +234 803 685 0229")
        _log_conversation(session_id, "assistant", handoff_msg, {})
        return {"answer": handoff_msg, "escalate": True, "actions": []}

    history = _load_session_history(session_id)
    session_text = _render_session_history(history)
    context_text = _render_context(context)

    _init_gemini()
    system_prompt = _build_system_prompt()
    if session_text:
        system_prompt += f"\n\nConversation history:\n{session_text}"
    if context_text:
        system_prompt += f"\n\nRequest context:\n{context_text}"
    full_query = f"{system_prompt}\n\nUser: {query}"

    answer = None
    error_log = None
    provider = None

    if _gemini_model:
        try:
            if hasattr(_gemini_model, "generate_text"):
                response = _gemini_model.generate_text(full_query)
            else:
                response = _gemini_model.generate_content(full_query)
            answer = _extract_response_text(response)
            if not answer:
                raise ValueError("empty response from Gemini")
            provider = "gemini"
        except Exception as gen_error:
            print(f"Gemini error: {gen_error}")
            error_log = str(gen_error)
            answer = None
            provider = None

    if not answer and OPENAI_API_KEY:
        openai_answer, openai_error = _call_openai(system_prompt, query)
        if openai_answer:
            answer = openai_answer
            provider = "openai"
        else:
            error_log = f"{error_log or 'Gemini unavailable'}; OpenAI error: {openai_error}"

    if not answer and ANTHROPIC_API_KEY:
        anthropic_answer, anthropic_error = _call_anthropic(system_prompt, query)
        if anthropic_answer:
            answer = anthropic_answer
            provider = "anthropic"
        else:
            error_log = f"{error_log or 'Gemini/OpenAI unavailable'}; Anthropic error: {anthropic_error}"

    if answer:
        _save_to_history(session_id, "user", query)
        _save_to_history(session_id, "assistant", answer)
        actions = _extract_actions(answer)
        clean_answer = answer
        for a in actions:
            clean_answer = clean_answer.replace(a.get("raw", ""), "").strip()
        _log_conversation(session_id, "assistant", clean_answer, {"provider": provider})
        return {"answer": clean_answer, "escalate": False, "actions": actions, "provider": provider}

    if not answer and not _gemini_model and not OPENAI_API_KEY and not ANTHROPIC_API_KEY:
        error_log = error_log or "No AI provider configured. Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY."

    kb_answer = _find_kb_response(query, kb)
    if kb_answer:
        _log_conversation(session_id, "assistant", kb_answer, {"fallback": True})
        return {"answer": kb_answer, "escalate": False, "actions": [], "provider": "kb_fallback"}

    fallbacks = kb.get("fallback_responses", ["I’m sorry, I’m having trouble answering right now. Please try again in a moment or contact WhatsApp at +234 803 685 0229."])
    import random
    fallback_answer = random.choice(fallbacks)
    print(f"AI fallback triggered. provider={provider}, error_log={error_log}")
    _log_conversation(session_id, "assistant", fallback_answer, {"fallback": True})
    return {"answer": fallback_answer, "escalate": False, "provider": "fallback", "error_log": error_log or "No provider available"}


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Compatibility adapter for frontend widget.
    Accepts either OpenAI-style `{ messages: [{role,content}, ...] }` or `{ query: '...' }`.
    Returns `{ reply: '...' , actions: [...], provider: '...' }` to match widget expectations.
    """
    data = request.get_json(silent=True) or {}

    # support OpenAI-like messages array
    query = ""
    if isinstance(data.get("messages"), list):
        msgs = data.get("messages")
        user_msgs = [m for m in msgs if str(m.get("role","") ).lower() == "user"]
        if user_msgs:
            query = (user_msgs[-1].get("content") or "").strip()
    if not query:
        query = (data.get("query") or "").strip()

    session_id = data.get("session_id", data.get("session", "anonymous")) or "anonymous"
    context = data.get("context", {})

    result = process_query(query, session_id, context)
    # normalize for frontend
    return jsonify({
        "reply": result.get("answer"),
        "actions": result.get("actions", []),
        "provider": result.get("provider"),
        "escalate": result.get("escalate", False),
    })


def _extract_actions(text):
    """Parse [SCROLL:section] and [PRODUCT:name] directives from AI response."""
    import re
    actions = []
    for m in re.finditer(r'\[SCROLL:(\w[\w-]*)\]', text):
        actions.append({"type": "scroll", "target": m.group(1), "raw": m.group(0)})
    for m in re.finditer(r'\[PRODUCT:([^\]]+)\]', text):
        actions.append({"type": "highlight_product", "name": m.group(1), "raw": m.group(0)})
    return actions


@app.route("/recommend", methods=["POST"])
def recommend():
    """
    AI product recommendation.
    Body: { "preferences": "...", "budget": "...", "room": "...", "session_id": "..." }
    """
    data        = request.get_json(silent=True) or {}
    preferences = data.get("preferences", "")
    budget      = data.get("budget", "")
    room        = data.get("room", "")
    session_id  = data.get("session_id", "anonymous")

    products = _load_products()
    product_list = "\n".join(
        f"{i+1}. {p.get('name','?')} | {p.get('category','')} | "
        f"{p.get('price','')} | {p.get('description','')}"
        for i, p in enumerate(products)
    )

    _init_gemini()
    if not _gemini_model:
        return jsonify({"recommendations": [], "message": "AI not configured."})

    prompt = f"""A customer wants furniture recommendations:
- Room: {room or 'not specified'}
- Budget: {budget or 'not specified'}
- Style/preferences: {preferences or 'not specified'}

Products available:
{product_list}

Return ONLY valid JSON — a list of exactly 3 objects:
[{{"id": <1-based index>, "name": "<product name>", "reason": "<one sentence>"}}]
No markdown, no explanation, just the JSON array."""

    try:
        if hasattr(_gemini_model, "generate_text"):
            response = _gemini_model.generate_text(prompt)
        else:
            response = _gemini_model.generate_content(prompt)
        raw = _extract_response_text(response).replace("```json", "").replace("```", "").strip()
        recs_raw = json.loads(raw)

        recommendations = []
        for rec in recs_raw:
            idx = int(rec.get("id", 0)) - 1
            if 0 <= idx < len(products):
                p = products[idx]
                recommendations.append({
                    "name":     p.get("name",""),
                    "price":    p.get("price",""),
                    "image":    p.get("image",""),
                    "category": p.get("category",""),
                    "reason":   rec.get("reason",""),
                })

        _log_event("recommendation", {
            "session_id": session_id,
            "room": room, "budget": budget,
            "results": [r["name"] for r in recommendations],
        })

        return jsonify({"recommendations": recommendations})

    except Exception as e:
        print(f"Recommend error: {e}")
        return jsonify({"recommendations": [], "message": "Could not generate recommendations."})


@app.route("/escalate", methods=["POST"])
def escalate():
    """Log escalation events (user wants human agent)."""
    data = request.get_json(silent=True) or {}
    _log_event("escalation", data)
    return jsonify({"escalated": True})


@app.route("/user-log", methods=["POST"])
def user_log():
    """Log user behaviour events (page views, product clicks, etc.)."""
    data = request.get_json(silent=True) or {}
    logs = _read_json(USER_LOG_PATH, [])
    logs.append({**data, "ts": int(time.time())})
    if len(logs) > 5000:
        logs = logs[-5000:]
    _write_json(USER_LOG_PATH, logs)
    return jsonify({"logged": True})


@app.route("/feedback", methods=["POST"])
def feedback():
    """
    Receive thumbs-up/thumbs-down on AI answers for self-improvement.
    Body: { "query": "...", "answer": "...", "rating": 1|-1, "session_id": "..." }
    """
    data = request.get_json(silent=True) or {}
    feedbacks = _read_json(FEEDBACK_PATH, [])
    feedbacks.append({
        "query":      data.get("query",""),
        "answer":     data.get("answer",""),
        "rating":     data.get("rating", 0),   # 1=good, -1=bad
        "comment":    data.get("comment",""),
        "session_id": data.get("session_id",""),
        "ts":         datetime.datetime.utcnow().isoformat(),
    })
    if len(feedbacks) > 10000:
        feedbacks = feedbacks[-10000:]
    _write_json(FEEDBACK_PATH, feedbacks)
    return jsonify({"saved": True})


@app.route("/analytics", methods=["GET"])
@require_env_token("ANALYTICS_TOKEN")
def analytics():
    """
    Basic analytics endpoint — returns conversation and feedback summary.
    Protection is provided by `ANALYTICS_TOKEN` (header `X-API-KEY` or query `token`).
    If `ANALYTICS_TOKEN` is not set the endpoint is public.
    """

    logs     = _read_json(CONV_LOG_PATH, [])
    feedback = _read_json(FEEDBACK_PATH, [])
    ulogs    = _read_json(USER_LOG_PATH, [])

    total_convs    = len(logs)
    user_msgs      = [l for l in logs if l.get("role") == "user"]
    positive_fb    = sum(1 for f in feedback if f.get("rating",0) > 0)
    negative_fb    = sum(1 for f in feedback if f.get("rating",0) < 0)

    # Most asked queries (simple frequency count)
    from collections import Counter
    query_counts = Counter(
        l.get("text","").lower()[:60]
        for l in user_msgs
    )

    return jsonify({
        "total_messages":    total_convs,
        "user_messages":     len(user_msgs),
        "unique_sessions":   len({l.get("session_id") for l in logs}),
        "positive_feedback": positive_fb,
        "negative_feedback": negative_fb,
        "behaviour_events":  len(ulogs),
        "top_queries":       query_counts.most_common(10),
    })


@app.route("/kb", methods=["GET"])
def get_kb():
    """Return the knowledge base (public, no auth — used by frontend)."""
    return jsonify(_load_kb())


@app.route("/products", methods=["GET"])
def get_products():
    """Return product list."""
    return jsonify(_load_products())


# ── Internal helpers ──────────────────────────────────────────────────────────

def _log_conversation(session_id, role, text, context):
    logs = _read_json(CONV_LOG_PATH, [])
    logs.append({
        "session_id": session_id,
        "role":       role,
        "text":       text,
        "context":    context,
        "ts":         datetime.datetime.utcnow().isoformat(),
    })
    if len(logs) > 50000:
        logs = logs[-50000:]
    _write_json(CONV_LOG_PATH, logs)


def _log_event(event_type, payload):
    logs = _read_json(USER_LOG_PATH, [])
    logs.append({
        "event": event_type,
        "data":  payload,
        "ts":    datetime.datetime.utcnow().isoformat(),
    })
    if len(logs) > 5000:
        logs = logs[-5000:]
    _write_json(USER_LOG_PATH, logs)


def _validate_env():
    """Check which AI providers and key configs are available and print a startup summary."""
    providers = {
        "gemini": bool(_get_env_var("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY")),
        "openai": bool(_get_env_var("OPENAI_API_KEY", "OPENAI_KEY", "OPENAI_API")),
        "anthropic": bool(_get_env_var("ANTHROPIC_API_KEY", "ANTHROPIC_KEY", "ANTHROPIC_API")),
    }
    analytics_token = bool(os.environ.get("ANALYTICS_TOKEN", "").strip())
    config_token = bool(os.environ.get("CONFIG_TOKEN", "").strip())
    print("--- Duct AI startup configuration ---")
    print(f"Allowed CORS origins: {_ALLOWED_ORIGINS_RAW}")
    print(f"Providers configured: {', '.join([k for k,v in providers.items() if v]) or 'none'}")
    print(f"Gemini env vars: {'yes' if _get_env_var('GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_GEMINI_API_KEY') else 'no'}")
    print(f"OpenAI env vars: {'yes' if _get_env_var('OPENAI_API_KEY', 'OPENAI_KEY', 'OPENAI_API') else 'no'}")
    print(f"Anthropic env vars: {'yes' if _get_env_var('ANTHROPIC_API_KEY', 'ANTHROPIC_KEY', 'ANTHROPIC_API') else 'no'}")
    print(f"Analytics token present: {analytics_token}")
    print(f"Config endpoint protected by token: {config_token}")
    if not any(providers.values()):
        print("WARNING: No AI providers configured. Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY.")
    return {**providers, "analytics": analytics_token, "config_token": config_token}


def require_env_token(env_var_name: str):
    """Decorator to protect endpoints with a token stored in environment.
    Checks `X-API-KEY` header or `token` query param. If the env var is unset,
    the endpoint remains public to avoid breaking existing integrations.
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            expected = os.environ.get(env_var_name, "").strip()
            if not expected:
                return func(*args, **kwargs)
            token = request.headers.get("X-API-KEY") or request.args.get("token", "")
            if token != expected:
                return jsonify({"error": "Unauthorized"}), 401
            return func(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/config", methods=["GET"])
@require_env_token("CONFIG_TOKEN")
def get_config():
    """Return non-sensitive config summary. Protected by CONFIG_TOKEN env var if set."""
    # kept for backward compatibility; protection now applied by decorator
    summary = _validate_env()
    summary["allowed_origins"] = _ALLOWED_ORIGINS_RAW
    return jsonify(summary)


def require_env_token(env_var_name: str):
    """Decorator to protect endpoints with a token stored in environment.
    Checks `X-API-KEY` header or `token` query param. If the env var is unset,
    the endpoint remains public to avoid breaking existing integrations.
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            expected = os.environ.get(env_var_name, "").strip()
            if not expected:
                return func(*args, **kwargs)
            token = request.headers.get("X-API-KEY") or request.args.get("token", "")
            if token != expected:
                return jsonify({"error": "Unauthorized"}), 401
            return func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
