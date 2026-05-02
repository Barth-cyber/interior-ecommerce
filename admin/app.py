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
from datetime import datetime
from pymongo import MongoClient
import io

from admin.routes.health import register_health

ENV_FILE = os.path.join(os.path.dirname(__file__), '..', '.env')
# Load environment variables from .env file
load_dotenv(ENV_FILE)

# Import S3 storage
try:
    from s3_storage import init_s3
    s3_storage = init_s3()
except Exception as e:
    print(f"S3 initialization warning: {e}")
    s3_storage = None

# ✅ MongoDB Connection
mongo_uri = os.getenv("MONGO_URI")
if mongo_uri:
    try:
        client = MongoClient(mongo_uri)
        db = client["ductai"]
        chats = db["chats"]
        users = db["users"]
        products = db["products"]
        print("✅ MongoDB connected successfully")
    except Exception as e:
        print(f"⚠️  MongoDB connection warning: {e}")
        chats = None
        users = None
        products = None
else:
    print("⚠️  MONGO_URI not set. Chat history will not be stored in MongoDB.")
    chats = None
    users = None
    products = None

app = Flask(__name__, static_folder=None)

# ✅ REQUIRED for sessions + auth
app.secret_key = os.environ.get("SECRET_KEY", os.environ.get('ADMIN_SECRET_KEY', 'change-me-in-production'))

# ✅ FIX CORS — VERY IMPORTANT - Allow frontend URLs to connect across all public routes
CORS(app, resources={r"/*": {"origins": [
    "https://interiorductltd.com",
    "https://www.interiorductltd.com",
    "https://duct-ai-backend.onrender.com",
    "https://api.interiorductltd.com",
    "https://main.d3v5c9s0p0.amplifyapp.com",
    "https://your-app.netlify.app",
    "https://your-app.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5500",
    "http://localhost:3000"
]}})

app.config.update({
    'SECRET_KEY': os.environ.get('ADMIN_SECRET_KEY', 'change-me-in-production'),
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'SESSION_COOKIE_SECURE': os.environ.get('ADMIN_COOKIE_SECURE', 'False').lower() == 'true',
})

register_health(app)

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
if isinstance(ADMIN_USERNAME, str):
    ADMIN_USERNAME = ADMIN_USERNAME.strip()
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
if isinstance(ADMIN_PASSWORD, str):
    ADMIN_PASSWORD = ADMIN_PASSWORD.strip() or None
ADMIN_PASSWORD_HASH_ENV = os.environ.get('ADMIN_PASSWORD_HASH')
if isinstance(ADMIN_PASSWORD_HASH_ENV, str):
    ADMIN_PASSWORD_HASH_ENV = ADMIN_PASSWORD_HASH_ENV.strip() or None
ADMIN_ALLOW_DEFAULT_ADMIN = os.environ.get('ADMIN_ALLOW_DEFAULT_ADMIN', 'False').lower() in ('1', 'true', 'yes')


def _looks_like_password_hash(value):
    return isinstance(value, str) and ':' in value and '$' in value


def _get_admin_password_hash():
    if ADMIN_PASSWORD_HASH_ENV:
        if _looks_like_password_hash(ADMIN_PASSWORD_HASH_ENV):
            return ADMIN_PASSWORD_HASH_ENV
        app.logger.warning(
            'ADMIN_PASSWORD_HASH does not look like a valid hash. Treating the provided value as the raw password and hashing it.'
        )
        return generate_password_hash(ADMIN_PASSWORD_HASH_ENV)
    if ADMIN_PASSWORD:
        return generate_password_hash(ADMIN_PASSWORD)
    if ADMIN_ALLOW_DEFAULT_ADMIN:
        app.logger.warning(
            'Using insecure default admin credentials because ADMIN_ALLOW_DEFAULT_ADMIN is enabled. Set ADMIN_PASSWORD or ADMIN_PASSWORD_HASH for production.'
        )
        return generate_password_hash('admin')

    app.logger.warning(
        'No admin password configured. Admin login will remain disabled until ADMIN_PASSWORD or ADMIN_PASSWORD_HASH is set.'
    )
    return None


ADMIN_PASSWORD_HASH = _get_admin_password_hash()


def _quote_env_value(value):
    if value is None:
        return ''
    safe = str(value)
    if any(ch.isspace() for ch in safe) or any(ch in safe for ch in '"\'"#'):
        safe = safe.replace('"', '\\"')
        return f'"{safe}"'
    return safe


def _write_env_var(key, value):
    env_path = ENV_FILE
    os.makedirs(os.path.dirname(env_path), exist_ok=True)
    if not os.path.exists(env_path):
        open(env_path, 'a', encoding='utf-8').close()
    lines = []
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    updated = False
    normalized = _quote_env_value(value)
    for index, line in enumerate(lines):
        if line.strip().startswith(f'{key}='):
            lines[index] = f'{key}={normalized}\n'
            updated = True
            break
    if not updated:
        lines.append(f'{key}={normalized}\n')
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def _remove_env_var(key):
    env_path = ENV_FILE
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = [line for line in lines if not line.strip().startswith(f'{key}=')]
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def _update_admin_settings(username, password=None):
    _write_env_var('ADMIN_USERNAME', username)
    if password:
        hash_value = generate_password_hash(password)
        _write_env_var('ADMIN_PASSWORD_HASH', hash_value)
        _remove_env_var('ADMIN_PASSWORD')
        return hash_value
    return None

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
CONVERSATION_LOG_DIR = os.path.join(ROOT_DIR, 'logs')
CONVERSATION_LOG_PATH = os.path.join(CONVERSATION_LOG_DIR, 'conversations.json')
BEHAVIOUR_LOG_PATH = os.path.join(CONVERSATION_LOG_DIR, 'behaviour.json')

# ── Payment gateway config ───────────────────────────────────────────────────
PAYSTACK_SECRET_KEY    = os.environ.get('PAYSTACK_SECRET_KEY', '')
STRIPE_SECRET_KEY      = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
PAYSTACK_PUBLIC_KEY    = os.environ.get('PAYSTACK_PUBLIC_KEY', '')

# ── Google Gemini AI config ──────────────────────────────────────────────────
# Free tier: 1,500 requests/day  |  get key at https://aistudio.google.com/apikey
GEMINI_API_KEY = (
    os.environ.get('GEMINI_API_KEY') or
    os.environ.get('Gemini_API_Key') or
    os.environ.get('GOOGLE_API_KEY') or
    ''
)
# Using gemini-2.0-flash — fast, free-tier supported model
GEMINI_MODEL   = 'gemini-2.0-flash'
GEMINI_URL     = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'

# ── Anthropic Claude config ─────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')

# ── OpenAI config ──────────────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

# Ensure at least one AI provider is available
if not any([GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY]):
    app.logger.warning("No AI API keys set. AI assistant responses will be disabled. Configure GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def sanitize_filename(filename):
    filename = secure_filename(filename)
    filename = filename.replace(' ', '_')
    return filename


def is_data_uri(value):
    return isinstance(value, str) and value.strip().lower().startswith('data:image/')


def normalize_product_image_value(image_value):
    if not isinstance(image_value, str):
        return image_value
    image = image_value.strip().replace('\\', '/')
    if is_data_uri(image):
        return ''
    if image.lower().startswith('http://') or image.lower().startswith('https://'):
        return image
    for prefix in ('/idl-images/', 'idl-images/', '/IDL_Product_branding/', 'IDL_Product_branding/'):
        if image.startswith(prefix):
            image = image[len(prefix):]
            break
    image = image.split('/')[-1]
    return sanitize_filename(image)


def normalize_content_image_paths(data):
    if isinstance(data, dict):
        normalized = {}
        for key, value in data.items():
            if key == 'image':
                normalized[key] = normalize_product_image_value(value)
            else:
                normalized[key] = normalize_content_image_paths(value)
        return normalized
    if isinstance(data, list):
        return [normalize_content_image_paths(item) for item in data]
    return data


def generate_model_thumbnail(model_filename, thumbnail_filename, model_path):
    """
    Generate a PNG thumbnail for a 3D model.
    Creates a placeholder image with model name and metadata.
    
    Args:
        model_filename: Name of the uploaded GLB/GLTF file
        thumbnail_filename: Name to save the thumbnail as
        model_path: Path to the uploaded model file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        app.logger.warning('Pillow is not installed. Thumbnail generation is disabled.')
        return False

    try:
        # Get model file size
        file_size = os.path.getsize(model_path)
        size_mb = file_size / (1024 * 1024)
        
        # Create a placeholder thumbnail image (400x300)
        img = Image.new('RGB', (400, 300), color=(30, 58, 107))  # Navy background
        draw = ImageDraw.Draw(img)
        
        # Try to use default font, fallback to default if unavailable
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            text_font = ImageFont.truetype("arial.ttf", 14)
        except Exception:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Extract model name without extension
        model_name = model_filename.rsplit('.', 1)[0]
        
        # Draw model name (truncate if too long)
        if len(model_name) > 30:
            model_name = model_name[:27] + "..."
        draw.text((20, 50), model_name, fill=(196, 168, 130), font=title_font)
        
        # Draw model info
        draw.text((20, 100), "3D Model Preview", fill=(255, 255, 255), font=text_font)
        draw.text((20, 130), f"Format: {model_filename.rsplit('.', 1)[1].upper()}", fill=(196, 168, 130), font=text_font)
        draw.text((20, 160), f"Size: {size_mb:.2f} MB", fill=(196, 168, 130), font=text_font)
        draw.text((20, 190), f"Uploaded: {datetime.now().strftime('%Y-%m-%d')}", fill=(196, 168, 130), font=text_font)
        draw.text((20, 240), "Click to view in 3D", fill=(212, 184, 150), font=text_font)
        
        # Save thumbnail
        img.save(thumbnail_filename, 'PNG')
        app.logger.info(f"Generated thumbnail: {thumbnail_filename}")
        return True
    except Exception as e:
        app.logger.error(f"Failed to generate thumbnail: {e}")
        return False


def create_model_metadata(model_filename, thumbnail_filename, model_url=None):
    """
    Create a metadata JSON file for the 3D model.
    Stores thumbnail path, cameraOrbit, and other model information.
    
    Args:
        model_filename: Name of the GLB/GLTF file
        thumbnail_filename: Name of the thumbnail PNG file
        model_url: URL to the model if using cloud storage
    
    Returns:
        Metadata dictionary
    """
    try:
        model_name = model_filename.rsplit('.', 1)[0]
        thumbnail_name = thumbnail_filename.rsplit('/', 1)[-1] if '/' in thumbnail_filename else thumbnail_filename
        
        metadata = {
            "filename": model_filename,
            "thumbnail": f"/idl-images/{thumbnail_name}",
            "url": model_url or f"/idl-images/{model_filename}",
            "cameraOrbit": "0deg 75deg 2.5m",  # Default camera position (azimuth, elevation, distance)
            "environmentImage": "https://modelviewer.dev/shared-assets/environments/neutral.hdr",
            "exposure": 1,
            "shadowIntensity": 1,
            "name": model_name,
            "uploadDate": datetime.now().isoformat(),
            "arModes": ["webxr", "scene-viewer", "quick-look"],
            "autoRotate": True,
            "reveal": "interaction"
        }
        
        # Save metadata alongside the model with .json extension
        metadata_filename = os.path.join(UPLOAD_FOLDER, f"{model_name}.json")
        with open(metadata_filename, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        app.logger.info(f"Created metadata: {metadata_filename}")
        return metadata
    except Exception as e:
        app.logger.error(f"Failed to create metadata: {e}")
        return None


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
    if ADMIN_PASSWORD_HASH and username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password or ''):
        session['logged_in'] = True
        return jsonify({'logged_in': True})
    if not ADMIN_PASSWORD_HASH:
        return jsonify({'error': 'Admin login is not configured.'}), 503
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/login', methods=['POST'])
def do_login():
    username = request.form.get('username')
    password = request.form.get('password')
    if ADMIN_PASSWORD_HASH and username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password or ''):
        session['logged_in'] = True
        return redirect(url_for('admin'))
    return redirect(url_for('login') + '?error=1')


@app.route('/api/session')
def api_session():
    return jsonify({'logged_in': bool(session.get('logged_in'))})


@app.route('/api/admin-settings', methods=['GET', 'POST'])
@login_required
def api_admin_settings():
    global ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_PASSWORD_HASH_ENV, ADMIN_PASSWORD_HASH
    if request.method == 'GET':
        return jsonify({
            'username': ADMIN_USERNAME,
            'admin_configured': bool(ADMIN_PASSWORD_HASH),
        })

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password', '')
    password_confirm = data.get('passwordConfirm', '')

    if not username:
        return jsonify({'error': 'Username is required.'}), 400
    if password:
        if password != password_confirm:
            return jsonify({'error': 'Password confirmation does not match.'}), 400
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters.'}), 400
        ADMIN_PASSWORD_HASH = _update_admin_settings(username, password)
        ADMIN_PASSWORD_HASH_ENV = ADMIN_PASSWORD_HASH
        ADMIN_PASSWORD = None
    else:
        _update_admin_settings(username, None)

    ADMIN_USERNAME = username
    return jsonify({'saved': True})


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('logged_in', None)
    if request.method == 'POST':
        return jsonify({'logged_out': True})
    return redirect(url_for('login'))


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
    return send_from_directory(ROOT_DIR, 'interior.html')


@app.route('/interior.html')
def interior():
    return send_from_directory(ROOT_DIR, 'interior.html')


@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(ROOT_DIR, 'robots.txt')


@app.route('/hero-popup-slider.js')
def hero_popup_slider_js():
    return send_from_directory(ROOT_DIR, 'hero-popup-slider.js')


@app.route('/duct-ai-assistant.js')
def duct_ai_assistant_js():
    return send_from_directory(ROOT_DIR, 'duct-ai-assistant.js')


@app.route('/duct-ai-widget.js')
def duct_ai_widget_js():
    return send_from_directory(ROOT_DIR, 'duct-ai-widget.js')


@app.route('/duct-ai-widget.css')
def duct_ai_widget_css():
    return send_from_directory(ROOT_DIR, 'duct-ai-widget.css')


@app.route('/IDL_Product_branding/<path:filename>')
def idl_product_branding(filename):
    return send_from_directory(IDL_BRANDING_DIR, filename)


@app.route('/admin.css')
def admin_css():
    return send_from_directory('.', 'admin.css')


@app.route('/admin.js')
def admin_js():
    return send_from_directory('.', 'admin.js')


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


@app.route('/admin/3dmodels')
@login_required
def admin_3dmodels():
    glb_files = [
        f for f in os.listdir(UPLOAD_FOLDER)
        if f.lower().endswith('.glb')
    ]
    glb_files.sort()
    models = []
    for filename in glb_files:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        size_kb = None
        try:
            size_kb = round(os.path.getsize(file_path) / 1024, 2)
        except OSError:
            size_kb = None
        models.append({
            'filename': filename,
            'name': os.path.splitext(filename)[0],
            'url': f'/idl-images/{filename}',
            'size_kb': size_kb,
        })
    return jsonify(models)


@app.route('/public-3dmodels')
def public_3dmodels():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if '.' in f and f.rsplit('.', 1)[1].lower() in ALLOWED_3D]
    files.sort()
    # Provide a few hosted demo models so the storefront has working samples
    demo_models = [
        'https://modelviewer.dev/shared-assets/models/Astronaut.glb',
        'https://modelviewer.dev/shared-assets/models/RobotExpressive.glb',
        'https://modelviewer.dev/shared-assets/models/DamagedHelmet.glb',
        'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Avocado/glTF-Binary/Avocado.glb',
        'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/BoomBox/glTF-Binary/BoomBox.glb'
    ]
    # Combine local filenames and demo URLs; front-end knows to prefix local names with /idl-images/
    combined = files + demo_models
    return jsonify(combined)


@app.route('/upload', methods=['POST'])
@login_required
def upload_image():
    if 'images' not in request.files:
        return 'No file part', 400
    files = request.files.getlist('images')
    saved = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = sanitize_filename(file.filename)
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
            filename = sanitize_filename(file.filename)
            model_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # Generate thumbnail filename
            model_name_base = filename.rsplit('.', 1)[0]
            thumbnail_filename = f"{model_name_base}_thumb.png"
            thumbnail_path = os.path.join(UPLOAD_FOLDER, thumbnail_filename)
            
            if s3_storage:
                try:
                    url = s3_storage.upload_file(file, filename, 'models/')
                    file.seek(0)
                    file.save(model_path)  # Also save locally for thumbnail generation
                    
                    # Generate thumbnail and metadata
                    generate_model_thumbnail(filename, thumbnail_path, model_path)
                    metadata = create_model_metadata(filename, thumbnail_filename, url)
                    
                    saved.append({
                        'filename': filename,
                        'url': url,
                        'thumbnail': f"/idl-images/{thumbnail_filename}",
                        'storage': 'S3',
                        'metadata': metadata
                    })
                except Exception as e:
                    app.logger.error(f"S3 model upload failed: {e}, using local storage")
                    file.seek(0)
                    file.save(model_path)
                    
                    # Generate thumbnail and metadata
                    generate_model_thumbnail(filename, thumbnail_path, model_path)
                    metadata = create_model_metadata(filename, thumbnail_filename)
                    
                    saved.append({
                        'filename': filename,
                        'thumbnail': f"/idl-images/{thumbnail_filename}",
                        'storage': 'local',
                        'metadata': metadata
                    })
            else:
                file.save(model_path)
                
                # Generate thumbnail and metadata
                generate_model_thumbnail(filename, thumbnail_path, model_path)
                metadata = create_model_metadata(filename, thumbnail_filename)
                
                saved.append({
                    'filename': filename,
                    'thumbnail': f"/idl-images/{thumbnail_filename}",
                    'storage': 'local',
                    'metadata': metadata
                })
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
    
    model_name_base = filename.rsplit('.', 1)[0]
    
    if s3_storage:
        try:
            s3_storage.delete_file(filename, 'models/')
        except Exception as e:
            app.logger.error(f"S3 delete failed: {e}")
    
    # Delete model file
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
    
    # Delete associated thumbnail
    thumbnail_path = os.path.join(UPLOAD_FOLDER, f"{model_name_base}_thumb.png")
    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)
    
    # Delete associated metadata JSON
    metadata_path = os.path.join(UPLOAD_FOLDER, f"{model_name_base}.json")
    if os.path.exists(metadata_path):
        os.remove(metadata_path)
    
    return jsonify({'deleted': filename})


@app.route('/idl-images/<filename>')
def serve_image(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_EXTENSIONS and ext not in ALLOWED_3D:
        return 'Invalid file', 400
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/api/model-metadata/<model_filename>', methods=['GET'])
def get_model_metadata(model_filename):
    """
    Retrieve metadata for a 3D model.
    Returns thumbnail path, camera settings, and other model information.
    """
    if '.' not in model_filename or model_filename.rsplit('.', 1)[1].lower() not in ALLOWED_3D:
        return jsonify({'error': 'Invalid model file'}), 400
    
    model_name_base = model_filename.rsplit('.', 1)[0]
    metadata_path = os.path.join(UPLOAD_FOLDER, f"{model_name_base}.json")
    
    if not os.path.exists(metadata_path):
        return jsonify({'error': 'Metadata not found'}), 404
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return jsonify(metadata)
    except Exception as e:
        app.logger.error(f"Failed to read metadata: {e}")
        return jsonify({'error': 'Failed to read metadata'}), 500


@app.route('/api/model-metadata/<model_filename>', methods=['PUT'])
@login_required
def update_model_metadata(model_filename):
    """
    Update metadata for a 3D model.
    Allows customizing camera orbit, exposure, shadow intensity, etc.
    """
    if '.' not in model_filename or model_filename.rsplit('.', 1)[1].lower() not in ALLOWED_3D:
        return jsonify({'error': 'Invalid model file'}), 400
    
    model_name_base = model_filename.rsplit('.', 1)[0]
    metadata_path = os.path.join(UPLOAD_FOLDER, f"{model_name_base}.json")
    
    if not os.path.exists(metadata_path):
        return jsonify({'error': 'Metadata not found'}), 404
    
    try:
        data = request.get_json()
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Update allowed fields
        allowed_fields = ['cameraOrbit', 'exposure', 'shadowIntensity', 'name', 'autoRotate', 'reveal', 'environmentImage']
        for field in allowed_fields:
            if field in data:
                metadata[field] = data[field]
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return jsonify({'updated': True, 'metadata': metadata})
    except Exception as e:
        app.logger.error(f"Failed to update metadata: {e}")
        return jsonify({'error': 'Failed to update metadata'}), 500




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
    data = normalize_content_image_paths(data)
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


def _get_conversation_summary(session_id, history):
    if not history:
        return None
    pages = set()
    for msg in history:
        if msg.get('page'):
            pages.add(msg['page'])
    return {
        'session_id': session_id,
        'message_count': len(history),
        'first_message': history[0].get('text', '')[:100] if history else '',
        'last_activity': history[-1].get('timestamp', '') if history else '',
        'pages_visited': list(pages)
    }


@app.route('/admin/conversations')
@login_required
def admin_conversations():
    if not os.path.exists(CONVERSATION_LOG_PATH):
        return jsonify({'conversations': []})
    try:
        with open(CONVERSATION_LOG_PATH, 'r', encoding='utf-8') as f:
            all_conversations = json.load(f)
        summaries = []
        for session_id, history in all_conversations.items():
            summary = _get_conversation_summary(session_id, history)
            if summary:
                summaries.append(summary)
        summaries.sort(key=lambda x: x['last_activity'], reverse=True)
        return jsonify({'conversations': summaries})
    except Exception as e:
        app.logger.error(f"Error reading conversations: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/admin/conversations/<session_id>')
@login_required
def admin_conversation_detail(session_id):
    if not os.path.exists(CONVERSATION_LOG_PATH):
        return jsonify({'error': 'No conversations found'}), 404
    try:
        with open(CONVERSATION_LOG_PATH, 'r', encoding='utf-8') as f:
            all_conversations = json.load(f)
        history = all_conversations.get(session_id)
        if not history:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify({
            'session_id': session_id,
            'history': history,
            'summary': _get_conversation_summary(session_id, history)
        })
    except Exception as e:
        app.logger.error(f"Error reading conversation detail: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/admin/conversations.html')
@login_required
def conversations_html():
    return send_from_directory('.', 'conversations.html')


# ─────────────────────────────────────────────────────────────────────────────
# PART 4 & 5 — ADMIN DASHBOARD (Chat Logs + Analytics)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/admin/chat-logs', methods=['GET'])
@login_required
def admin_chat_logs():
    """Get chat logs from MongoDB (PART 4 - Admin Dashboard)."""
    if not chats:
        return jsonify({'error': 'MongoDB not available'}), 500
    
    try:
        limit = request.args.get('limit', 50, type=int)
        data = list(chats.find().sort("_id", -1).limit(limit))
        
        # Convert ObjectId to string for JSON serialization
        for d in data:
            d["_id"] = str(d["_id"])
            if "timestamp" in d:
                d["timestamp"] = d["timestamp"].isoformat()
        
        return jsonify({'chats': data})
    except Exception as e:
        app.logger.error(f"Error retrieving chat logs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/admin/analytics', methods=['GET'])
@login_required
def admin_analytics():
    """Get analytics data for dashboard (PART 5 - Self-Learning)."""
    try:
        result = {
            'top_questions': [],
            'total_chats': 0,
            'total_users': 0
        }
        
        if chats:
            # Get total chat count
            result['total_chats'] = chats.count_documents({})
            
            # Get top questions (PART 5)
            result['top_questions'] = get_top_questions()
        
        if users:
            # Get total unique users
            result['total_users'] = users.count_documents({})
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error retrieving analytics: {e}")
        return jsonify({'error': str(e)}), 500


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
        return answer, False, None
    except Exception as e:
        error_str = str(e)
        app.logger.error(f"Gemini API error: {error_str}")
        return None, True, error_str


def _call_llm(prompt_text, system_instruction=None, max_tokens=512):
    """Call LLM with intelligent multi-provider fallback chain.
    
    Priority order:
    1. Gemini (Google) - most reliable, fast free tier
    2. Anthropic Claude - excellent reasoning
    3. OpenAI GPT-4o-mini - reliable fallback
    
    Returns: (answer_text, error_bool)
    """
    # Try Gemini first (Primary)
    provider = None
    error_log = None

    if GEMINI_API_KEY:
        app.logger.info("Trying Gemini API...")
        answer, error, provider_error = _call_gemini(prompt_text, system_instruction, max_tokens)
        if answer and not error:
            app.logger.info("✅ Gemini responded successfully")
            return answer, False, 'gemini', None
        error_log = f"Gemini: {provider_error}" if provider_error else "Gemini failed"
        app.logger.warning("Gemini failed or no response")

    if ANTHROPIC_API_KEY:
        app.logger.info("Fallback 1: Trying Anthropic Claude API...")
        answer, error, provider_error = _call_anthropic(prompt_text, system_instruction, max_tokens)
        if answer and not error:
            app.logger.info("✅ Anthropic Claude responded successfully")
            return answer, False, 'anthropic', None
        error_log = f"Anthropic: {provider_error}" if provider_error else error_log or "Anthropic failed"
        app.logger.warning("Anthropic failed or no response")

    if OPENAI_API_KEY:
        app.logger.info("Fallback 2: Trying OpenAI API...")
        answer, error, provider_error = _call_openai(prompt_text, system_instruction, max_tokens)
        if answer and not error:
            app.logger.info("✅ OpenAI responded successfully")
            return answer, False, 'openai', None
        error_log = f"OpenAI: {provider_error}" if provider_error else error_log or "OpenAI failed"
        app.logger.warning("OpenAI failed or no response")

    app.logger.error("❌ All AI providers failed. No response available.")
    return None, True, None, error_log or "No AI providers available"


def _ask_gemini_chat(query, kb, products):
    """Call AI API for intelligent AI chat responses (with fallback chain)."""
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

    return _call_llm(query, system_instruction=system_instruction, max_tokens=512)


# ─────────────────────────────────────────────────────────────────────────────
# MongoDB Chat Functions
# ─────────────────────────────────────────────────────────────────────────────

def save_chat(session_id, user_msg, bot_reply):
    """Save chat messages to MongoDB."""
    if not chats:
        app.logger.warning("MongoDB not available. Chat not saved.")
        return False
    
    try:
        chats.insert_one({
            "session_id": session_id,
            "user": user_msg,
            "bot": bot_reply,
            "timestamp": datetime.utcnow()
        })
        return True
    except Exception as e:
        app.logger.error(f"Error saving chat to MongoDB: {e}")
        return False


def load_history(session_id, limit=5):
    """Load chat history from MongoDB (context memory)."""
    if not chats:
        app.logger.warning("MongoDB not available. No history loaded.")
        return []
    
    try:
        history = chats.find({"session_id": session_id}).sort("_id", -1).limit(limit)
        
        messages = []
        for h in reversed(list(history)):
            messages.append({"role": "user", "parts": [h["user"]]})
            messages.append({"role": "model", "parts": [h["bot"]]})
        
        return messages
    except Exception as e:
        app.logger.error(f"Error loading chat history from MongoDB: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# PART 1 — USER PROFILES (returning visitors)
# ─────────────────────────────────────────────────────────────────────────────

def get_or_create_user(session_id):
    """Track users across visits and build behavior history."""
    if not users:
        return {"session_id": session_id}
    
    try:
        user = users.find_one({"session_id": session_id})
        
        if not user:
            user = {
                "session_id": session_id,
                "created_at": datetime.utcnow(),
                "interests": [],
                "visits": 1
            }
            users.insert_one(user)
        else:
            users.update_one(
                {"session_id": session_id},
                {"$inc": {"visits": 1}}
            )
        
        return user
    except Exception as e:
        app.logger.error(f"Error in get_or_create_user: {e}")
        return {"session_id": session_id}


def update_user_interests(session_id, message):
    """Track user interests automatically based on message keywords."""
    if not users:
        return False
    
    try:
        keywords = {
            "chair": "chairs",
            "sofa": "sofas",
            "table": "tables",
            "bed": "beds",
            "cabinet": "cabinets",
            "desk": "desks",
            "shelf": "shelves",
            "wardrobe": "wardrobes",
            "decor": "decoration",
            "lighting": "lights",
            "rug": "rugs",
            "curtain": "curtains",
        }
        
        for word, tag in keywords.items():
            if word in message.lower():
                users.update_one(
                    {"session_id": session_id},
                    {"$addToSet": {"interests": tag}}
                )
        
        return True
    except Exception as e:
        app.logger.error(f"Error in update_user_interests: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# PART 3 — AI RECOMMENDATIONS (PRODUCT-BASED)
# ─────────────────────────────────────────────────────────────────────────────

def get_recommendation(user):
    """Get product recommendation based on user interests."""
    if not products:
        return None
    
    try:
        interests = user.get("interests", [])
        
        if not interests:
            return None
        
        # Find a product matching user interests
        product = products.find_one({"category": {"$in": interests}})
        
        if product:
            name = product.get("name", "Product")
            price = product.get("price", "Price on request")
            return f"👉 You may like: {name} ({price})"
        
        return None
    except Exception as e:
        app.logger.error(f"Error in get_recommendation: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# PART 5 — SELF-LEARNING AI LOOP
# ─────────────────────────────────────────────────────────────────────────────

def get_top_questions():
    """Analyze patterns — get most frequently asked questions."""
    if not chats:
        return []
    
    try:
        pipeline = [
            {"$group": {"_id": "$user", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        return list(chats.aggregate(pipeline))
    except Exception as e:
        app.logger.error(f"Error in get_top_questions: {e}")
        return []


def build_dynamic_prompt(user, message):
    """Improve AI prompt dynamically based on user interests."""
    interests = ", ".join(user.get("interests", []))
    visits = user.get("visits", 1)
    
    context = ""
    if interests:
        context += f"\nUser interests: {interests}"
    
    if visits > 1:
        context += f"\n(Returning visitor - {visits} visits)"
    
    return context


def _build_product_summary(products):
    if not products:
        return 'No current products are available.'
    lines = []
    for product in products[:80]:
        name = product.get('name', 'Unknown product')
        category = product.get('category', 'Uncategorized')
        price = product.get('price', 'N/A')
        lines.append(f'- {name} | {category} | {price}')
    return '\n'.join(lines)


def _build_drogram_prompt(products):
    product_summary = _build_product_summary(products)
    return (
        'You are Duct AI, the intelligent assistant for Interior Duct Ltd, a premium Nigerian furniture and interior design company. '
        'You help visitors explore products, get design advice, receive personalized recommendations, and place orders. '
        'You remember what users have discussed in this session and provide context-aware responses. '
        'You should make specific product recommendations from the current catalog when users ask about furniture, design, or purchase decisions. '
        'Current product catalog:\n'
        f'{product_summary}\n'
        'When making recommendations, refer to actual product names, categories, and prices from this catalog. '
        'If a requested item is not available, explain that it is unavailable and offer a suitable alternative from the catalog.'
    )


def _load_conversation_history(session_id):
    if not os.path.exists(CONVERSATION_LOG_PATH):
        return []
    try:
        with open(CONVERSATION_LOG_PATH, 'r', encoding='utf-8') as f:
            all_conversations = json.load(f)
        return all_conversations.get(session_id, [])
    except Exception as e:
        app.logger.warning(f"Unable to load conversation history: {e}")
        return []


def _save_conversation_history(session_id, history):
    os.makedirs(CONVERSATION_LOG_DIR, exist_ok=True)
    all_conversations = {}
    if os.path.exists(CONVERSATION_LOG_PATH):
        try:
            with open(CONVERSATION_LOG_PATH, 'r', encoding='utf-8') as f:
                all_conversations = json.load(f)
        except Exception as e:
            app.logger.warning(f"Unable to read existing conversation log file: {e}")
    all_conversations[session_id] = history
    with open(CONVERSATION_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_conversations, f, indent=2, ensure_ascii=False)


def _append_behaviour_event(event):
    os.makedirs(CONVERSATION_LOG_DIR, exist_ok=True)
    behaviour_log = []
    if os.path.exists(BEHAVIOUR_LOG_PATH):
        try:
            with open(BEHAVIOUR_LOG_PATH, 'r', encoding='utf-8') as f:
                behaviour_log = json.load(f)
        except Exception as e:
            app.logger.warning(f"Unable to read existing behaviour log: {e}")
    behaviour_log.append(event)
    with open(BEHAVIOUR_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(behaviour_log, f, indent=2, ensure_ascii=False)


def _call_gemini_conversation(history, system_instruction=None, max_tokens=512):
    if not GEMINI_API_KEY:
        return None, True, 'Gemini API key not configured'

    body = {
        'contents': [
            {'role': message['role'], 'parts': [{'text': message['text']}]}
            for message in history
        ],
        'generationConfig': {
            'maxOutputTokens': max_tokens,
            'temperature': 0.7,
        },
    }

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
        answer = data['candidates'][0]['content']['parts'][0]['text'].strip()
        return answer, False, None
    except Exception as e:
        error_str = str(e)
        app.logger.error(f"Gemini conversation API error: {error_str}")
        return None, True, error_str


def _parse_recommendations_json(answer_text):
    try:
        parsed = json.loads(answer_text)
        if isinstance(parsed, dict) and 'recommendations' in parsed:
            parsed = parsed['recommendations']
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    return None


def _call_openai(prompt_text, system_instruction=None, max_tokens=512):
    """Call OpenAI API (GPT-4o-mini) for AI chat responses."""
    if not OPENAI_API_KEY:
        return None, True, 'OpenAI API key not configured'

    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        messages = []
        if system_instruction:
            messages.append({'role': 'system', 'content': system_instruction})
        messages.append({'role': 'user', 'content': prompt_text})
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        
        if response.choices and len(response.choices) > 0:
            answer = response.choices[0].message.content.strip()
            return answer, False, None
        return None, True, 'OpenAI returned no text'
    except ImportError:
        error_str = 'OpenAI package not installed. Install with: pip install openai'
        app.logger.error(error_str)
        return None, True, error_str
    except Exception as e:
        error_str = str(e)
        app.logger.error(f"OpenAI API error: {error_str}")
        return None, True, error_str


def _call_openai_conversation(history, system_instruction=None, max_tokens=512):
    """Call OpenAI API with conversation history."""
    if not OPENAI_API_KEY:
        return None, True, 'OpenAI API key not configured'

    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Convert history to OpenAI format
        messages = []
        if system_instruction:
            messages.append({'role': 'system', 'content': system_instruction})
        
        for msg in history:
            if msg['role'] == 'user':
                messages.append({'role': 'user', 'content': msg['text']})
            elif msg['role'] == 'assistant':
                messages.append({'role': 'assistant', 'content': msg['text']})
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        
        if response.choices and len(response.choices) > 0:
            answer = response.choices[0].message.content.strip()
            return answer, False, None
        return None, True, 'OpenAI conversation returned no text'
    except ImportError:
        error_str = 'OpenAI package not installed. Install with: pip install openai'
        app.logger.error(error_str)
        return None, True, error_str
    except Exception as e:
        error_str = str(e)
        app.logger.error(f"OpenAI conversation API error: {error_str}")
        return None, True, error_str


def _call_anthropic(prompt_text, system_instruction=None, max_tokens=512):
    """Call Anthropic Claude API for AI chat responses."""
    if not ANTHROPIC_API_KEY:
        return None, True, 'Anthropic API key not configured'

    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        messages = [
            {'role': 'user', 'content': prompt_text}
        ]
        
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system_instruction,
            messages=messages,
            temperature=0.7,
        )
        
        if response.content and len(response.content) > 0:
            answer = response.content[0].text.strip()
            return answer, False, None
        return None, True, 'Anthropic returned no text'
    except ImportError:
        error_str = 'Anthropic package not installed. Install with: pip install anthropic'
        app.logger.error(error_str)
        return None, True, error_str
    except Exception as e:
        error_str = str(e)
        app.logger.error(f"Anthropic Claude API error: {error_str}")
        return None, True, error_str


def _call_anthropic_conversation(history, system_instruction=None, max_tokens=512):
    """Call Anthropic Claude API with conversation history."""
    if not ANTHROPIC_API_KEY:
        return None, True, 'Anthropic API key not configured'

    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Convert history to Anthropic format (user/assistant alternating)
        messages = []
        for msg in history:
            if msg['role'] == 'user':
                messages.append({'role': 'user', 'content': msg['text']})
            elif msg['role'] == 'assistant':
                messages.append({'role': 'assistant', 'content': msg['text']})
        
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system_instruction,
            messages=messages,
            temperature=0.7,
        )
        
        if response.content and len(response.content) > 0:
            answer = response.content[0].text.strip()
            return answer, False, None
        return None, True, 'Anthropic conversation returned no text'
    except ImportError:
        error_str = 'Anthropic package not installed. Install with: pip install anthropic'
        app.logger.error(error_str)
        return None, True, error_str
    except Exception as e:
        error_str = str(e)
        app.logger.error(f"Anthropic Claude conversation API error: {error_str}")
        return None, True, error_str


def _call_llm_conversation(history, system_instruction=None, max_tokens=512):
    """Call LLM with intelligent fallback chain for conversation."""
    error_log = None

    if GEMINI_API_KEY:
        app.logger.info("Trying Gemini for conversation...")
        answer, error, provider_error = _call_gemini_conversation(history, system_instruction, max_tokens)
        if answer and not error:
            return answer, False, 'gemini', None
        error_log = f"Gemini: {provider_error}" if provider_error else "Gemini failed"

    if ANTHROPIC_API_KEY:
        app.logger.info("Fallback 1: Trying Anthropic Claude for conversation...")
        answer, error, provider_error = _call_anthropic_conversation(history, system_instruction, max_tokens)
        if answer and not error:
            return answer, False, 'anthropic', None
        error_log = f"Anthropic: {provider_error}" if provider_error else error_log or "Anthropic failed"

    if OPENAI_API_KEY:
        app.logger.info("Fallback 2: Trying OpenAI for conversation...")
        answer, error, provider_error = _call_openai_conversation(history, system_instruction, max_tokens)
        if answer and not error:
            return answer, False, 'openai', None
        error_log = f"OpenAI: {provider_error}" if provider_error else error_log or "OpenAI failed"

    app.logger.error("All LLM providers failed for conversation. No API keys configured or all APIs are down.")
    return None, True, None, error_log or "No AI providers available"


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = str(data.get('message', '')).strip()
    session_id = str(data.get('session_id', '')).strip()
    page = str(data.get('page', ''))
    user_agent = str(data.get('user_agent', ''))

    if not message or not session_id:
        return jsonify({'error': 'message and session_id are required'}), 400

    history = _load_conversation_history(session_id)
    history.append({
        'role': 'user',
        'text': message,
        'page': page,
        'user_agent': user_agent,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })

    system_prompt = (
        "You are Duct AI, the intelligent assistant for Interior Duct Ltd, a premium Nigerian furniture and interior design company. "
        "You help visitors explore products, get design advice, receive personalized recommendations, and place orders. "
        "You remember what users have discussed in this session and provide context-aware responses."
    )

    products = _load_products()
    system_prompt = _build_drogram_prompt(products)

    answer, error, provider, error_log = _call_llm_conversation(history, system_instruction=system_prompt, max_tokens=512)
    if error or answer is None:
        app.logger.error(f"/chat fallback response: provider={provider}, error_log={error_log}")
        return jsonify({'error': 'Unable to get a response from AI provider', 'provider': provider, 'error_log': error_log}), 503

    history.append({
        'role': 'assistant',
        'text': answer,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })
    _save_conversation_history(session_id, history)

    return jsonify({'reply': answer})


@app.route('/track', methods=['POST'])
def track():
    data = request.get_json() or {}
    event = data.get('event')
    session_id = str(data.get('session_id', '')).strip()
    if not event or not session_id:
        return jsonify({'error': 'event and session_id are required'}), 400

    record = {
        'event': event,
        'session_id': session_id,
        'page': data.get('page'),
        'product_name': data.get('product_name'),
        'seconds': data.get('seconds'),
        'user_agent': data.get('user_agent') or request.headers.get('User-Agent'),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    _append_behaviour_event(record)
    return jsonify({'tracked': True})


@app.route('/recommendations', methods=['POST', 'GET'])
def recommendations():
    if request.method == 'GET':
        session_id = str(request.args.get('session_id', '')).strip()
    else:
        data = request.get_json() or {}
        session_id = str(data.get('session_id', '')).strip()
    if not session_id:
        return jsonify({'error': 'session_id is required'}), 400

    history = _load_conversation_history(session_id)
    if not history:
        return jsonify({'error': 'No conversation history found for this session'}), 404

    products = _load_products()
    system_prompt = (
        _build_drogram_prompt(products) +
        ' Analyze the conversation and return exactly 3 product recommendations as JSON. '
        'Provide only a JSON array of recommendation objects with the fields: name, price, category, reason, image_path. '
        'Do not include any additional narrative outside the JSON array.'
    )

    answer, error, provider, error_log = _call_llm_conversation(history, system_instruction=system_prompt, max_tokens=512)
    if error or answer is None:
        app.logger.error(f"/recommendations fallback response: provider={provider}, error_log={error_log}")
        return jsonify({'error': 'Unable to get a response from AI provider', 'provider': provider, 'error_log': error_log}), 503

    recommendations = _parse_recommendations_json(answer)
    if recommendations is None:
        return jsonify({
            'error': 'Gemini response could not be parsed as recommendation JSON',
            'raw': answer
        }), 502

    return jsonify({'recommendations': recommendations})


# ─────────────────────────────────────────────────────────────────────────────
# Duct AI API Endpoints (Public)
# ─────────────────────────────────────────────────────────────────────────────
# GET  /health                              → {"status": "ok"}
# POST /chat                                → {"reply": "..."}  
# POST /track                               → {"tracked": true}
# GET  /recommendations?session_id=<uuid>  → {"recommendations": [...]}
# POST /recommendations (body: session_id)  → {"recommendations": [...]}
# ─────────────────────────────────────────────────────────────────────────────
# AI Chat endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/ai-query', methods=['POST'])
def ai_query():
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    session_id = data.get('session_id', 'default')  # Get session_id from request
    
    if not query:
        return jsonify({'answer': None, 'escalate': True})

    # PART 1: Get or create user + track interests
    user = get_or_create_user(session_id)
    update_user_interests(session_id, query)

    kb = _load_kb()
    products_data = _load_products()

    # 1. Try fast local fuzzy match first (no API cost)
    local_answer = _fuzzy_kb_match(query, kb)
    if local_answer:
        # Save to MongoDB if available
        save_chat(session_id, query, local_answer)
        
        # PART 3: Get recommendation based on user interests
        recommendation = get_recommendation(user)
        
        return jsonify({
            'answer': local_answer,
            'escalate': False,
            'recommendation': recommendation,
            'visits': user.get('visits', 1)
        })

    # 2. Call Gemini API
    answer, escalate, provider, error_log = _ask_gemini_chat(query, kb, products_data)
    if answer:
        # Save to MongoDB if available
        save_chat(session_id, query, answer)
        
        # PART 3: Get recommendation based on user interests
        recommendation = get_recommendation(user)
        
        return jsonify({
            'answer': answer,
            'escalate': False,
            'provider': provider,
            'recommendation': recommendation,
            'visits': user.get('visits', 1)
        })

    fallback_answer = 'Sorry, I’m having trouble connecting to our AI service right now. Please try again later or contact us on WhatsApp.'
    app.logger.error(f"/ai-query fallback response: provider={provider}, escalate={escalate}, error_log={error_log}")
    return jsonify({
        'answer': fallback_answer,
        'escalate': escalate,
        'provider': provider,
        'error_log': error_log
    })


@app.route('/escalate', methods=['POST'])
def escalate():
    data = request.get_json()
    return jsonify({'escalated': True, 'payload': data})


@app.route('/chat-history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    """Retrieve chat history for a session from MongoDB."""
    history = load_history(session_id, limit=5)
    return jsonify({'session_id': session_id, 'history': history})


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
        return send_from_directory(ROOT_DIR, 'interior.html')
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

@app.route('/3d-demo')
@login_required
def three_d_demo():
    return send_from_directory('.', '3d-demo.html')


@app.route('/categories.html')
@login_required
def categories_html():
    return send_from_directory('.', 'categories.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
