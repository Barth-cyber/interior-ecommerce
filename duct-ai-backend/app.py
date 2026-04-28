"""
Duct AI Backend — Interior Duct Ltd
Serves: https://interiorductltd.com  (embedded chat widget)
Model:  Google Gemini 1.5 Flash
"""

import os
import json
import time
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

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
            _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
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
    "https://interior-ecommerce-lh3e.onrender.com",
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

    _init_gemini()
    if not _gemini_model:
        # Graceful fallback when API key not set or Gemini is unavailable
        fallbacks = kb.get("fallback_responses",
            ["I'm not available right now. Please WhatsApp +234 803 685 0229"])
        import random
        return jsonify({"answer": random.choice(fallbacks), "escalate": False})

    try:
        system_prompt = _build_system_prompt()
        history       = _get_history(session_id)

        # Build Gemini chat with history
        chat = _gemini_model.start_chat(history=history)

        # Prepend system prompt only on first message
        if not history:
            full_query = f"{system_prompt}\n\nUser: {query}"
        else:
            full_query = query

        response = chat.send_message(full_query)
        answer   = response.text.strip()

        # Save to history
        _save_to_history(session_id, "user",  query)
        _save_to_history(session_id, "model", answer)

        # Parse action directives embedded in answer
        actions = _extract_actions(answer)
        # Clean directives from visible answer text
        clean_answer = answer.replace("[SCROLL:", "").replace("[PRODUCT:", "")
        for a in actions:
            clean_answer = clean_answer.replace(a.get("raw", ""), "").strip()

        _log_conversation(session_id, "assistant", clean_answer, {})

        return jsonify({
            "answer":   clean_answer,
            "escalate": False,
            "actions":  actions,
        })

    except Exception as e:
        print(f"Gemini error: {e}")
        fallbacks = kb.get("fallback_responses", ["Sorry, something went wrong."])
        import random
        return jsonify({
            "answer":   random.choice(fallbacks),
            "escalate": False,
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
        response = _gemini_model.generate_content(prompt)
        raw      = response.text.strip().replace("```json","").replace("```","").strip()
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
