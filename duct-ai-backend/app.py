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
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

DEPLOYMENT_REVISION = '43c88de'

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '').strip()
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
OPENAI_URL = 'https://api.openai.com/v1/chat/completions'
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '').strip()
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
        gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            for model_name in ["gemini-1.5-flash", "gemini-1.5", "gemini-1.0"]:
                try:
                    _gemini_model = genai.GenerativeModel(model_name)
                    print(f"Gemini init: using model {model_name}")
                    break
                except Exception as model_error:
                    print(f"Gemini model init failed for {model_name}: {model_error}")
            if not _gemini_model:
                print("Gemini init error: no usable model could be initialized")
        else:
            _gemini_model = None
    except Exception as _e:
        print(f"Gemini init warning: {_e}")
        _gemini_model = None

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# Allow requests from your live domain AND localhost for development
CORS(app, resources={r"/*": {"origins": [
    "https://interiorductltd.com",
    "https://www.interiorductltd.com",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:3000",
]}})

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


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "duct-ai-backend",
        "model": "gemini-1.5-flash",
        "keySet": bool(os.environ.get("GEMINI_API_KEY")),
        "revision": DEPLOYMENT_REVISION,
    })


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


@app.route("/ai-query", methods=["POST"])
def ai_query():
    """
    Main chat endpoint.
    Body: { "query": "...", "session_id": "...", "context": {...} }
    Returns: { "answer": "...", "escalate": false, "actions": [...] }
    """
    data       = request.get_json(silent=True) or {}
    query      = (data.get("query") or "").strip()
    session_id = (data.get("session_id") or "anonymous")
    context    = data.get("context", {})   # optional: { page, product, scroll_pos }

    if not query:
        return jsonify({"answer": None, "escalate": True})

    # Log the query
    _log_conversation(session_id, "user", query, context)

    # Check human-handoff triggers first (no AI needed)
    kb = _load_kb()
    handoff_triggers = kb.get("human_handoff", {}).get("triggers", [])
    if any(t.lower() in query.lower() for t in handoff_triggers):
        handoff_msg = kb.get("human_handoff", {}).get("response",
            "Let me connect you to our human team. WhatsApp: +234 803 685 0229")
        _log_conversation(session_id, "assistant", handoff_msg, {})
        return jsonify({"answer": handoff_msg, "escalate": True, "actions": []})

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
    else:
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
        return jsonify({"answer": clean_answer, "escalate": False, "actions": actions, "provider": provider})

    if not answer and not _gemini_model and not OPENAI_API_KEY and not ANTHROPIC_API_KEY:
        error_log = error_log or "No AI provider configured. Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY."

    kb_answer = _find_kb_response(query, kb)
    if kb_answer:
        _log_conversation(session_id, "assistant", kb_answer, {"fallback": True})
        return jsonify({"answer": kb_answer, "escalate": False, "actions": [], "provider": "kb_fallback"})

    fallbacks = kb.get("fallback_responses", ["I’m sorry, I’m having trouble answering right now. Please try again in a moment or contact WhatsApp at +234 803 685 0229."])
    import random
    fallback_answer = random.choice(fallbacks)
    print(f"AI fallback triggered. provider={provider}, error_log={error_log}")
    _log_conversation(session_id, "assistant", fallback_answer, {"fallback": True})
    return jsonify({"answer": fallback_answer, "escalate": False, "provider": "fallback", "error_log": error_log or "No provider available"})


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
def analytics():
    """
    Basic analytics endpoint — returns conversation and feedback summary.
    Protected by a simple token check.
    """
    token = request.args.get("token","")
    if token != os.environ.get("ANALYTICS_TOKEN",""):
        return jsonify({"error": "Unauthorized"}), 401

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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
