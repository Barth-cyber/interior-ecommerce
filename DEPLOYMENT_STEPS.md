# Step-by-Step Render Deployment Guide
## Interior Ecommerce Application

### Phase 1: Pre-Deployment Setup (Local) ✓ DONE

You've already completed:
- ✅ Created `render.yaml`
- ✅ Created `Procfile`
- ✅ Updated `.gitignore`
- ✅ Pushed to GitHub

---

## Phase 2: Render Account Setup (5 minutes)

### Step 1: Create Render Account
**Action:** Go to https://render.com

- Click **"Sign Up"** (top right)
- Click **"Continue with GitHub"**
- Authorize Render to access your GitHub account
- You'll be redirected to Render dashboard

**Screenshot reference:** Render homepage with "Sign Up" button in top right

---

### Step 2: Create New Web Service
**Action:** In Render Dashboard

1. Click **"New +"** (top right) → Select **"Web Service"**
   - **Screenshot reference:** Dropdown menu with service options
   
2. Click **"Connect Repository"**
   - **Screenshot reference:** GitHub connection dialog

3. Find and select **`interior-ecommerce`**
   - **Screenshot reference:** Repository selection list
   - (May need to authorize GitHub if first time)

---

### Step 3: Configure Web Service
**Action:** Fill in the deployment settings

**Service Settings Panel:**

| Field | Value | Notes |
|-------|-------|-------|
| **Name** | `interior-ecommerce` | This becomes your URL domain |
| **Environment** | `Python 3` | Render will auto-detect |
| **Build Command** | `pip install -r requirements.txt` | Installs dependencies |
| **Start Command** | `gunicorn -w 2 -b 0.0.0.0:$PORT application:app` | Starts Flask server |
| **Plan** | `Free` (or `Starter $7/mo`) | Free tier OK for testing |

**Screenshot reference locations:**
- Build Command field (left panel, second section)
- Start Command field (left panel, third section)
- Plan selector (right side, "Starter" section)

**Scroll down to find:**
- Health Check Path: `/` (leave default or remove)
- Autoscaling: Can leave disabled for free tier

---

### Step 4: Add Environment Variables
**Action:** Set required variables before deployment

**In Render Dashboard:**
1. Scroll to **"Environment"** section
2. Click **"Add Environment Variable"**
3. Add these variables:

```
ADMIN_SECRET_KEY = (generate a secure key below)
ADMIN_USERNAME = admin
ADMIN_COOKIE_SECURE = true
PYTHONUNBUFFERED = true
```

**Generate secure key (copy one of these):**
```
Option 1: In terminal run:
python -c "import secrets; print(secrets.token_hex(32))"

Option 2: Use random value:
a7f8e3b2c9d1f4a6e8b0c2d4f6a8e0c2d4f6a8e0c2d4f6a8e0c2d4f6a8e0

Option 3: Online generator:
https://1password.com/password-generator/
```

**Screenshot reference:**
- Environment Variables section (below Start Command)
- "Add Environment Variable" button
- Key/Value input fields

---

## Phase 3: Deploy! (2-3 minutes)

### Step 5: Click "Create Web Service"
**Action:** Final step

1. Review all settings one more time
2. Ensure you see:
   - ✅ Name: `interior-ecommerce`
   - ✅ Build Command: `pip install -r requirements.txt`
   - ✅ Start Command: `gunicorn -w 2 -b 0.0.0.0:$PORT application:app`
   - ✅ Environment variables added

3. Click **"Create Web Service"** (bottom right, blue button)

**Screenshot reference:** Bottom right corner has blue "Create Web Service" button

---

### Step 6: Watch Deployment Logs
**Action:** Monitor deployment progress

**Render will show:**
- 📥 "Cloning repository..."
- 🔨 "Building..." (watch logs scroll)
- ⏳ "Starting..." 
- ✅ "Live" (deployment complete)

**Timeline:**
- Clone: ~5-10 seconds
- Build: ~30-60 seconds (first time downloads ML models)
- Start: ~10-20 seconds
- **Total: 2-3 minutes**

**Screenshot reference:**
- Live logs panel (right side)
- Green "Live" status indicator (next to service name)

---

### Step 7: Access Your Live Application
**Action:** Your app is now live!

**Your URL:**
```
https://interior-ecommerce.onrender.com
```

**What to test:**
1. ✅ Homepage loads → `/`
2. ✅ Images display → Check static files
3. ✅ API endpoints work → Try `/api/session`
4. ✅ Admin panel → `/admin` (if exists)
5. ✅ No 500 errors → Check Render logs if issues

---

## Phase 4: Troubleshooting (if needed)

### If Deployment Fails

**Check these in order:**

1. **View Build Logs**
   - Dashboard → Your Service → Logs
   - Look for red error messages
   - Common: `ModuleNotFoundError`, `SyntaxError`
   - **Fix Guide:** See `DEPLOYMENT_TROUBLESHOOTING.md`

2. **Service Won't Start (502 Bad Gateway)**
   - Check Start Command spelling
   - Should be: `gunicorn -w 2 -b 0.0.0.0:$PORT application:app`
   - Wait 30 seconds for retry

3. **Missing Environment Variables**
   - App crashes with `KeyError`
   - Add missing variables in Settings → Environment
   - Click "Deploy" after adding

4. **Timeout (>60 seconds)**
   - ML models loading is slow
   - Render free tier has limited resources
   - Either:
     - Upgrade to Starter ($7/mo)
     - Reduce workers: `-w 1`
     - Use paid tier with more RAM

---

## Phase 5: After Deployment

### Auto-Deploy on Git Push
**Render automatically redeploys when you:**
```bash
git push origin main
```

**What happens:**
1. Render detects push
2. Pulls latest code
3. Rebuilds automatically
4. Redeploys (0 downtime)

### Monitor Your App
**In Render Dashboard:**
- Check **"Events"** tab for deployment history
- Check **"Logs"** tab for runtime errors
- Check **"Metrics"** tab for resource usage

### Update Environment Variables
1. Dashboard → Settings
2. Click Environment variable
3. Edit value
4. Click "Deploy" button (appears when you change settings)

---

## Quick Checklist

- [ ] GitHub account linked to Render
- [ ] Repository `interior-ecommerce` selected
- [ ] Service name: `interior-ecommerce`
- [ ] Build Command copied exactly
- [ ] Start Command copied exactly
- [ ] Environment variables added (ADMIN_SECRET_KEY, etc.)
- [ ] Plan selected (Free or Starter)
- [ ] "Create Web Service" button clicked
- [ ] Waited 2-3 minutes for deployment
- [ ] Live URL accessible
- [ ] Homepage loads without errors

---

## Support Resources

If something goes wrong:

1. **Check Logs First** (most important)
   - Render Dashboard → Your Service → Logs

2. **Reference Troubleshooting Guide**
   - `DEPLOYMENT_TROUBLESHOOTING.md` in your repo

3. **Render Official Docs**
   - https://render.com/docs/deploy-flask
   - https://render.com/docs/troubleshooting

4. **Common Quick Fixes**
   - Rebuild: Click "Manual Deploy" in Render
   - Restart: Click "Re-run build" 
   - Wait: Free tier may need 3-5 min to stabilize

---

## Success! 🎉

Once you see the green **"Live"** badge in Render Dashboard:

✅ Your app is deployed and running  
✅ URL: `https://interior-ecommerce.onrender.com`  
✅ Future git pushes auto-deploy  
✅ You can access it from anywhere  

**Congratulations!** Your ecommerce website is now live on the internet! 🚀
