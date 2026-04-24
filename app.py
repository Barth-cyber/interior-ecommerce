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