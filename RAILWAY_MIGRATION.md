# Railway Migration Guide: Render → Railway

Comprehensive guide for migrating Interior Ecommerce backend from Render to Railway with Cloudflare DNS and AWS S3 integration.

---

## Table of Contents
1. [Pre-Migration Checklist](#pre-migration-checklist)
2. [Step 1: Local Testing](#step-1-local-testing)
3. [Step 2: Create Railway Service](#step-2-create-railway-service)
4. [Step 3: Configure Environment Variables](#step-3-configure-environment-variables)
5. [Step 4: Deploy to Railway](#step-4-deploy-to-railway)
6. [Step 5: Configure Custom Domain](#step-5-configure-custom-domain)
7. [Step 6: Verify Deployment](#step-6-verify-deployment)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Plan](#rollback-plan)

---

## Pre-Migration Checklist

Before starting the migration, ensure you have:

- [ ] **Railway account** — Create at https://railway.app
- [ ] **Railway CLI installed** — `npm install -g @railway/cli` or `brew install railway`
- [ ] **AWS credentials** — Access key ID and secret key for S3
- [ ] **All API keys** — Gemini, OpenAI, Anthropic, Stripe, Paystack (if used)
- [ ] **MongoDB URI** — If you use MongoDB
- [ ] **Current Render service running** — For comparison during testing
- [ ] **Git repo up-to-date** — All changes committed
- [ ] **Domain access** — Route 53 and Cloudflare DNS control

### Verify Current Render Deployment
```bash
# Check if current Render service is working
curl https://your-current-render-domain.onrender.com/health
# Should return 200 OK
```

---

## Step 1: Local Testing

### 1.1 Test Dependencies
```bash
# Activate virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Install dependencies (same as Railway will use)
pip install -r requirements.txt

# Verify no errors
echo "Build successful!"
```

### 1.2 Test Flask App Locally
```bash
# Copy .env.example to .env and fill in your secrets
cp .env.example .env

# Edit .env with your actual credentials:
# - ADMIN_SECRET_KEY
# - AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
# - GEMINI_API_KEY
# - MONGO_URI (if applicable)
# etc.

# Run Flask app locally
python application.py

# Test in another terminal
curl http://localhost:5000/health
# Should return 200 OK with health status
```

### 1.3 Test AWS S3 Integration
```bash
# With .env configured and app running:
curl -X POST http://localhost:5000/api/test-s3 \
  -H "Content-Type: application/json" \
  -d '{"test": "file"}'

# Should return success or clear error indicating S3 issue
# Check logs for "S3 connection successful" or AWS error details
```

### 1.4 Test AI Provider Integration
```bash
# Test Gemini API
curl -X POST http://localhost:5000/api/test-ai \
  -H "Content-Type: application/json" \
  -d '{"provider": "gemini", "prompt": "test"}'

# Should return AI response or clear error
```

---

## Step 2: Create Railway Service

### 2.1 Option A: Using Railway CLI (Recommended)
```bash
# Login to Railway
railway login

# Create new project
railway init

# Select "Python" as framework
# Name project: "interior-ecommerce"

# This creates a railway.json and links your local repo
```

### 2.2 Option B: Using Railway Dashboard
1. Go to https://railway.app/dashboard
2. Click **New Project**
3. Select **Deploy from GitHub**
4. Connect your GitHub repo (Barth-cyber/interior-ecommerce)
5. Select the correct branch/worktree
6. Railway auto-detects Python from Procfile
7. Click **Deploy**

### 2.3 Verify Railway Detected Configuration
```bash
# If using CLI, verify settings
railway status

# Should show:
# - Python 3.11.9 (detected from render.yaml or railway.toml)
# - Gunicorn start command
# - Port 8000 (Railway's default)
```

---

## Step 3: Configure Environment Variables

### 3.1 Set Environment Variables in Railway Dashboard

Go to **Railway Dashboard** → Your Project → **Variables** tab:

**Critical Secrets** (set these first):
```
ADMIN_SECRET_KEY = [Generate secure random value, min 32 chars]
ADMIN_PASSWORD_HASH = [Use: python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YourPassword'))"]
```

**AWS S3 Configuration**:
```
AWS_ACCESS_KEY_ID = [Your AWS IAM access key]
AWS_SECRET_ACCESS_KEY = [Your AWS IAM secret key]
AWS_S3_BUCKET_NAME = interior-ecommerce-prod
AWS_S3_REGION = us-east-1  # or appropriate region
```

**AI Provider Keys**:
```
GEMINI_API_KEY = [Your Google Gemini API key]
OPENAI_API_KEY = [Your OpenAI API key - optional]
ANTHROPIC_API_KEY = [Your Anthropic API key - optional]
```

**Database** (if applicable):
```
MONGO_URI = [Your MongoDB connection string]
```

**Payment Providers** (if applicable):
```
STRIPE_SECRET_KEY = [Your Stripe secret key]
STRIPE_PUBLISHABLE_KEY = [Your Stripe publishable key]
STRIPE_WEBHOOK_SECRET = [Your Stripe webhook secret]
PAYSTACK_SECRET_KEY = [Your Paystack secret key]
PAYSTACK_PUBLIC_KEY = [Your Paystack public key]
```

**Application Settings**:
```
FLASK_ENV = production
PYTHONUNBUFFERED = true
ADMIN_USERNAME = admin
ADMIN_COOKIE_SECURE = true  # Enable in production
```

### 3.2 Verify Variables Are Set
```bash
# If using CLI
railway env

# Should show all variables set (secrets will be masked)
```

---

## Step 4: Deploy to Railway

### 4.1 Using Railway CLI
```bash
# Trigger deployment from current branch
railway up

# Or deploy from main branch
railway deploy --branch main

# Watch logs during deployment
railway logs --follow

# Should see:
# - Python 3.11.9 installed
# - Dependencies installing (pip install -r requirements.txt)
# - Gunicorn starting on port $PORT
# - "Application ready" message
```

### 4.2 Using Railway Dashboard
1. Dashboard → Your Project → **Deployments**
2. Should show green checkmark if deployment successful
3. Click **View Logs** to see deployment output

### 4.3 Get Railway Backend URL
```bash
# Railway generates a public URL automatically
railway env | grep RAILWAY_PUBLIC_DOMAIN
# Output: interior-ecommerce-api.railway.app (example)

# Or from Dashboard: Settings → Domain
# Copy the Railway-generated domain
```

**Important**: Keep this URL handy for Step 5!

---

## Step 5: Configure Custom Domain

### 5.1 Update Route 53 (DNS Registration)

You have two options:

**Option A: CNAME via Cloudflare (Recommended)**
- Route 53 remains unchanged (points to Cloudflare nameservers)
- Cloudflare handles the CNAME to Railway
- See Step 5.2

**Option B: Direct CNAME in Route 53**
1. Route 53 Console → Your Hosted Zone
2. Create new record:
   - **Name**: `api.yourdomain.com` (or your subdomain)
   - **Type**: CNAME
   - **Value**: `interior-ecommerce-api.railway.app` (your Railway domain)
   - **TTL**: 300
3. Click **Create**

### 5.2 Update Cloudflare DNS (Recommended)

1. **Cloudflare Dashboard** → Your Domain → **DNS**
2. Add new record:
   - **Type**: CNAME
   - **Name**: `api` (or your subdomain)
   - **Content**: `interior-ecommerce-api.railway.app`
   - **TTL**: Auto
   - **Proxy status**: Proxied (orange cloud)
3. Click **Save**

### 5.3 Set Custom Domain in Railway

1. **Railway Dashboard** → Your Project → **Settings** → **Domains**
2. Click **Add Domain**
3. Enter: `api.yourdomain.com`
4. Railway will validate the CNAME record
5. Once validated, HTTPS is automatically enabled (Cloudflare handles SSL)

### 5.4 Verify DNS Resolution
```bash
# Wait 2-5 minutes for DNS propagation

# Test CNAME resolution
nslookup api.yourdomain.com

# Should resolve to Railway backend IP

# Test HTTPS connection
curl https://api.yourdomain.com/health

# Should return 200 OK with backend response
```

---

## Step 6: Verify Deployment

### 6.1 Health Check
```bash
# Test basic connectivity
curl https://api.yourdomain.com/health

# Response should be:
# {"status": "ok", "timestamp": "2024-05-17T..."}
```

### 6.2 Test Key Endpoints

**S3 Integration**:
```bash
curl https://api.yourdomain.com/api/test-s3 \
  -H "Content-Type: application/json" \
  -d '{"test": "file"}'
```

**AI Integration**:
```bash
curl https://api.yourdomain.com/api/test-ai \
  -H "Content-Type: application/json" \
  -d '{"provider": "gemini", "prompt": "Hello"}'
```

**Admin Login** (if applicable):
```bash
curl -X POST https://api.yourdomain.com/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "YOUR_PASSWORD"}'
```

### 6.3 Check Railway Logs
```bash
# View deployment logs
railway logs --follow

# Look for:
# - No Python errors
# - No module import failures
# - "Application running" message
# - Requests hitting the API
```

### 6.4 Monitor Cloudflare CDN

1. **Cloudflare Dashboard** → Your Domain → **Analytics**
2. Check that traffic is being proxied
3. Look for cache hit ratio (should increase over time)
4. Verify no 5xx errors

### 6.5 Test End-to-End

From **Cloudflare Pages frontend**:
```javascript
// In your frontend code
fetch('https://api.yourdomain.com/health')
  .then(r => r.json())
  .then(data => console.log('Backend healthy:', data))
  .catch(err => console.error('Backend offline:', err))
```

Should see "Backend healthy" message in console.

---

## Troubleshooting

### Issue: "502 Bad Gateway" from Cloudflare

**Cause**: Railway backend not responding or crashed

**Solutions**:
1. Check Railway logs: `railway logs --follow`
2. Verify environment variables are set correctly
3. Test directly on Railway domain (without Cloudflare):
   ```bash
   curl https://interior-ecommerce-api.railway.app/health
   ```
4. If Railway domain fails, issue is in backend code or env vars
5. If Railway succeeds but Cloudflare fails, check DNS/SSL settings

### Issue: "Connection timeout" after deployment

**Cause**: Application startup taking too long or dependency issue

**Solutions**:
1. Check if all dependencies installed: `railway logs | grep "pip install"`
2. Look for Python syntax errors: `railway logs | grep "SyntaxError"`
3. Increase Railway plan resources (if needed) for faster boot
4. Check for blocking imports or large file loads in app.py

### Issue: S3 upload failing (403 Forbidden)

**Cause**: AWS credentials invalid or insufficient permissions

**Solutions**:
1. Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in Railway env vars
2. Check AWS IAM policy allows S3 PutObject on your bucket
3. Test locally with same credentials:
   ```bash
   export AWS_ACCESS_KEY_ID=...
   export AWS_SECRET_ACCESS_KEY=...
   python test_s3_interactive.py
   ```

### Issue: AI API not working (401 Unauthorized)

**Cause**: API key invalid or expired

**Solutions**:
1. Verify API key in Railway env vars
2. Test API key locally:
   ```bash
   export GEMINI_API_KEY=...
   python test_ai_query.py
   ```
3. Check if API key has correct permissions/quotas
4. Regenerate API key in provider dashboard if needed

### Issue: Custom domain not resolving

**Cause**: CNAME not propagated or misconfigured

**Solutions**:
1. Verify CNAME record in Cloudflare DNS:
   ```bash
   nslookup api.yourdomain.com
   ```
2. Ensure Railway domain is correctly entered in Railway Settings → Domains
3. Wait 5-10 minutes for DNS propagation
4. Clear Cloudflare cache if recently changed:
   - Dashboard → Caching → Purge Cache

---

## Rollback Plan

If deployment has critical issues:

### 1. Immediate Rollback (Keep Render running)
```bash
# Point custom domain back to Render
# In Cloudflare DNS → Edit CNAME
# Change from: interior-ecommerce-api.railway.app
# Change to: interior-ecommerce.onrender.com (your Render domain)

# Wait for DNS propagation (2-5 minutes)
curl https://api.yourdomain.com/health
# Should now hit Render backend
```

### 2. Delete Railway Deployment (Temporary)
```bash
# If Railway causes issues, pause or delete the service
railway service delete

# Keep Railway project data intact for diagnostics
```

### 3. Investigate & Redeploy
```bash
# After fixing issue, redeploy
railway deploy --branch main

# Gradually switch back to Railway after verification
```

---

## Post-Migration Cleanup

Once Railway is stable and handling traffic:

### 1. Disable Render Service
- Render Dashboard → Your Service → **Settings** → **Suspend/Delete**
- Keep for 24-48 hours as backup before full deletion

### 2. Update Documentation
- [ ] Update README.md to reference Railway instead of Render
- [ ] Update team wiki/docs with new backend URL
- [ ] Archive Render troubleshooting guide

### 3. Monitor & Optimize
```bash
# Monitor Railway metrics
railway logs --follow
railway status

# Cloudflare Analytics
# - Track cache hit ratio
# - Monitor API response times
# - Watch for errors
```

### 4. Optional: Set Up Railway Alerts
- Dashboard → Notifications → Add email alerts for crashes/errors
- Configure Railway to notify on deployment failures

---

## Success Indicators

Your migration is successful when:

✅ `curl https://api.yourdomain.com/health` returns 200 OK
✅ S3 file uploads work through API
✅ AI integrations respond correctly
✅ MongoDB queries work (if applicable)
✅ Cloudflare shows traffic being proxied
✅ No 5xx errors in Cloudflare Analytics
✅ Frontend successfully calls backend API
✅ Payment providers work (if applicable)
✅ No warnings or errors in Railway logs for 24+ hours

---

## Support & Resources

- **Railway Docs**: https://docs.railway.app
- **Railway Status**: https://status.railway.app
- **Cloudflare DNS Docs**: https://developers.cloudflare.com/dns/
- **AWS S3 Docs**: https://docs.aws.amazon.com/s3/
- **Flask Docs**: https://flask.palletsprojects.com/

For issues, check `DEPLOYMENT_TROUBLESHOOTING.md` and this file for specific error messages.
