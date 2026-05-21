# Free Social Media API Setup Guide

This guide shows how to obtain FREE API keys for YouTube, Instagram, Facebook, TikTok, and X (Twitter) for automatic video fetching.

---

## 1. YouTube Data API (FREE - 10,000 units/day)

### Step-by-Step Setup:

1. **Create Google Cloud Project:**
   - Go to https://console.cloud.google.com/
   - Click "Select a Project" → "NEW PROJECT"
   - Name it "Interior Ecommerce Videos"
   - Click CREATE

2. **Enable YouTube Data API:**
   - Search "YouTube Data API v3" in the search bar
   - Click on it
   - Press "ENABLE"

3. **Create API Key:**
   - Go to "Credentials" (left sidebar)
   - Click "Create Credentials" → "API Key"
   - Copy your API key

4. **Set API Key in .env:**
   ```
   YOUTUBE_API_KEY=your_api_key_here
   ```

5. **Get Your Channel ID:**
   - Visit your YouTube channel
   - Copy the URL: `https://www.youtube.com/@YOUR_CHANNEL`
   - Go to https://www.youtube.com/
   - Click your profile → Copy channel URL
   - Or use: https://www.youtube.com/c/@interiorductltd → get channel ID from "About" tab

   ```
   YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxx
   ```

**Daily Quota:** 10,000 units (1 video = ~15 units) = ~666 videos/day
**Cost:** FREE with quota limits

---

## 2. Instagram Graph API (FREE - Business Account Required)

### Prerequisites:
- Instagram Business or Creator Account (FREE to upgrade)
- Facebook Page connected to Instagram

### Step-by-Step Setup:

1. **Create Facebook App:**
   - Go to https://developers.facebook.com/
   - Click "My Apps" → "Create App"
   - Choose "Business" as app type
   - Fill in details

2. **Get Access Token:**
   - In your app dashboard, go to "Settings" → "Basic"
   - Copy your App ID and App Secret

3. **Generate Long-Lived Token:**
   - Go to "Tools & Support" → "Access Token Tool"
   - Select your app
   - Copy User Token

4. **Convert to Long-Lived Token:**
   - Use this endpoint (replace tokens):
   ```
   GET https://graph.instagram.com/access_token?grant_type=ig_refresh_token&access_token=YOUR_USER_TOKEN
   ```

5. **Get Business Account ID:**
   ```bash
   curl "https://graph.instagram.com/me?fields=id&access_token=YOUR_TOKEN"
   ```

6. **Set in .env:**
   ```
   INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id
   INSTAGRAM_ACCESS_TOKEN=your_long_lived_token
   ```

**Daily Quota:** FREE, but rate limited to 200 calls/hour
**Cost:** FREE

---

## 3. Facebook Graph API (FREE - Same as Instagram)

### Setup:

1. **Use same Facebook App from Instagram setup above**

2. **Get Page ID:**
   ```bash
   curl "https://graph.instagram.com/me/accounts?access_token=YOUR_TOKEN"
   ```

3. **Set in .env:**
   ```
   FACEBOOK_PAGE_ID=your_page_id
   FACEBOOK_ACCESS_TOKEN=your_token_from_instagram_setup
   ```

4. **Fetch Videos:**
   ```bash
   curl "https://graph.instagram.com/YOUR_PAGE_ID/videos?fields=id,media_type,media_url,caption&access_token=YOUR_TOKEN"
   ```

**Cost:** FREE (same API as Instagram)

---

## 4. TikTok API (FREE - Research Account)

### Limitation:
- TikTok officially does NOT allow video scraping in their developer API
- However, you can use the **unofficial but stable** method

### Free Alternative: Web Scraping (Recommended)
```python
# Uses existing web scraping from app.py
# Fetch latest posts from: https://www.tiktok.com/@your_handle
```

**Cost:** FREE (web scraping - no API)

---

## 5. X/Twitter API (FREE - Essential Tier)

### Step-by-Step Setup:

1. **Apply for X Developer Account:**
   - Go to https://developer.twitter.com/en/apply-for-access
   - Select "Hobbyist" → "Explore the API"
   - Answer questions about your use case
   - Wait for approval (usually instant-1 day)

2. **Create Project & App:**
   - Go to https://dashboard.twitter.com/apps
   - Create a new project
   - Create an app within the project

3. **Generate Keys:**
   - Go to "Keys and Tokens"
   - Under API Keys section, copy:
     - API Key (Consumer Key)
     - API Secret Key (Consumer Secret)
   - Under Bearer Token, copy the Bearer Token

4. **Set in .env:**
   ```
   TWITTER_BEARER_TOKEN=your_bearer_token
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   ```

5. **Get Your User ID:**
   ```bash
   curl -H "Authorization: Bearer YOUR_BEARER_TOKEN" \
     "https://api.twitter.com/2/users/by/username/your_handle"
   ```

**Daily Quota (Free Tier):**
- 300 requests / 15 minutes
- Can fetch ~300 tweets/day

**Cost:** FREE for essential tier

---

## 6. LinkedIn API (LIMITED - Company Page Posts)

### Limitation:
- LinkedIn API is restricted - no public API for regular posts
- Official API requires Enterprise tier (paid)

### Free Alternative: Web Scraping
```python
# Uses existing web scraping from app.py
# Fetch from: https://www.linkedin.com/company/interior-duct-ltd/
```

**Cost:** FREE (web scraping - no API)

---

## Summary Table

| Platform | API Type | Cost | Daily Quota | Status |
|----------|----------|------|-------------|--------|
| YouTube | Official | FREE | ~666 videos | ✅ Recommended |
| Instagram | Official | FREE | Unlimited | ✅ Recommended |
| Facebook | Official | FREE | Unlimited | ✅ Recommended |
| TikTok | Web Scrape | FREE | ~100 | ⚠️ Best effort |
| X/Twitter | Official | FREE | ~300 | ✅ Recommended |
| LinkedIn | Web Scrape | FREE | ~50 | ⚠️ Best effort |

---

## Complete .env Configuration

```ini
# YouTube
YOUTUBE_API_KEY=AIzaSy...
YOUTUBE_CHANNEL_ID=UCx...

# Instagram & Facebook (use same token)
INSTAGRAM_BUSINESS_ACCOUNT_ID=17...
INSTAGRAM_ACCESS_TOKEN=IGQVJXx...
FACEBOOK_PAGE_ID=1234567...
FACEBOOK_ACCESS_TOKEN=IGQVJXx...

# X/Twitter
TWITTER_BEARER_TOKEN=AAAAAx...
TWITTER_API_KEY=xxxxx...
TWITTER_API_SECRET=xxxxx...
```

---

## Testing Your APIs

Once configured, test each API:

```bash
# YouTube
curl "https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=YOUR_CHANNEL&type=video&key=YOUR_API_KEY"

# Instagram
curl "https://graph.instagram.com/YOUR_ACCOUNT_ID/media?fields=id,caption,media_url&access_token=YOUR_TOKEN"

# Facebook
curl "https://graph.instagram.com/YOUR_PAGE_ID/videos?access_token=YOUR_TOKEN"

# X/Twitter
curl -H "Authorization: Bearer YOUR_BEARER_TOKEN" \
  "https://api.twitter.com/2/tweets/search/recent?query=from:your_handle"
```

---

## Next Steps

1. Obtain all API keys following the steps above
2. Add them to your `.env` file
3. Deploy the `social_media_fetcher.py` module
4. Update `app.py` to use the API integrations
5. Test the `/api/promotions` endpoint
