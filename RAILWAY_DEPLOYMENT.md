# Railway Deployment Verification Checklist

Post-deployment verification steps to ensure your Interior Ecommerce backend is running correctly on Railway with full integration to Cloudflare, S3, and AI providers.

---

## Pre-Verification Requirements

- [ ] Railway deployment completed (status shows "active" in dashboard)
- [ ] Custom domain configured in Railway (e.g., `api.yourdomain.com`)
- [ ] DNS records created and propagated (CNAME in Cloudflare)
- [ ] All environment variables set in Railway Dashboard
- [ ] SSL certificate issued and active

---

## 1. Basic Connectivity

### 1.1 Railway Public Domain (Direct Test)

```bash
# Test Railway backend directly (bypasses Cloudflare)
curl -I https://interior-ecommerce-api.railway.app/health

# Expected response:
# HTTP/2 200
# Server: gunicorn
# CF-RAY: xxx
```

**Status**: ✅ ❌ 

**If fails**: 
- Check Railway logs: `railway logs --follow`
- Verify environment variables: `railway env`
- Ensure Python dependencies installed: `railway logs | grep "pip install"`

### 1.2 Custom Domain (Via Cloudflare)

```bash
# Test via custom domain (through Cloudflare CDN)
curl -I https://api.yourdomain.com/health

# Expected response:
# HTTP/2 200
# CF-Cache-Status: MISS or HIT
# CF-Ray: [ray-id]
```

**Status**: ✅ ❌ 

**If fails**:
- Verify DNS resolution: `nslookup api.yourdomain.com`
- Check Cloudflare SSL/TLS setting (should be "Full")
- Verify Railway custom domain settings
- Wait 5 minutes for DNS propagation if recently changed

### 1.3 Health Endpoint Response

```bash
# Get full response
curl https://api.yourdomain.com/health

# Expected output:
# {"status": "ok", "timestamp": "2024-05-17T15:46:15Z", ...}
```

**Status**: ✅ ❌ 

**Response format**: 

```json
{
  "status": "ok",
  "timestamp": "...",
  "app": "interior-ecommerce",
  "version": "..."
}
```

---

## 2. Application Functionality

### 2.1 Flask App Routes

```bash
# Test main routes
curl https://api.yourdomain.com/
curl https://api.yourdomain.com/admin
curl https://api.yourdomain.com/products

# Should return HTML or JSON, not 404 or 500
```

**Status**: ✅ ❌ 

**Common issues**:
- If 500: Check `railway logs` for Python errors
- If 404: Verify routes defined in app.py
- If slow: May be first request after cold start, test again

### 2.2 CORS Headers (Frontend Integration)

```bash
# Test CORS headers (used by Cloudflare Pages frontend)
curl -H "Origin: https://yourdomain.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://api.yourdomain.com/api/products

# Expected headers in response:
# Access-Control-Allow-Origin: https://yourdomain.com
# Access-Control-Allow-Methods: GET, POST, OPTIONS
# Access-Control-Allow-Headers: Content-Type
```

**Status**: ✅ ❌ 

**If missing CORS headers**:
- Verify FLASK_CORS configuration in app.py
- Check that flask-cors is installed: `railway env | grep flask`
- Restart Railway service after adding CORS

---

## 3. AWS S3 Integration

### 3.1 Environment Variables

```bash
# Verify S3 credentials set (should be masked)
railway env | grep AWS

# Should show:
# AWS_ACCESS_KEY_ID [redacted]
# AWS_SECRET_ACCESS_KEY [redacted]
# AWS_S3_BUCKET_NAME interior-ecommerce-prod
# AWS_S3_REGION us-east-1
```

**Status**: ✅ ❌ 

**If missing**: Set variables in Railway Dashboard → Variables

### 3.2 S3 Connectivity Test

```bash
# Test S3 upload endpoint (if available)
curl -X POST https://api.yourdomain.com/api/upload \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.txt", "content": "test data"}'

# Expected response:
# {"url": "https://your-bucket.s3.amazonaws.com/test.txt", "status": "success"}
```

**Status**: ✅ ❌ 

**If fails with 403 Forbidden**:
- AWS IAM access key invalid or expired
- Verify AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
- Check AWS IAM policy allows S3 PutObject
- Run locally: `python test_s3_interactive.py` for diagnostics

### 3.3 S3 File Retrieval

```bash
# Test reading previously uploaded files
curl https://your-bucket.s3.amazonaws.com/path/to/file.jpg

# Should return the file contents or 200 OK
```

**Status**: ✅ ❌ 

**If 403 Forbidden**:
- S3 bucket policy may not allow public read
- If behind Cloudflare CDN: Check bucket CORS settings
- Verify object ACL allows read access

### 3.4 S3 CDN Subdomain (if configured)

```bash
# If you have cdn.yourdomain.com CNAME to S3
curl https://cdn.yourdomain.com/path/to/file.jpg

# Should return the file (cached via Cloudflare)
```

**Status**: ✅ ❌ 

**If fails**:
- Verify CNAME record exists in Cloudflare DNS
- Ensure S3 bucket is configured for website hosting
- Check S3 CORS policy allows Cloudflare IPs

---

## 4. AI Provider Integration

### 4.1 Google Gemini API

```bash
# Test Gemini integration
curl -X POST https://api.yourdomain.com/api/ai/gemini \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, test this API"}'

# Expected response (successful):
# {"response": "...", "provider": "gemini", "tokens_used": 123}

# Expected response (error):
# {"error": "GEMINI_API_KEY not set", "status": 500}
```

**Status**: ✅ ❌ 

**If fails with 401 Unauthorized**:
- GEMINI_API_KEY not set in Railway env vars
- API key expired or invalid
- Regenerate in Google Cloud Console

### 4.2 OpenAI API (if configured)

```bash
curl -X POST https://api.yourdomain.com/api/ai/openai \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "model": "gpt-3.5-turbo"}'

# Expected response:
# {"response": "...", "provider": "openai", "tokens_used": 50}
```

**Status**: ✅ ❌ 

**If fails**:
- OPENAI_API_KEY not set (optional, test only if configured)
- API key invalid or rate limited
- Model not available on account

### 4.3 Anthropic Claude (if configured)

```bash
curl -X POST https://api.yourdomain.com/api/ai/claude \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, Claude"}'

# Expected response:
# {"response": "...", "provider": "anthropic", "tokens_used": 100}
```

**Status**: ✅ ❌ 

**If fails**:
- ANTHROPIC_API_KEY not set (optional)
- Anthropic API experiencing issues
- Rate limit hit

---

## 5. Database Connection (MongoDB)

### 5.1 MongoDB URI Configuration

```bash
# Check if MongoDB configured
railway env | grep MONGO

# Should show:
# MONGO_URI mongodb+srv://user:pass@cluster.mongodb.net/dbname
```

**Status**: ✅ ❌ 

**If missing**: May be optional, skip to 5.3

### 5.2 Database Operations Test

```bash
# Test database read/write
curl -X POST https://api.yourdomain.com/api/db/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Expected response:
# {"status": "connected", "inserted_id": "...", "query_time_ms": 45}
```

**Status**: ✅ ❌ 

**If fails with "Connection timeout"**:
- MongoDB URI invalid or cluster offline
- IP whitelist issue: MongoDB Atlas may need Cloudflare IPs whitelisted
- Verify MongoDB credentials in MONGO_URI

### 5.3 MongoDB IP Whitelist (if needed)

If MongoDB connection fails:

```
MongoDB Atlas Console → Network Access → IP Whitelist
Add: 0.0.0.0/0 (allow all) OR
Add: Cloudflare IP ranges (if restricting)
```

---

## 6. Authentication & Admin Panel

### 6.1 Admin Credentials

```bash
# Verify admin credentials set
railway env | grep ADMIN

# Should show:
# ADMIN_USERNAME admin
# ADMIN_PASSWORD_HASH [redacted]
# ADMIN_SECRET_KEY [redacted]
```

**Status**: ✅ ❌ 

**If missing**:
- Generate password hash: `python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YourPassword'))"`
- Set ADMIN_PASSWORD_HASH in Railway variables
- Restart service

### 6.2 Admin Login

```bash
# Test admin login
curl -X POST https://api.yourdomain.com/admin/login \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"username": "admin", "password": "YOUR_PASSWORD"}'

# Expected response:
# {"status": "success", "session_id": "...", "username": "admin"}
```

**Status**: ✅ ❌ 

**If fails with 401 Unauthorized**:
- Wrong password or username
- ADMIN_PASSWORD_HASH not set correctly
- Session management not working (check Flask session config)

---

## 7. Payment Integration

### 7.1 Stripe Configuration

```bash
# Verify Stripe credentials
railway env | grep STRIPE

# Should show:
# STRIPE_SECRET_KEY [redacted]
# STRIPE_PUBLISHABLE_KEY [redacted]
# STRIPE_WEBHOOK_SECRET [redacted]
```

**Status**: ✅ ❌ 

### 7.2 Stripe Webhook Test

```bash
# List recent webhook events
curl -u sk_test_...: https://api.stripe.com/v1/events?limit=5

# Should show webhook events if configured
```

**Status**: ✅ ❌ 

### 7.3 Paystack Configuration

```bash
# Verify Paystack credentials
railway env | grep PAYSTACK

# Should show:
# PAYSTACK_SECRET_KEY [redacted]
# PAYSTACK_PUBLIC_KEY [redacted]
```

**Status**: ✅ ❌ 

---

## 8. Static Files & CDN

### 8.1 Static Content Serving

```bash
# Test CSS, JS, images
curl -I https://api.yourdomain.com/static/style.css
curl -I https://api.yourdomain.com/static/app.js
curl -I https://api.yourdomain.com/favicon.png

# Expected response:
# HTTP/2 200
# Content-Type: text/css (or application/javascript, image/png)
# CF-Cache-Status: HIT (after first request)
```

**Status**: ✅ ❌ 

**If 404**:
- Static files not in Flask app `/static` directory
- Verify file paths in templates
- Check gunicorn is serving static files

### 8.2 Cloudflare Cache Status

```bash
# Check cache effectiveness
curl -I https://api.yourdomain.com/static/style.css | grep CF-Cache

# Expected progression:
# First request: CF-Cache-Status: MISS
# Subsequent requests: CF-Cache-Status: HIT

# For API endpoints (should NOT cache):
curl -I https://api.yourdomain.com/api/products | grep CF-Cache
# Should be: BYPASS or MISS (not HIT)
```

**Status**: ✅ ❌ 

**If everything is MISS**:
- Check Cloudflare Page Rules for cache settings
- Verify Cache-Control headers from backend
- Add Page Rule: `api.yourdomain.com/static/* → Cache Everything`

---

## 9. Performance & Monitoring

### 9.1 Response Time

```bash
# Measure API response time
time curl https://api.yourdomain.com/health

# Acceptable ranges:
# First request after cold start: 1-5 seconds
# Warm requests: 100-500ms
# Static cached content: 50-200ms via Cloudflare CDN
```

**Status**: ✅ ❌ 

**If very slow (> 10 seconds)**:
- Check Railway logs for errors: `railway logs --follow`
- May indicate cold start or overload
- Consider upgrading Railway plan

### 9.2 Railway Logs

```bash
# Monitor live logs
railway logs --follow

# Look for:
# ✅ No error messages
# ✅ Gunicorn startup message
# ✅ Requests being processed
# ✅ No module import errors

# Should NOT see:
# ❌ ModuleNotFoundError
# ❌ SyntaxError in app
# ❌ "Connection refused"
```

**Status**: ✅ ❌ 

### 9.3 Cloudflare Analytics

1. **Cloudflare Dashboard** → Analytics → Domain

```
Metrics to check:
- Requests: Should show traffic to api.yourdomain.com
- Cached: High cache hit ratio (> 50% for CDN)
- Bandwidth saved: How much Cloudflare cached
- Errors: 5xx should be low (< 1%), 4xx acceptable
```

**Status**: ✅ ❌ 

---

## 10. Frontend Integration

### 10.1 Frontend Calling Backend

In your **Cloudflare Pages frontend** (React/Vue/HTML):

```javascript
// Test from frontend console
fetch('https://api.yourdomain.com/health')
  .then(r => r.json())
  .then(data => console.log('Backend healthy:', data))
  .catch(err => console.error('Backend error:', err))

// Should log: Backend healthy: {status: "ok", ...}
```

**Status**: ✅ ❌ 

**If fails with CORS error**:
- Backend not sending CORS headers
- Check Cloudflare Page Rules don't block CORS
- Verify flask-cors middleware enabled in app.py

### 10.2 Frontend API Calls

```javascript
// Example: Load products from backend
fetch('https://api.yourdomain.com/api/products')
  .then(r => r.json())
  .then(data => console.log('Products:', data.products))

// Should return product list
```

**Status**: ✅ ❌ 

---

## 11. Security Checks

### 11.1 HTTPS Enforcement

```bash
# Test HTTP redirect to HTTPS
curl -I http://api.yourdomain.com/

# Expected response:
# HTTP/1.1 301 Moved Permanently
# Location: https://api.yourdomain.com/
```

**Status**: ✅ ❌ 

### 11.2 Security Headers

```bash
# Check security headers
curl -I https://api.yourdomain.com/ | grep -i "X-"

# Should include:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY or SAMEORIGIN
# Strict-Transport-Security: (if configured)
```

**Status**: ✅ ❌ 

### 11.3 SSL Certificate Validity

```bash
# Check certificate
openssl s_client -connect api.yourdomain.com:443 -showcerts < /dev/null

# Should show:
# ✅ Subject: *.yourdomain.com (or yourdomain.com)
# ✅ Issuer: Cloudflare
# ✅ Valid from: [past date]
# ✅ Valid until: [future date]
```

**Status**: ✅ ❌ 

---

## Final Verification Summary

### 12.1 Success Checklist

- [ ] ✅ Health endpoint responds (HTTP 200)
- [ ] ✅ Custom domain resolves (DNS working)
- [ ] ✅ CORS headers present (frontend can call backend)
- [ ] ✅ S3 uploads working (file storage functional)
- [ ] ✅ AI APIs responding (Gemini/OpenAI/Claude)
- [ ] ✅ MongoDB connected (if configured)
- [ ] ✅ Admin login works (authentication functional)
- [ ] ✅ Static files cached (Cloudflare CDN active)
- [ ] ✅ Logs show no errors (application healthy)
- [ ] ✅ Response times acceptable (< 500ms warm)
- [ ] ✅ Frontend can call backend (full integration)
- [ ] ✅ HTTPS working (certificate valid)

### 12.2 Deployment Status

**All checks passing**: ✅ DEPLOYMENT SUCCESSFUL

**Some checks failing**: ⚠️ INVESTIGATE FAILURES (see troubleshooting)

**Critical check failing**: ❌ DEPLOYMENT NOT READY (rollback to Render)

---

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | Check Railway logs: `railway logs --follow` |
| DNS not resolving | Wait 5 min for propagation or `ipconfig /flushdns` |
| S3 upload fails (403) | Verify AWS credentials and IAM policy |
| AI API 401 error | Check API keys set in Railway env vars |
| CORS error from frontend | Enable flask-cors in app.py |
| Slow response times | Check for Python errors in logs or upgrade plan |
| Certificate error | Set Cloudflare SSL/TLS to "Full" |
| Cloudflare cache not working | Add Page Rule for static files |

---

## Next Steps

After verification, implement:

1. **Monitoring**: Set up Railway alerts for errors/crashes
2. **Logging**: Configure log aggregation if needed
3. **Backups**: Set up MongoDB backups (if using)
4. **Scaling**: Monitor metrics, upgrade Railway plan if needed
5. **Updates**: Plan regular dependency updates
6. **Testing**: Set up automated API health checks
7. **Documentation**: Update team docs with new backend URL

---

## Support

- **Railway Docs**: https://docs.railway.app
- **Cloudflare Support**: https://support.cloudflare.com
- **AWS S3 Support**: https://docs.aws.amazon.com/s3/
- **Flask Debug**: Set `FLASK_DEBUG=1` locally for detailed errors

Deployment verified! Backend is production-ready on Railway.
