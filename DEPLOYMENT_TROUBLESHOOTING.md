# Troubleshooting Render Deployment Guide
## Interior Ecommerce Flask Application

This guide covers common issues you might encounter when deploying your Flask application to Render and provides specific solutions.

---

## Quick Diagnostics

### 1. Check Render Logs
Always start here when your app fails to deploy or crashes:

```bash
# In Render Dashboard:
# Navigate to your service → Logs
# Watch for:
# - Build errors (red text)
# - Runtime errors (500, 502, timeouts)
# - Module import errors
```

### 2. Verify Local Setup Works
Before deploying, ensure it works locally:

```bash
# Activate virtual environment
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally
python application.py
# Should start on http://localhost:5000
```

---

## Build & Deploy Errors

### ❌ ModuleNotFoundError / Module Not Found

**Error Message:**
```
ModuleNotFoundError: No module named 'xyz'
```

**Common Causes:**
1. **Missing from requirements.txt** - Dependency not listed
2. **Incorrect import name** - Typo in import statement
3. **File path issues on Linux** - Flask apps are case-sensitive on Render

**Solutions:**

✅ **Update requirements.txt:**
```bash
# Generate current dependencies
pip freeze > requirements.txt

# OR manually add missing package
echo "package-name==1.2.3" >> requirements.txt
```

✅ **Check file names are case-correct:**
```bash
# Render uses Linux (case-sensitive)
# admin/app.py - CORRECT
# Admin/App.py - WRONG
# Check all imports match actual file names exactly
```

✅ **Verify all imports in application.py:**
```python
# application.py - This file MUST exist and be correct
from admin.app import app  # admin/app.py must exist

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
```

---

### ❌ SyntaxError or Invalid Python Code

**Error Message:**
```
SyntaxError: invalid syntax
```

**Solutions:**

✅ **Run local syntax check:**
```bash
# Check application.py
python -m py_compile application.py

# Check all Python files
python -m py_compile admin/app.py
python -m py_compile admin/admin.js  # Wait, this shouldn't be .py
```

✅ **Ensure correct file extensions:**
- Python files: `.py`
- JavaScript files: `.js`
- HTML files: `.html`

---

### ❌ Python Version Conflicts

**Error Message:**
```
requires Python >= 3.8
The engine "python" is incompatible
```

**Solution:**

✅ **Verify requirements.txt compatibility:**
```bash
# Check which Python version your packages need
pip check

# Common issue: torch, transformers need Python 3.8+
# Your requirements.txt specifies packages that need Python 3.10+
```

✅ **In Render Dashboard:**
- Service Settings → Environment
- Ensure Python version matches requirements
- For this app, use **Python 3.10** (recommended)

---

### ❌ Invalid Build Command

**Error Message:**
```
Build failed: Invalid build command
```

**Your Correct Build Command:**
```
pip install -r requirements.txt
```

**Verify in Render:**
1. Dashboard → Your Service → Settings
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn -w 2 -b 0.0.0.0:$PORT application:app`

---

### ❌ Invalid Start Command

**Error Message:**
```
Service failed to start: Invalid start command
```

**Your Correct Start Command:**
```
gunicorn -w 2 -b 0.0.0.0:$PORT application:app
```

**Why This Works:**
- `gunicorn` - WSGI server for Python/Flask
- `-w 2` - 2 worker processes (appropriate for free tier)
- `-b 0.0.0.0:$PORT` - Bind to all interfaces on Render's PORT
- `application:app` - Points to `app` variable in `application.py`

---

### ❌ Missing Environment Variables

**Error Message:**
```
KeyError: 'ADMIN_SECRET_KEY'
or silent app crash with no logs
```

**Required Environment Variables for Your App:**

Add these in **Render Dashboard** → Settings → Environment:

```
ADMIN_SECRET_KEY = [generate-random-string]
ADMIN_USERNAME = admin
ADMIN_PASSWORD = [your-secure-password]
ADMIN_COOKIE_SECURE = true
PYTHONUNBUFFERED = true
```

**Generate a secure key:**
```python
import secrets
print(secrets.token_hex(32))
```

---

## Runtime Errors

### ❌ 400 Bad Request

**Error Message:**
```
400 Bad Request
```

**Possible Causes:**
- CORS issues with frontend requests
- Missing required form fields
- Invalid JSON in request body

**Solutions:**

✅ **Check CORS configuration in admin/app.py:**
```python
# Should include:
CORS(app, supports_credentials=True)
```

✅ **Verify frontend is making correct requests:**
```javascript
// Check console in browser DevTools
// Network tab → look for 400 errors
// Click the request → Response tab
// This shows the actual error from Flask
```

---

### ❌ 404 Not Found

**Error Message:**
```
404 Not Found
```

**For Static Files (HTML, CSS, Images):**

✅ **Verify Flask serves static files correctly:**
```python
# admin/app.py should have:
app = Flask(__name__, 
           static_folder='static',        # Folder name
           static_url_path='/static')     # URL path
```

✅ **Check file locations:**
```
c:\ecommerce\
├── static/
│   ├── 3d-viewer.js
│   ├── duct-ai.js
│   ├── interior.html    # OR should this be in templates/?
│   └── [other files]
├── admin/
│   └── static/
│       └── [admin files]
```

✅ **If interior.html is not serving:**
```python
# In admin/app.py, add this route:
@app.route('/')
def serve_index():
    return send_from_directory('static', 'interior.html')
```

---

### ❌ 500 Internal Server Error

**Error Message:**
```
500 Internal Server Error
This is a Flask crash
```

**Debugging Steps:**

✅ **Step 1: Check Render Logs**
```
Render Dashboard → Your Service → Logs
Look for:
- Traceback errors
- Exception messages
- Line numbers
```

✅ **Step 2: Check MongoDB Connection**
```python
# If using MongoDB, verify:
# 1. Connection string is correct
# 2. Database is accessible from Render
# 3. Firewall allows connections

# Test connection locally:
from pymongo import MongoClient
client = MongoClient('your-connection-string')
print(client.admin.command('ping'))
```

✅ **Step 3: Check for unhandled exceptions**
```python
# Wrap your route handlers:
@app.route('/api/endpoint')
def my_route():
    try:
        # Your code here
        return jsonify(success=True)
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify(error=str(e)), 500
```

✅ **Step 4: Enable debugging (locally only)**
```python
# In application.py - local only, NOT in production
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

### ❌ 502 Bad Gateway

**Error Message:**
```
502 Bad Gateway
Service unreachable
```

**Most Common Causes:**

**1. Port Binding Issue**

✅ **Fix in Procfile:**
```
web: gunicorn -w 2 -b 0.0.0.0:$PORT application:app
```

**Verify:**
- Bind host: `0.0.0.0` ✓
- Bind port: `$PORT` (Render-provided) ✓
- NOT hardcoded port like `:5000` ✗

**2. Startup Timeout**

✅ **If your app takes >60s to start:**
```bash
# In Procfile, increase timeout:
web: gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 application:app
```

**3. Worker Timeout (if job gets stuck)**

✅ **Increase worker timeout:**
```bash
web: gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 --graceful-timeout 30 application:app
```

**4. Too Many Workers for Free Tier**

✅ **Reduce workers (free tier has limited RAM):**
```bash
# Current:  -w 2 (2 workers)
# If still crashing, try:
web: gunicorn -w 1 -b 0.0.0.0:$PORT application:app
```

---

## Common Issues Specific to Your App

### ❌ AI/ML Model Loading Fails

**Error:**
```
Model loading timeout or out of memory
```

**Your app uses:**
- `sentence-transformers` (250MB+)
- `torch` (large dependency)
- `transformers`

✅ **Solutions:**

1. **Load model on-demand (lazy loading):**
```python
# admin/app.py - Instead of loading at startup
model = None

@app.route('/api/endpoint')
def endpoint():
    global model
    if model is None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
    # Now use model
```

2. **Use a paid tier with more resources:**
   - Free tier: 512 MB RAM
   - Starter: 2 GB RAM (recommended for your app)

3. **Install only necessary ML packages:**
```bash
# Check which packages you actually need
# Optionally remove unused ones from requirements.txt
```

---

### ❌ Static Files Not Loading

**Symptoms:**
- CSS/JS not loading (404 errors)
- Images not displaying
- `interior.html` not serving

**Solutions:**

✅ **Check static folder location:**
```bash
# Correct structure:
c:\ecommerce\
├── static/
│   ├── 3d-viewer.js
│   ├── duct-ai.js
│   └── [all static files]
├── admin/
│   ├── app.py
│   └── [admin files]
├── application.py
```

✅ **Verify Flask serves static files:**
```python
# admin/app.py should have:
app = Flask(__name__, 
           static_folder='../static',      # Correct path from admin/ to static/
           static_url_path='/static')
```

✅ **Or serve interior.html from root:**
```python
@app.route('/')
@app.route('/index')
def serve_frontend():
    # Serve interior.html as root page
    return send_from_directory('../', 'interior.html')
```

---

### ❌ Database Connection Issues

**Error:**
```
pymongo.errors.ServerSelectionTimeoutError
SSL connection has been closed unexpectedly
```

**Solutions:**

✅ **If using MongoDB Atlas:**
```python
# In admin/app.py, use connection pooling:
from pymongo import MongoClient
from pymongo.pool import PoolOptions

client = MongoClient(
    'your-connection-string',
    maxPoolSize=5,              # Render has limited connections
    serverSelectionTimeoutMS=5000
)
```

✅ **Add SSL connection:**
```python
client = MongoClient(
    'your-connection-string',
    ssl=True,
    ssl_cert_reqs='CERT_REQUIRED',
    sslmode='require'
)
```

✅ **Firewall: Whitelist Render IP**
- Render uses dynamic IPs
- In MongoDB Atlas: Network Access → Add IP 0.0.0.0/0 (DEVELOPMENT ONLY)

---

## Deployment Checklist

Before deploying to Render:

- [ ] `requirements.txt` is up-to-date (`pip freeze > requirements.txt`)
- [ ] All imports are correct and case-sensitive
- [ ] `application.py` exists at root level
- [ ] `admin/app.py` exists with Flask app
- [ ] `Procfile` has correct build/start commands
- [ ] `render.yaml` is configured (optional, but recommended)
- [ ] All file paths use forward slashes `/` not backslashes `\`
- [ ] No hardcoded `localhost` or `127.0.0.1` in code
- [ ] No hardcoded port numbers (use `$PORT` instead)
- [ ] Environment variables added to Render Dashboard
- [ ] Static files are in correct folder

---

## Testing Before Deployment

```bash
# 1. Verify requirements.txt
pip freeze > requirements.txt
pip install -r requirements.txt --force-reinstall

# 2. Test locally
python application.py
# Visit http://localhost:5000

# 3. Test as Render would run it
gunicorn -w 1 -b 0.0.0.0:5000 application:app
# Visit http://localhost:5000

# 4. Check for common Python issues
python -m py_compile application.py admin/app.py

# 5. Commit and push
git add requirements.txt Procfile render.yaml
git commit -m "fix: deployment configuration"
git push origin main
```

---

## Getting Help

**If your app still doesn't work:**

1. **Check Render Logs** (most important)
   - Dashboard → Your Service → Logs
   - Look for error messages with line numbers

2. **Compare with local test**
   ```bash
   # Run exact same command locally:
   gunicorn -w 2 -b 0.0.0.0:5000 application:app
   ```

3. **Test a minimal Flask app first**
   ```python
   # test_app.py
   from flask import Flask
   app = Flask(__name__)
   
   @app.route('/')
   def hello():
       return 'Hello World!'
   
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=5000)
   ```

4. **Review Render's official docs:**
   - https://render.com/docs/deploy-flask
   - https://render.com/docs/troubleshooting

---

## Quick Reference: Common Fixes

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError` | Add to `requirements.txt`, run `pip freeze` |
| `404 Not Found` | Check static folder path, Flask config |
| `500 Internal Server Error` | Check Render logs, test locally |
| `502 Bad Gateway` | Check Procfile start command, verify port binding |
| `Build failed` | Run `pip install -r requirements.txt` locally |
| `Timeout` | Increase gunicorn `--timeout` value |
| `Memory exceeded` | Reduce workers `-w 1`, upgrade to Starter plan |
| `Database connection` | Whitelist Render IPs, check connection string |

---

## Success! 🎉

Once deployment succeeds:
- You'll see "Live" status in Render Dashboard
- Your app will be available at `https://interior-ecommerce.onrender.com`
- Any git pushes to `main` will auto-deploy

Good luck! 🚀
