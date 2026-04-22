from flask import Flask, request, redirect, url_for, send_from_directory, jsonify, session
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from dotenv import load_dotenv
import os
import json
import difflib

# Load environment variables from .env file
load_dotenv()

# Try to import ML model (optional dependency)
try:
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer('all-MiniLM-L6-v2')
except ImportError:
    model = None

# ...existing code...

from flask import Flask
from flask_cors import CORS
import os
 
app = Flask(__name__)

from flask import Flask, request, redirect, url_for, send_from_directory, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import json
import difflib
try:
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer('all-MiniLM-L6-v2')
except ImportError:
    model = None

app = Flask(__name__, static_folder=None)
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

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'IDL_Product_branding')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_3D = {'glb', 'gltf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CONTENT_PATH = os.path.join(os.path.dirname(__file__), 'content.json')
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IDL_BRANDING_DIR = os.path.join(ROOT_DIR, 'IDL_Product_branding')
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), 'categories.json')
KB_PATH = os.path.join(os.path.dirname(__file__), 'knowledge_base.json')
USER_LOG_PATH = os.path.join(os.path.dirname(__file__), 'user_log.json')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

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

@app.route('/admin-auth.js')
def admin_auth_js():
    return send_from_directory('.', 'admin-auth.js')


# Redirect /admin/ (with trailing slash) to /admin (no slash)
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
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            saved.append(filename)
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
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            saved.append(filename)
    return jsonify({'uploaded': saved})

@app.route('/delete', methods=['POST'])
@login_required
def delete_image():
    data = request.get_json()
    filename = data.get('filename')
    if not filename or not allowed_file(filename):
        return 'Invalid filename', 400
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'deleted': filename})
    return 'File not found', 404

@app.route('/delete-model', methods=['POST'])
@login_required
def delete_model():
    data = request.get_json()
    filename = data.get('filename')
    if not filename or '.' not in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_3D:
        return 'Invalid filename', 400
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'deleted': filename})
    return 'File not found', 404

@app.route('/idl-images/<filename>')
def serve_image(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_EXTENSIONS and ext not in ALLOWED_3D:
        return 'Invalid file', 400
    return send_from_directory(UPLOAD_FOLDER, filename)

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



@app.route('/ai-query', methods=['POST'])
def ai_query():
    data = request.get_json()
    query = data.get('query', '').lower()
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        kb = json.load(f)
    faqs = kb.get('faqs', [])
    questions = [faq['q'] for faq in faqs]
    # Semantic search if model available
    if model and questions:
        q_emb = model.encode([query], convert_to_tensor=True)
        faq_embs = model.encode(questions, convert_to_tensor=True)
        scores = util.pytorch_cos_sim(q_emb, faq_embs)[0]
        best_idx = int(scores.argmax())
        if float(scores[best_idx]) > 0.65:
            return jsonify({'answer': faqs[best_idx]['a'], 'escalate': False})
    # Fuzzy match using difflib
    matches = difflib.get_close_matches(query, [q.lower() for q in questions], n=1, cutoff=0.6)
    if matches:
        for faq in faqs:
            if faq['q'].lower() == matches[0]:
                return jsonify({'answer': faq['a'], 'escalate': False})
    # Fallback: substring search
    for faq in faqs:
        if faq['q'].lower() in query or query in faq['q'].lower():
            return jsonify({'answer': faq['a'], 'escalate': False})
    for tip in kb.get('design_tips', []):
        if tip.lower() in query:
            return jsonify({'answer': tip, 'escalate': False})
    # Escalate if not found
    return jsonify({'answer': None, 'escalate': True})

@app.route('/escalate', methods=['POST'])
def escalate():
    data = request.get_json()
    # Here, you would integrate with WhatsApp API or redirect logic
    # For now, just return the data for frontend to handle
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

