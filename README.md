# interior-ecommerce

Ecommerce Website with AI-powered interior design assistant, built with Flask backend, Cloudflare Pages frontend, AWS S3 storage, and MongoDB database.

---

## 🚀 Deployment Architecture

```
Route 53 (Domain Registration)
    ↓
Cloudflare (DNS + SSL + CDN)
    ├→ Frontend: Cloudflare Pages
    └→ Backend: Railway (Python Flask)
       ├→ Storage: AWS S3
       └→ Email: Zoho Mail
```

---

## 📋 Deployment Guides

### Backend (Flask API)

The backend is deployed on **Railway** (migrated from Render).

#### Quick Start

```bash
# 1. Local setup
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys, AWS credentials, etc.

# 3. Run locally
python application.py
# Open http://localhost:5000
```

#### Deploy to Railway

See **[RAILWAY_MIGRATION.md](./RAILWAY_MIGRATION.md)** for complete step-by-step guide:

- [Pre-Migration Checklist](./RAILWAY_MIGRATION.md#pre-migration-checklist)
- [Local Testing](./RAILWAY_MIGRATION.md#step-1-local-testing)
- [Create Railway Service](./RAILWAY_MIGRATION.md#step-2-create-railway-service)
- [Configure Environment Variables](./RAILWAY_MIGRATION.md#step-3-configure-environment-variables)
- [Deploy & Verify](./RAILWAY_MIGRATION.md#step-6-verify-deployment)

#### Post-Deployment Verification

Use **[RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)** to verify:

- ✅ Backend responding to requests
- ✅ S3 storage integration working
- ✅ AI providers (Gemini, OpenAI, Anthropic) connected
- ✅ Database (MongoDB) accessible
- ✅ Frontend can call backend API

#### DNS Configuration

See **[RAILWAY_DNS_SETUP.md](./RAILWAY_DNS_SETUP.md)** to configure:

- Route 53 → Cloudflare nameservers
- Cloudflare DNS records (CNAME to Railway backend)
- SSL/TLS certificates
- Cloudflare Page Rules for caching

### Frontend (Cloudflare Pages)

Frontend is hosted on Cloudflare Pages. See `COMPLETE_SYSTEM_GUIDE.md` for setup.

### Storage (AWS S3)

S3 configuration details in `S3_SETUP_GUIDE.md`.

### Email (Zoho Mail)

Email configuration in `COMPLETE_SYSTEM_GUIDE.md` (DNS MX records).

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [RAILWAY_MIGRATION.md](./RAILWAY_MIGRATION.md) | **Start here** - Step-by-step Render→Railway migration guide |
| [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) | Post-deployment verification checklist and troubleshooting |
| [RAILWAY_DNS_SETUP.md](./RAILWAY_DNS_SETUP.md) | Route53 + Cloudflare + Railway DNS configuration |
| [COMPLETE_SYSTEM_GUIDE.md](./COMPLETE_SYSTEM_GUIDE.md) | Full system architecture and component setup |
| [DEPLOYMENT_TROUBLESHOOTING.md](./DEPLOYMENT_TROUBLESHOOTING.md) | Render deployment issues (archived) |
| [S3_SETUP_GUIDE.md](./S3_SETUP_GUIDE.md) | AWS S3 configuration for file storage |
| [TESTING_GUIDE.md](./TESTING_GUIDE.md) | Running tests and diagnostics |
| [MONGODB_INTEGRATION.md](./MONGODB_INTEGRATION.md) | MongoDB setup and usage |

---

## 🏗️ Project Structure

```
.
├── app.py                      # Flask application (main logic)
├── application.py              # Render/Railway entrypoint
├── requirements.txt            # Python dependencies
├── Procfile                    # Process definition (Render/Railway)
├── render.yaml                 # Render configuration (archived)
├── railway.json               # Railway configuration
├── railway.toml               # Railway CLI config
│
├── templates/                 # HTML templates (Jinja2)
├── static/                    # CSS, JS, images
│
├── admin/                     # Admin panel code
├── duct-ai-backend/           # AI assistant backend
├── project_gemini/            # Gemini integration
│
├── scripts/                   # Utility scripts
├── tests/                     # Test files
│
└── docs/
    ├── RAILWAY_MIGRATION.md   # Railway deployment guide
    ├── RAILWAY_DNS_SETUP.md   # DNS configuration
    ├── RAILWAY_DEPLOYMENT.md  # Post-deployment checklist
    └── ...
```

---

## 🔐 Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

Key variables:

- **Flask Security**: `ADMIN_SECRET_KEY`, `ADMIN_PASSWORD_HASH`
- **AWS S3**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET_NAME`
- **AI APIs**: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- **Database**: `MONGO_URI` (MongoDB connection string)
- **Payment**: `STRIPE_*`, `PAYSTACK_*` (if needed)

For Railway: Set these in **Railway Dashboard → Variables**

---

## 🧪 Testing

```bash
# Run local development server
python application.py

# Test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/api/products

# Run test suite (see TESTING_GUIDE.md)
python test_routes.py
python test_s3_interactive.py
python test_ai_query.py
```

---

## 📊 Architecture Details

### Stack Components

- **Frontend**: Cloudflare Pages (React/Vue/static HTML)
- **Backend**: Flask (Python 3.11.9) on Railway
- **Storage**: AWS S3 (images, documents, uploads)
- **Database**: MongoDB (optional, for users/orders/inventory)
- **AI**: Google Gemini, OpenAI, Anthropic APIs
- **Payments**: Stripe, Paystack (optional)
- **Email**: Zoho Mail
- **CDN/DNS**: Cloudflare (SSL, caching, DDoS protection)

### Data Flow

```
Client Browser (Cloudflare Pages)
    ↓ HTTPS request to api.yourdomain.com
Cloudflare CDN (cached if possible)
    ↓
Railway Backend (Flask API)
    ├→ Database (MongoDB)
    ├→ Storage (AWS S3)
    └→ AI APIs (Gemini/OpenAI/Anthropic)
    ↓
Response back through Cloudflare CDN
    ↓
Browser renders response
```

---

## 🔧 Common Tasks

### Add New Endpoint

1. Edit `app.py`
2. Define Flask route:
   ```python
   @app.route('/api/new-endpoint', methods=['GET', 'POST'])
   def new_endpoint():
       return jsonify({"status": "ok"})
   ```
3. Test locally: `python application.py`
4. Deploy: `railway deploy` or push to Git (Railway auto-deploys)

### Update Dependencies

```bash
# Add package
pip install new-package
pip freeze > requirements.txt

# Deploy to Railway (auto-detects changes)
git add requirements.txt
git commit -m "Add new-package"
git push
```

### Deploy New Version

```bash
# Option 1: Git push (Railway auto-deploys)
git commit -am "Update backend logic"
git push origin main

# Option 2: Manual Railway CLI
railway deploy --branch main

# Monitor deployment
railway logs --follow
```

### Rollback to Render (Emergency)

If Railway has critical issues, temporarily switch back to Render:

1. Get Render domain
2. Update Cloudflare DNS CNAME `api` record to point to Render
3. Wait 5 minutes for DNS propagation
4. Investigate Railway issue in logs

See **RAILWAY_MIGRATION.md → Rollback Plan** for details.

---

## 🐛 Troubleshooting

### Backend not responding (502 Bad Gateway)

```bash
# Check Railway logs
railway logs --follow

# Verify environment variables
railway env

# Test local build
pip install -r requirements.txt
python application.py
```

### S3 upload failing

```bash
# Test S3 credentials locally
python test_s3_interactive.py

# Verify AWS IAM policy allows S3 PutObject
```

### AI API returns 401

```bash
# Check API keys in Railway env vars
railway env | grep GEMINI

# Verify API key is valid in provider dashboard
```

### CORS error from frontend

```python
# Ensure flask-cors is enabled in app.py
from flask_cors import CORS
CORS(app)
```

See **DEPLOYMENT_TROUBLESHOOTING.md** and **RAILWAY_DEPLOYMENT.md** for more.

---

## 📖 Git Commit Guidelines

Use the `.gitmessage.txt` template:

```bash
# Use template for commits
git commit  # (without -m, opens template in editor)

# Write:
# [First line: short imperative summary]
# 
# [Detailed explanation of why this change was made]
# [Any follow-up notes or decisions]
```

---

## 🚀 Getting Help

- **Railway Docs**: https://docs.railway.app
- **Flask Docs**: https://flask.palletsprojects.com/
- **AWS S3 Docs**: https://docs.aws.amazon.com/s3/
- **Cloudflare Docs**: https://developers.cloudflare.com/
- **MongoDB Docs**: https://docs.mongodb.com/

Check documentation files in this repo first, then consult official docs.

---

## 📄 License & Status

Production-grade architecture for **Interior Duct Ltd**.

Status: ✅ Migrated from Render to Railway (May 2024)
