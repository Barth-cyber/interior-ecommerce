#!/usr/bin/env python3
"""
Test Social Media API Credentials

Run this script to verify all your API keys are configured correctly
"""

import os
import sys
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

print("\n" + "="*60)
print("SOCIAL MEDIA API CREDENTIALS TEST")
print("="*60 + "\n")

test_results = []

# 1. YouTube
print("📺 YOUTUBE API")
print("-" * 40)
youtube_key = os.getenv('YOUTUBE_API_KEY')
youtube_channel = os.getenv('YOUTUBE_CHANNEL_ID')

if youtube_key and youtube_channel:
    print(f"✅ API Key:      {youtube_key[:10]}...{youtube_key[-10:]}")
    print(f"✅ Channel ID:   {youtube_channel}")
    test_results.append(('YouTube', True))

    # Test the API
    print("\nTesting API connection...")
    try:
        import requests
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'channelId': youtube_channel,
            'type': 'video',
            'maxResults': 1,
            'key': youtube_key
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            print("✅ API Connection: SUCCESS")
        else:
            print(f"❌ API Error: {response.status_code} - {response.text[:100]}")
            test_results[-1] = ('YouTube', False)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        test_results[-1] = ('YouTube', False)
else:
    print("❌ Missing YOUTUBE_API_KEY or YOUTUBE_CHANNEL_ID")
    test_results.append(('YouTube', False))

# 2. Instagram
print("\n\n📸 INSTAGRAM API")
print("-" * 40)
instagram_account = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
instagram_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')

if instagram_account and instagram_token:
    print(f"✅ Account ID:   {instagram_account}")
    print(f"✅ Access Token: {instagram_token[:20]}...{instagram_token[-20:]}")
    test_results.append(('Instagram', True))

    # Test the API
    print("\nTesting API connection...")
    try:
        import requests
        url = f"https://graph.instagram.com/{instagram_account}/media"
        params = {
            'fields': 'id,caption',
            'access_token': instagram_token,
            'limit': 1
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            print("✅ API Connection: SUCCESS")
            data = response.json()
            if 'data' in data:
                print(f"✅ Retrieved {len(data.get('data', []))} posts")
        else:
            print(f"❌ API Error: {response.status_code}")
            if response.status_code == 400:
                print("   Note: Invalid token or account ID. Check your credentials.")
            test_results[-1] = ('Instagram', False)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        test_results[-1] = ('Instagram', False)
else:
    print("❌ Missing INSTAGRAM_BUSINESS_ACCOUNT_ID or INSTAGRAM_ACCESS_TOKEN")
    test_results.append(('Instagram', False))

# 3. Facebook
print("\n\n📱 FACEBOOK API")
print("-" * 40)
facebook_page = os.getenv('FACEBOOK_PAGE_ID')
facebook_token = os.getenv('FACEBOOK_ACCESS_TOKEN')

if facebook_page and facebook_token:
    print(f"✅ Page ID:      {facebook_page}")
    print(f"✅ Access Token: {facebook_token[:20]}...{facebook_token[-20:]}")
    test_results.append(('Facebook', True))

    # Test the API
    print("\nTesting API connection...")
    try:
        import requests
        url = f"https://graph.instagram.com/{facebook_page}/videos"
        params = {
            'fields': 'id,title',
            'access_token': facebook_token,
            'limit': 1
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            print("✅ API Connection: SUCCESS")
        else:
            print(f"❌ API Error: {response.status_code}")
            test_results[-1] = ('Facebook', False)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        test_results[-1] = ('Facebook', False)
else:
    print("❌ Missing FACEBOOK_PAGE_ID or FACEBOOK_ACCESS_TOKEN")
    test_results.append(('Facebook', False))

# 4. X/Twitter
print("\n\n🐦 X/TWITTER API")
print("-" * 40)
twitter_token = os.getenv('TWITTER_BEARER_TOKEN')

if twitter_token:
    print(f"✅ Bearer Token: {twitter_token[:20]}...{twitter_token[-20:]}")
    test_results.append(('Twitter', True))

    # Test the API
    print("\nTesting API connection...")
    try:
        import requests
        headers = {"Authorization": f"Bearer {twitter_token}"}
        response = requests.get("https://api.twitter.com/2/users/me", headers=headers, timeout=5)
        if response.status_code == 200:
            print("✅ API Connection: SUCCESS")
        elif response.status_code == 401:
            print("❌ Unauthorized: Invalid bearer token")
            test_results[-1] = ('Twitter', False)
        else:
            print(f"❌ API Error: {response.status_code}")
            test_results[-1] = ('Twitter', False)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        test_results[-1] = ('Twitter', False)
else:
    print("❌ Missing TWITTER_BEARER_TOKEN")
    test_results.append(('Twitter', False))

# Summary
print("\n\n" + "="*60)
print("TEST SUMMARY")
print("="*60)

passed = sum(1 for _, result in test_results if result)
total = len(test_results)

for platform, result in test_results:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{platform:15} {status}")

print(f"\nTotal: {passed}/{total} APIs configured")

if passed == total:
    print("\n🎉 All APIs are configured and working!")
    print("\nYou can now:")
    print("1. Run: curl -X POST http://localhost:5000/api/media-hub/videos")
    print("   to fetch fresh videos from all platforms")
    print("2. Run: curl http://localhost:5000/api/media-hub/videos")
    print("   to get cached videos")
    sys.exit(0)
else:
    print(f"\n⚠️  {total - passed} API(s) still need configuration")
    print("\nFollow SOCIAL_MEDIA_API_GUIDE.md for setup instructions")
    sys.exit(1)
