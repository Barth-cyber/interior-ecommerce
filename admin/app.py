from flask import Flask, request, redirect, url_for, send_from_directory, jsonify, session
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from dotenv import load_dotenv
import os
import json
import difflib
import requests as http_requests

# Load environment variables from .env file
load_dotenv()

# Import S3 storage
try:
    from s3_storage import init_s3
    s3_storage = init_s3()
except Exception as e:
    print(f"S3 initialization warning: {e}")
    s3_storage = None

app = Flask(__name__, static_folder=None)
CORS(app)
app.config.update({
    'SECRET_KEY': os.environ.get('ADMIN_SECRET_KEY', 'change-me-in-production'),
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'SESSION_COOKIE_SECURE': os.environ.get('ADMIN_COOKIE_SECURE', 'False').lower() == 'true',
})

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.environ.get(
    'ADMIN_PASSWORD_HASH',
    'scrypt:32768:8:1$yqcKe3f2fiH8izeD$e4d9d627698e8f6d14d569375589c1f2d7236e3ec875e0c9ded18542bbcd72b58853c8b187696d3d0d49b2e39d6501a43ce8469303dbb085ad34ec574382d74d'
)

# Fallback local upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'IDL_Product_branding')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_3D = {'glb', 'gltf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CONTENT_PATH = os.path.join(os.path.dirname(__file__), 'content.json')
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IDL_BRANDING_DIR = os.path.join(ROOT_DIR, 'IDL_Product_branding')
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), 'categories.json')
KB_PATH = os.path.join(os.path.dirname(__file__), 'knowledge_base.json')
USER_LOG_PATH = os.path.join(os.path.dirname(__file__), 'user_log.json')

# ── Payment gateway config ───────────────────────────────────────────────────
PAYSTACK_SECRET_KEY    = os.environ.get('PAYSTACK_SECRET_KEY', '')
STRIPE_SECRET_KEY      = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
PAYSTACK_PUBLIC_KEY    = os.environ.get('PAYSTACK_PUBLIC_KEY', '')

# ── Google Gemini AI config ──────────────────────────────────────────────────
# Free tier: 1,500 requests/day  |  get key at https://aistudio.google.com/apikey
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
# Using gemini-1.5-flash — fastest, free-tier supported model
GEMINI_MODEL   = 'gemini-1.5-flash'
GEMINI_URL     = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'


# Ensure GEMINI_API_KEY is set
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY is not set. Please configure it in the environment variables.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
# Auth routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/login')
def login():
    if session.get('logged_in'):
        return redirect(url_for('admin'))
    return send_from_directory('.', 'login.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password or ''):
        session['logged_in'] = True
        return jsonify({'logged_in': True})
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/login', methods=['POST'])
def do_login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password or ''):
        session['logged_in'] = True
        return redirect(url_for('admin'))
    return redirect(url_for('login') + '?error=1')


@app.route('/api/session')
def api_session():
    return jsonify({'logged_in': bool(session.get('logged_in'))})


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('logged_in', None)
    if request.method == 'POST':
        return jsonify({'logged_out': True})
    return redirect(url_for('home'))


# ─────────────────────────────────────────────────────────────────────────────
# Page routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/admin-auth.js')
def admin_auth_js():
    return send_from_directory('.', 'admin-auth.js')


@app.route('/admin/')
@login_required
def admin_slash():
    return redirect(url_for('admin'))


@app.route('/admin')
@login_required
def admin():
    return send_from_directory('.', 'index.html')


@app.route('/')
def home():
    return send_from_directory('..', 'interior.html')


@app.route('/interior.html')
def interior():
    return send_from_directory('..', 'interior.html')


@app.route('/hero-popup-slider.js')
def hero_popup_slider_js():
    return send_from_directory(ROOT_DIR, 'hero-popup-slider.js')


@app.route('/duct-ai-assistant.js')
def duct_ai_assistant_js():
    return send_from_directory(ROOT_DIR, 'duct-ai-assistant.js')


@app.route('/IDL_Product_branding/<path:filename>')
def idl_product_branding(filename):
    return send_from_directory(IDL_BRANDING_DIR, filename)


@app.route('/admin.css')
def admin_css():
    return send_from_directory('.', 'admin.css')


@app.route('/admin.js')
def admin_js():
    return send_from_directory('.', 'admin.js')


@app.route('/3d-demo')
def three_d_demo():
    return send_from_directory('.', '3d-demo.html')


@app.route('/categories.html')
def categories_html():
    return send_from_directory('.', 'categories.html')


@app.route('/faq_manager.js')
def faq_manager_js():
    return send_from_directory('.', 'faq_manager.js')


# ─────────────────────────────────────────────────────────────────────────────
# Image / model management
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/images')
@login_required
def list_images():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
    files.sort()
    return jsonify(files)


@app.route('/public-images')
def public_images():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
    files.sort()
    return jsonify(files)


@app.route('/3dmodels')
@login_required
def list_3dmodels():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if '.' in f and f.rsplit('.', 1)[1].lower() in ALLOWED_3D]
    files.sort()
    return jsonify(files)


@app.route('/upload', methods=['POST'])
@login_required
def upload_image():
    if 'images' not in request.files:
        return 'No file part', 400
    files = request.files.getlist('images')
    saved = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if s3_storage:
                try:
                    url = s3_storage.upload_file(file, filename, 'images/')
                    saved.append({'filename': filename, 'url': url, 'storage': 'S3'})
                except Exception as e:
                    app.logger.error(f"S3 upload failed: {e}, using local storage")
                    file.seek(0)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    saved.append({'filename': filename, 'storage': 'local'})
            else:
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                saved.append({'filename': filename, 'storage': 'local'})
    return jsonify({'uploaded': saved})


@app.route('/upload-model', methods=['POST'])
@login_required
def upload_model():
    if 'models' not in request.files:
        return 'No file part', 400
    files = request.files.getlist('models')
    saved = []
    for file in files:
        if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_3D:
            filename = secure_filename(file.filename)
            if s3_storage:
                try:
                    url = s3_storage.upload_file(file, filename, 'models/')
                    saved.append({'filename': filename, 'url': url, 'storage': 'S3'})
                except Exception as e:
                    app.logger.error(f"S3 model upload failed: {e}, using local storage")
                    file.seek(0)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    saved.append({'filename': filename, 'storage': 'local'})
            else:
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                saved.append({'filename': filename, 'storage': 'local'})
    return jsonify({'uploaded': saved})


@app.route('/delete', methods=['POST'])
@login_required
def delete_image():
    data = request.get_json()
    filename = data.get('filename')
    if not filename or not allowed_file(filename):
        return 'Invalid filename', 400
    if s3_storage:
        try:
            s3_storage.delete_file(filename, 'images/')
        except Exception as e:
            app.logger.error(f"S3 delete failed: {e}")
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
    return jsonify({'deleted': filename})


@app.route('/delete-model', methods=['POST'])
@login_required
def delete_model():
    data = request.get_json()
    filename = data.get('filename')
    if not filename or '.' not in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_3D:
        return 'Invalid filename', 400
    if s3_storage:
        try:
            s3_storage.delete_file(filename, 'models/')
        except Exception as e:
            app.logger.error(f"S3 delete failed: {e}")
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
    return jsonify({'deleted': filename})


@app.route('/idl-images/<filename>')
def serve_image(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_EXTENSIONS and ext not in ALLOWED_3D:
        return 'Invalid file', 400
    return send_from_directory(UPLOAD_FOLDER, filename)


# ─────────────────────────────────────────────────────────────────────────────
# Content / categories / knowledge base
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/content', methods=['GET'])
def get_content():
    if not os.path.exists(CONTENT_PATH):
        return jsonify({})
    with open(CONTENT_PATH, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/content', methods=['POST'])
@login_required
def save_content():
    data = request.get_json()
    if not isinstance(data, dict):
        return 'Invalid content', 400
    with open(CONTENT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'saved': True})


@app.route('/categories', methods=['GET'])
def get_categories():
    if not os.path.exists(CATEGORIES_PATH):
        return jsonify({})
    with open(CATEGORIES_PATH, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/categories', methods=['POST'])
def save_categories():
    data = request.get_json()
    if not isinstance(data, dict):
        return 'Invalid categories', 400
    with open(CATEGORIES_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'saved': True})


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'static'), filename)


@app.route('/admin/content.json')
@login_required
def admin_content():
    return get_content()


@app.route('/kb', methods=['GET'])
def get_kb():
    if not os.path.exists(KB_PATH):
        return jsonify({})
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/kb', methods=['POST'])
def save_kb():
    data = request.get_json()
    if not isinstance(data, dict):
        return 'Invalid knowledge base', 400
    with open(KB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'saved': True})


# ─────────────────────────────────────────────────────────────────────────────
# AI helpers — Google Gemini (FREE tier: 1,500 req/day, no credit card needed)
# Docs: https://ai.google.dev/gemini-api/docs
# Get your free API key: https://aistudio.google.com/apikey
# ─────────────────────────────────────────────────────────────────────────────

def _load_kb():
    if not os.path.exists(KB_PATH):
        return {}
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _load_products():
    if not os.path.exists(CONTENT_PATH):
        return []
    with open(CONTENT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('products', [])


def _fuzzy_kb_match(query, kb):
    """Fast local fallback: try FAQ fuzzy match before calling Gemini API."""
    faqs = kb.get('faqs', [])
    questions = [faq['q'] for faq in faqs]
    if not questions:
        return None
    matches = difflib.get_close_matches(query.lower(), [q.lower() for q in questions], n=1, cutoff=0.65)
    if matches:
        for faq in faqs:
            if faq['q'].lower() == matches[0]:
                return faq['a']
    for faq in faqs:
        if faq['q'].lower() in query.lower() or query.lower() in faq['q'].lower():
            return faq['a']
    return None


def _call_gemini(prompt_text, system_instruction=None, max_tokens=512):
    """
    Call the Google Gemini API (gemini-1.5-flash).
    Free tier: 1,500 requests/day, 1 million tokens/day.
    Returns (answer_text, error_bool).
    """
    if not GEMINI_API_KEY:
        return None, True

    # Build request body
    body = {
        'contents': [
            {'role': 'user', 'parts': [{'text': prompt_text}]}
        ],
        'generationConfig': {
            'maxOutputTokens': max_tokens,
            'temperature': 0.7,
        },
    }

    # Gemini 1.5 supports system instructions
    if system_instruction:
        body['systemInstruction'] = {
            'parts': [{'text': system_instruction}]
        }

    try:
        response = http_requests.post(
            GEMINI_URL,
            params={'key': GEMINI_API_KEY},
            headers={'Content-Type': 'application/json'},
            json=body,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        # Extract text from Gemini response structure
        answer = data['candidates'][0]['content']['parts'][0]['text'].strip()
        return answer, False
    except Exception as e:
        app.logger.error(f"Gemini API error: {e}")
        return None, True


def _ask_gemini_chat(query, kb, products):
    """Call Gemini API for intelligent AI chat responses."""
    product_summary = "\n".join(
        f"- {p['name']} | {p.get('category','')} | {p.get('price','')} | {p.get('description','')}"
        for p in products[:30]
    )

    company_info = kb.get('company_info', {})
    system_instruction = f"""You are Duct AI, the intelligent virtual design assistant for Interior Duct Ltd — a premium luxury furniture and interior solutions company based in Benin City, Nigeria.

COMPANY:
- Name: {company_info.get('name', 'Interior Duct Ltd')}
- Tagline: {company_info.get('tagline', 'Functionality, Durability & Aesthetics')}
- Founder: {company_info.get('founder', 'Benedict Omoregbe Onaiwu')}
- Phone: {company_info.get('contact', {}).get('phone', '+234 803 685 0229')}
- Email: {company_info.get('contact', {}).get('email_primary', 'hello@interiorductltd.com')}
- Hours: {company_info.get('contact', {}).get('business_hours', 'Mon-Sat 8am-6pm WAT')}
- Showrooms: Benin City, Abuja, Port Harcourt
- Experience: 15+ years, 1,200+ bespoke pieces made

PRODUCT CATALOGUE (sample):
{product_summary}

PAYMENT OPTIONS:
- Nigeria: Paystack — bank transfer, USSD, card, mobile money (NGN)
- International: Stripe — Visa, Mastercard, Apple Pay, Google Pay (USD, GBP, EUR)
- All transactions are TLS 1.3 encrypted with 3D Secure

YOUR ROLE:
- Help customers browse furniture, get quotes, design advice, and product recommendations
- Be warm, professional, and knowledgeable about interior design
- For custom orders or showroom visits, invite them to WhatsApp: +234 803 685 0229
- Keep answers concise (2-4 sentences unless more detail is needed)
- Do NOT make up prices — reference the catalogue or invite them to request a quote
- If you cannot help, say so honestly and offer to connect them to the human team"""

    return _call_gemini(query, system_instruction=system_instruction, max_tokens=512)


# ─────────────────────────────────────────────────────────────────────────────
# AI Chat endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/ai-query', methods=['POST'])
def ai_query():
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'answer': None, 'escalate': True})

    kb = _load_kb()
    products = _load_products()

    # 1. Try fast local fuzzy match first (no API cost)
    local_answer = _fuzzy_kb_match(query, kb)
    if local_answer:
        return jsonify({'answer': local_answer, 'escalate': False})

    # 2. Call Gemini API
    answer, escalate = _ask_gemini_chat(query, kb, products)
    if answer:
        return jsonify({'answer': answer, 'escalate': False})

    # 3. Escalate to human
    return jsonify({'answer': None, 'escalate': escalate})


@app.route('/escalate', methods=['POST'])
def escalate():
    data = request.get_json()
    return jsonify({'escalated': True, 'payload': data})


@app.route('/user-log', methods=['GET'])
@login_required
def get_user_log():
    if not os.path.exists(USER_LOG_PATH):
        return jsonify([])
    with open(USER_LOG_PATH, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/user-log', methods=['POST'])
def user_log():
    data = request.get_json()
    logs = []
    if os.path.exists(USER_LOG_PATH):
        with open(USER_LOG_PATH, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    logs.append(data)
    with open(USER_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
    return jsonify({'logged': True})


# ─────────────────────────────────────────────────────────────────────────────
# Product Recommender — Gemini API
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.get_json() or {}
    preferences = data.get('preferences', '')
    budget = data.get('budget', '')
    room = data.get('room', '')

    if not GEMINI_API_KEY:
        return jsonify({'recommendations': [], 'message': 'AI recommendations not configured.'})

    products = _load_products()
    product_list = "\n".join(
        f"{i+1}. {p['name']} | {p.get('category','')} | {p.get('price','')} | {p.get('description','')}"
        for i, p in enumerate(products)
    )

    prompt = f"""A customer is shopping for furniture with these preferences:
- Room: {room or 'not specified'}
- Budget: {budget or 'not specified'}
- Style/preferences: {preferences or 'not specified'}

Available products:
{product_list}

Recommend the top 3 most suitable products. Return ONLY a JSON array like:
[{{"id": <product_number>, "reason": "<one sentence why>"}}]
No other text, no markdown, no code fences."""

    raw, error = _call_gemini(prompt, max_tokens=300)

    if error or not raw:
        return jsonify({'recommendations': [], 'message': 'Could not generate recommendations right now.'})

    try:
        # Strip any accidental markdown fences
        clean = raw.replace('```json', '').replace('```', '').strip()
        recs_idx = json.loads(clean)
        recommendations = []
        for rec in recs_idx:
            idx = rec.get('id', 0) - 1
            if 0 <= idx < len(products):
                p = products[idx]
                recommendations.append({
                    'name': p['name'],
                    'price': p.get('price', ''),
                    'image': p.get('image', ''),
                    'category': p.get('category', ''),
                    'reason': rec.get('reason', ''),
                })
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        app.logger.error(f"Recommend parse error: {e} | raw: {raw}")
        return jsonify({'recommendations': [], 'message': 'Could not parse recommendations.'})


# ─────────────────────────────────────────────────────────────────────────────
# Payment config endpoint (public keys only — safe to expose)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/payment-config')
def payment_config():
    return jsonify({
        'paystack_public_key': PAYSTACK_PUBLIC_KEY,
        'stripe_publishable_key': STRIPE_PUBLISHABLE_KEY,
    })


# ─────────────────────────────────────────────────────────────────────────────
# PAYSTACK — Nigeria (NGN)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/paystack/initialize', methods=['POST'])
def paystack_initialize():
    """Initialize a Paystack transaction and return the authorization URL."""
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    amount_naira = data.get('amount')
    product_name = data.get('product_name', 'Interior Duct Order')
    callback_url = data.get('callback_url', request.host_url + 'payment/verify')

    if not email or not amount_naira:
        return jsonify({'error': 'email and amount are required'}), 400

    if not PAYSTACK_SECRET_KEY:
        return jsonify({'error': 'Paystack not configured on server'}), 500

    amount_kobo = int(float(amount_naira) * 100)

    try:
        resp = http_requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers={
                'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'email': email,
                'amount': amount_kobo,
                'currency': 'NGN',
                'callback_url': callback_url,
                'metadata': {
                    'product_name': product_name,
                    'custom_fields': [
                        {'display_name': 'Product', 'variable_name': 'product', 'value': product_name}
                    ]
                },
            },
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get('status'):
            return jsonify({
                'authorization_url': result['data']['authorization_url'],
                'access_code': result['data']['access_code'],
                'reference': result['data']['reference'],
            })
        return jsonify({'error': result.get('message', 'Paystack error')}), 400
    except Exception as e:
        app.logger.error(f"Paystack initialize error: {e}")
        return jsonify({'error': 'Payment initialization failed. Please try again.'}), 500


@app.route('/api/paystack/verify', methods=['POST'])
def paystack_verify():
    """Verify a Paystack transaction by reference."""
    data = request.get_json() or {}
    reference = data.get('reference', '').strip()

    if not reference:
        return jsonify({'error': 'reference is required'}), 400

    if not PAYSTACK_SECRET_KEY:
        return jsonify({'error': 'Paystack not configured on server'}), 500

    try:
        resp = http_requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers={'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'},
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get('status') and result['data'].get('status') == 'success':
            return jsonify({
                'verified': True,
                'amount': result['data']['amount'] / 100,
                'currency': result['data']['currency'],
                'email': result['data']['customer']['email'],
                'reference': reference,
                'paid_at': result['data'].get('paid_at'),
            })
        return jsonify({'verified': False, 'message': result.get('message', 'Payment not successful')}), 400
    except Exception as e:
        app.logger.error(f"Paystack verify error: {e}")
        return jsonify({'error': 'Verification failed. Please contact support.'}), 500


@app.route('/payment/verify')
def payment_verify_callback():
    """Paystack redirect callback after payment."""
    reference = request.args.get('reference', '')
    if reference:
        return send_from_directory('..', 'interior.html')
    return redirect('/')


# ─────────────────────────────────────────────────────────────────────────────
# STRIPE — International (USD / GBP / EUR)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/stripe/create-payment-intent', methods=['POST'])
def stripe_create_payment_intent():
    """Create a Stripe PaymentIntent and return the client secret."""
    import stripe as stripe_lib
    stripe_lib.api_key = STRIPE_SECRET_KEY

    data = request.get_json() or {}
    amount = data.get('amount')
    currency = data.get('currency', 'usd').lower()
    product_name = data.get('product_name', 'Interior Duct Order')
    customer_email = data.get('email', '')

    if not amount:
        return jsonify({'error': 'amount is required'}), 400

    if not STRIPE_SECRET_KEY:
        return jsonify({'error': 'Stripe not configured on server'}), 500

    try:
        amount_int = int(float(amount) * 100)
        intent_params = {
            'amount': amount_int,
            'currency': currency,
            'automatic_payment_methods': {'enabled': True},
            'metadata': {'product_name': product_name},
        }
        if customer_email:
            intent_params['receipt_email'] = customer_email

        intent = stripe_lib.PaymentIntent.create(**intent_params)
        return jsonify({'client_secret': intent.client_secret, 'payment_intent_id': intent.id})
    except Exception as e:
        app.logger.error(f"Stripe create intent error: {e}")
        return jsonify({'error': 'Payment setup failed. Please try again.'}), 500


@app.route('/api/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Stripe webhook for payment confirmation events."""
    import stripe as stripe_lib
    stripe_lib.api_key = STRIPE_SECRET_KEY

    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature', '')

    try:
        if webhook_secret:
            event = stripe_lib.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            event = stripe_lib.Event.construct_from(
                json.loads(payload), stripe_lib.api_key
            )
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        app.logger.info(f"Stripe payment succeeded: {intent['id']} amount={intent['amount']} currency={intent['currency']}")

    return jsonify({'received': True})


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
