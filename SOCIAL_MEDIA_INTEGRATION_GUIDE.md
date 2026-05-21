# Social Media Video Integration - Complete Implementation Guide

## Overview

Your e-commerce site now has a full integration system to automatically fetch and display videos from YouTube, Instagram, Facebook, Twitter, and TikTok in the Media Hub.

### Files Created/Modified:

1. **`social_media_fetcher.py`** - Core module for fetching videos from APIs
2. **`app.py`** - Updated with new `/api/media-hub/videos` endpoint
3. **`interior.html`** - Updated to use new media hub API
4. **`test_social_apis.py`** - Script to verify API credentials
5. **`SOCIAL_MEDIA_API_GUIDE.md`** - Detailed API setup instructions
6. **`.env.example`** - Updated with all required API variables

---

## Step 1: Get Your Free API Keys

Follow the guide in `SOCIAL_MEDIA_API_GUIDE.md` to obtain free API keys for:

- ✅ **YouTube** - 10,000 free units/day
- ✅ **Instagram** - FREE (rate limited)
- ✅ **Facebook** - FREE (rate limited)
- ✅ **X/Twitter** - 300 requests/15 min free tier
- ✅ **TikTok** - Web scraping (no official free API)
- ✅ **LinkedIn** - Web scraping (no official free API)

**Estimated Time:** 30-45 minutes per platform

---

## Step 2: Configure Environment Variables

After obtaining your API keys, add them to your `.env` file:

```bash
# YouTube
YOUTUBE_API_KEY=AIzaSy...your_key_here...
YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxx

# Instagram & Facebook
INSTAGRAM_BUSINESS_ACCOUNT_ID=17xxxxxxxxxxxxx
INSTAGRAM_ACCESS_TOKEN=IGQVJXxxxxxxxxx...
FACEBOOK_PAGE_ID=123456789
FACEBOOK_ACCESS_TOKEN=IGQVJXxxxxxxxxx...

# X/Twitter
TWITTER_BEARER_TOKEN=AAAAAxxxxxxxxx...
TWITTER_API_KEY=xxxxx
TWITTER_API_SECRET=xxxxx
```

### Get Your Channel/Page IDs:

**YouTube Channel ID:**
```bash
# Visit your channel, the ID is in the URL:
# https://www.youtube.com/@YOUR_CHANNEL
# Or copy from channel settings
```

**Instagram Business Account ID:**
```bash
curl "https://graph.instagram.com/me?fields=id&access_token=YOUR_TOKEN"
```

**Facebook Page ID:**
```bash
curl "https://graph.instagram.com/me/accounts?access_token=YOUR_TOKEN"
```

**Twitter User ID:**
```bash
curl -H "Authorization: Bearer YOUR_BEARER_TOKEN" \
  "https://api.twitter.com/2/users/by/username/InteriorDuctLtd"
```

---

## Step 3: Test Your Configuration

Run the test script to verify all APIs are working:

```bash
# From your project root directory
python test_social_apis.py
```

Expected output:
```
============================================================
SOCIAL MEDIA API CREDENTIALS TEST
============================================================

📺 YOUTUBE API
✅ API Key:      AIzaSyxxxxxx...
✅ Channel ID:   UCxxxxxx
✅ API Connection: SUCCESS

📸 INSTAGRAM API
✅ Account ID:   17xxxxx
✅ Access Token: IGQVJXxx...xxx
✅ API Connection: SUCCESS
✅ Retrieved 12 posts

... [more platforms]

============================================================
TEST SUMMARY
============================================================
YouTube          ✅ PASS
Instagram        ✅ PASS
Facebook         ✅ PASS
Twitter          ✅ PASS
...

Total: 5/5 APIs configured

🎉 All APIs are configured and working!
```

---

## Step 4: Fetch Videos from APIs

### Option A: Manually Sync Videos

```bash
# Fetch fresh videos from all APIs and update cache
curl -X POST http://localhost:5000/api/media-hub/videos

# Response:
{
  "success": true,
  "videos": [
    {
      "type": "youtube",
      "id": "video_id",
      "title": "Video Title",
      "description": "Video description",
      "platform": "YouTube",
      "url": "https://youtube.com/watch?v=...",
      "thumbnail": "https://img.youtube.com/vi/.../mqdefault.jpg",
      "published_at": "2026-05-21T10:30:00Z",
      "badge": "YOUTUBE"
    },
    ...
  ],
  "count": 20,
  "source": "live_apis",
  "synced_at": "2026-05-21T16:45:30.123456"
}
```

### Option B: Get Cached Videos

```bash
# Get videos from cache (faster)
curl http://localhost:5000/api/media-hub/videos

# Response includes:
{
  "success": true,
  "videos": [...],
  "count": 20,
  "source": "cache",
  "last_updated": "2026-05-21T16:45:30.123456"
}
```

---

## Step 5: Automatic Sync (Cron Job)

To keep videos fresh, set up periodic syncing:

### Option A: Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this to sync every 6 hours:
0 */6 * * * curl -X POST http://localhost:5000/api/media-hub/videos

# Or every day at 2 AM:
0 2 * * * curl -X POST http://localhost:5000/api/media-hub/videos
```

### Option B: Scheduled Task (Windows)

1. Open **Task Scheduler**
2. Create Basic Task → Name it "Sync Media Hub Videos"
3. Set trigger: Daily/Hourly as needed
4. Add action: `powershell.exe -Command "Invoke-WebRequest -Method POST 'http://localhost:5000/api/media-hub/videos'"`

### Option C: Background Worker (Render/Railway)

If deployed on Render or Railway:

```python
# Add to app.py for periodic background sync
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

def sync_media_hub():
    """Background task to sync videos every 6 hours"""
    try:
        videos = get_social_videos(use_cache=False)
        logger.info(f"Background sync: fetched {len(videos)} videos")
    except Exception as e:
        logger.error(f"Background sync failed: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=sync_media_hub, trigger="interval", hours=6)
scheduler.start()

# Shut down scheduler on app exit
atexit.register(lambda: scheduler.shutdown())
```

---

## Step 6: Website Integration

The Media Hub on `interior.html` now automatically:

1. **Loads videos** from the new `/api/media-hub/videos` endpoint
2. **Displays videos** from all social platforms in one playlist
3. **Falls back** to cached videos if APIs are unavailable
4. **Handles different video types** (YouTube, Facebook, Instagram, Twitter)

### What Your Customers See:

- YouTube videos with official thumbnails
- Instagram Reels with captions
- Facebook videos with metadata
- Twitter videos with timestamps
- Automatic platform badges (YOUTUBE, INSTAGRAM, FACEBOOK, TWITTER)

---

## API Reference

### GET `/api/media-hub/videos`
Returns cached videos (fast, no API calls)

```json
{
  "success": true,
  "videos": [Array of video objects],
  "count": 20,
  "source": "cache",
  "last_updated": "2026-05-21T16:45:30Z"
}
```

### POST `/api/media-hub/videos`
Fetches fresh videos from all APIs (slower, ~10-15 seconds)

```json
{
  "success": true,
  "videos": [Array of video objects],
  "count": 20,
  "source": "live_apis",
  "synced_at": "2026-05-21T16:45:30Z"
}
```

### Video Object Format

```json
{
  "type": "youtube|instagram|facebook|twitter",
  "id": "video_id",
  "title": "Video Title",
  "description": "Full description",
  "platform": "YouTube|Instagram|Facebook|X (Twitter)",
  "url": "https://...",
  "thumbnail": "https://...",
  "published_at": "2026-05-21T10:30:00Z",
  "badge": "YOUTUBE|INSTAGRAM|FACEBOOK|TWITTER"
}
```

---

## Troubleshooting

### Problem: "API credentials not configured" warning

**Solution:** Check `.env` file has all required variables
```bash
grep YOUTUBE_API_KEY .env
grep INSTAGRAM_BUSINESS_ACCOUNT_ID .env
# ... etc
```

### Problem: "Invalid token" from Instagram/Facebook

**Solution:** Regenerate your access token
1. Go to https://developers.facebook.com/
2. Go to Tools & Support → Access Token Tool
3. Generate new User Token
4. Convert to Long-Lived Token (60 days)
5. Update `.env` file

### Problem: YouTube returns 403 Forbidden

**Solution:** Check API quota
```bash
# In Google Cloud Console:
# APIs & Services → YouTube Data API v3 → Quotas
# Verify you have 10,000 units/day
```

### Problem: No videos loading on site

**Solution:** Check browser console
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Check Network tab → `/api/media-hub/videos` response
4. Run `python test_social_apis.py` to verify backend

### Problem: Slow video loading

**Solution:** Use cached endpoint or add caching header
```python
# In app.py, add cache header:
@app.route('/api/media-hub/videos', methods=['GET'])
def api_media_hub_videos():
    response = jsonify({...})
    response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
    return response
```

---

## Performance Optimization

### Reduce API Calls:

```python
# In social_media_fetcher.py - fetch fewer videos per platform
get_social_videos(max_per_platform=3)  # Instead of 6
```

### Cache Longer:

```python
# Sync less frequently - every 24 hours instead of 6
scheduler.add_job(func=sync_media_hub, trigger="interval", hours=24)
```

### Monitor Quotas:

| Platform | Daily Quota | Videos/Day |
|----------|------------|-----------|
| YouTube | 10,000 units | ~666 videos |
| Instagram | Unlimited* | ~200/hour |
| Facebook | Unlimited* | ~200/hour |
| Twitter | 300/15min | ~288/day |

*Rate limited, not quota-limited

---

## Next Steps

1. ✅ Obtain API keys (SOCIAL_MEDIA_API_GUIDE.md)
2. ✅ Add to .env file
3. ✅ Run test_social_apis.py
4. ✅ Test endpoints (POST then GET)
5. ✅ Set up automatic syncing (cron/scheduler)
6. ✅ Verify on website

---

## Support

For detailed setup instructions for each platform, see:
- **`SOCIAL_MEDIA_API_GUIDE.md`** - Step-by-step API setup

For testing and debugging:
- Run: `python test_social_apis.py`
- Check Flask logs in terminal
- Monitor Network tab in browser DevTools

---

## Summary of Endpoints

```bash
# Your Flask app now has:

# Existing endpoints:
GET  /api/promotions                 # Returns all media (videos + social + products)
GET  /api/social-sync               # Get cached social posts
POST /api/social-sync               # Fetch fresh social posts

# NEW endpoints:
GET  /api/media-hub/videos          # Get cached videos (FAST)
POST /api/media-hub/videos          # Fetch fresh videos (COMPREHENSIVE)
```

---

**You're all set!** 🚀

Your Media Hub is now connected to all major social platforms and will automatically display the latest videos from your company's accounts.
