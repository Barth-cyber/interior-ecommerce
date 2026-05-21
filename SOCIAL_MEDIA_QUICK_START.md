# Quick Start Checklist - Social Media Video Integration

## 🚀 5-Minute Overview

Your site now automatically fetches videos from YouTube, Instagram, Facebook, Twitter, and TikTok!

---

## ✅ What Was Done

1. **Created `social_media_fetcher.py`** - Connects to all social media APIs
2. **Updated `app.py`** - New `/api/media-hub/videos` endpoint
3. **Updated `interior.html`** - Media Hub now uses live API data
4. **Created `test_social_apis.py`** - Verify your credentials work
5. **Added documentation** - Complete setup guides

---

## 📋 Next Steps (In Order)

### Step 1: Get API Keys (30-45 min)

Follow `SOCIAL_MEDIA_API_GUIDE.md`:

- [ ] **YouTube** - Get from Google Cloud Console
- [ ] **Instagram** - Get from Facebook Developer Portal  
- [ ] **Facebook** - Use same credentials as Instagram
- [ ] **X/Twitter** - Get from Twitter Developer Portal
- [ ] **TikTok** - Uses web scraping (no API key needed)
- [ ] **LinkedIn** - Uses web scraping (no API key needed)

### Step 2: Add to .env (5 min)

Copy your API keys to `.env`:

```bash
YOUTUBE_API_KEY=AIzaSy...
YOUTUBE_CHANNEL_ID=UCxx...
INSTAGRAM_BUSINESS_ACCOUNT_ID=17xxx...
INSTAGRAM_ACCESS_TOKEN=IGQVJXxx...
FACEBOOK_PAGE_ID=123456789
FACEBOOK_ACCESS_TOKEN=IGQVJXxx...
TWITTER_BEARER_TOKEN=AAAAAxx...
```

### Step 3: Test Configuration (2 min)

```bash
python test_social_apis.py
```

You should see:
```
Total: 5/5 APIs configured
🎉 All APIs are configured and working!
```

### Step 4: Sync Videos (1 min)

```bash
# Fetch fresh videos from all platforms
curl -X POST http://localhost:5000/api/media-hub/videos

# Get cached videos (faster)
curl http://localhost:5000/api/media-hub/videos
```

### Step 5: Set Up Auto-Sync (Optional, 5 min)

**On Windows (Task Scheduler):**
- Task Scheduler → Create Basic Task
- Trigger: Daily at 2 AM
- Action: `powershell.exe -Command "Invoke-WebRequest -Method POST 'http://localhost:5000/api/media-hub/videos'"`

**On Linux/Mac (Cron):**
```bash
crontab -e
# Add: 0 2 * * * curl -X POST http://localhost:5000/api/media-hub/videos
```

**On Render/Railway:**
See section in `SOCIAL_MEDIA_INTEGRATION_GUIDE.md` → "Automatic Sync"

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `SOCIAL_MEDIA_API_GUIDE.md` | Step-by-step setup for each API |
| `SOCIAL_MEDIA_INTEGRATION_GUIDE.md` | Complete implementation guide |
| `social_media_fetcher.py` | Core Python module |
| `test_social_apis.py` | Test your credentials |

---

## 🎯 Your Endpoints

```bash
# GET cached videos (fast)
GET http://localhost:5000/api/media-hub/videos

# POST fetch fresh videos (comprehensive)
POST http://localhost:5000/api/media-hub/videos

# GET all promotions (existing)
GET http://localhost:5000/api/promotions
```

---

## 🆘 Need Help?

**Issue: API credentials not working**
→ Run `python test_social_apis.py` to see which one failed

**Issue: Videos not showing on website**
→ Check browser console (F12) and look at Network tab

**Issue: Can't get API key for platform X**
→ See `SOCIAL_MEDIA_API_GUIDE.md` → Platform X section

---

## 🎉 Done!

Once you complete all 5 steps, your Media Hub will:

✅ Automatically display latest videos from YouTube  
✅ Show Instagram Reels with captions  
✅ Display Facebook videos  
✅ Include X/Twitter videos  
✅ Update every 6 hours (if you set up auto-sync)  
✅ Fall back to cached videos if APIs are down  

**Your customers will see videos from all your social handles in one beautiful playlist!**

---

## 💡 Pro Tips

1. **Test one API at a time** - Get YouTube working first, then Instagram, etc.
2. **Keep API keys safe** - Never commit `.env` to git
3. **Monitor quotas** - YouTube has 10,000 units/day (check Google Cloud)
4. **Cache is your friend** - Use GET endpoint for fast loads
5. **Start with 6 videos/platform** - Reduce if hitting rate limits

---

## 📞 Support Resources

- YouTube API: https://developers.google.com/youtube
- Instagram API: https://developers.facebook.com/
- X/Twitter API: https://developer.twitter.com/
- Flask: https://flask.palletsprojects.com/

---

**Last Updated:** May 21, 2026
