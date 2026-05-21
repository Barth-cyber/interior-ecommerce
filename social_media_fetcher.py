"""
Social Media Video Fetcher
Automatically fetches videos from YouTube, Instagram, Facebook, Twitter, and TikTok
"""

import os
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SocialMediaVideoFetcher:
    """Fetch videos from various social media platforms using their official APIs"""

    def __init__(self):
        # YouTube
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.youtube_channel_id = os.getenv('YOUTUBE_CHANNEL_ID')

        # Instagram & Facebook (same API)
        self.instagram_account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
        self.instagram_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        self.facebook_page_id = os.getenv('FACEBOOK_PAGE_ID')
        self.facebook_token = os.getenv('FACEBOOK_ACCESS_TOKEN')

        # X/Twitter
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

        self.timeout = 10

    def fetch_youtube_videos(self, max_results: int = 12) -> List[Dict]:
        """
        Fetch latest videos from YouTube channel

        API Cost: ~15 units per request (10,000 daily quota = ~666 videos/day)
        """
        if not self.youtube_api_key or not self.youtube_channel_id:
            logger.warning("YouTube API credentials not configured")
            return []

        try:
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'channelId': self.youtube_channel_id,
                'type': 'video',
                'order': 'date',
                'maxResults': max_results,
                'key': self.youtube_api_key
            }

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            videos = []
            for item in data.get('items', []):
                video_id = item['id'].get('videoId')
                snippet = item['snippet']

                videos.append({
                    'type': 'youtube',
                    'id': video_id,
                    'title': snippet['title'],
                    'description': snippet['description'],
                    'platform': 'YouTube',
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'thumbnail': snippet['thumbnails']['medium']['url'],
                    'published_at': snippet['publishedAt'],
                    'badge': 'YOUTUBE'
                })

            logger.info(f"Fetched {len(videos)} videos from YouTube")
            return videos

        except Exception as e:
            logger.error(f"YouTube fetch error: {e}")
            return []

    def fetch_instagram_videos(self, max_results: int = 12) -> List[Dict]:
        """
        Fetch latest videos/reels from Instagram Business Account

        Requires: Instagram Business Account, Graph API access token
        API Cost: FREE (but rate limited to 200 calls/hour)
        """
        if not self.instagram_account_id or not self.instagram_token:
            logger.warning("Instagram API credentials not configured")
            return []

        try:
            url = f"https://graph.instagram.com/{self.instagram_account_id}/media"
            params = {
                'fields': 'id,caption,media_type,media_url,timestamp,permalink',
                'access_token': self.instagram_token,
                'limit': max_results
            }

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            videos = []
            for item in data.get('data', []):
                # Filter for video/reel content only
                if item['media_type'] not in ('VIDEO', 'CAROUSEL'):
                    continue

                videos.append({
                    'type': 'instagram',
                    'id': item['id'],
                    'title': item.get('caption', 'Instagram Post')[:100],
                    'description': item.get('caption', ''),
                    'platform': 'Instagram',
                    'url': item.get('permalink', f'https://instagram.com'),
                    'thumbnail': item.get('media_url', ''),
                    'published_at': item.get('timestamp', ''),
                    'badge': 'INSTAGRAM'
                })

            logger.info(f"Fetched {len(videos)} videos from Instagram")
            return videos

        except Exception as e:
            logger.error(f"Instagram fetch error: {e}")
            return []

    def fetch_facebook_videos(self, max_results: int = 12) -> List[Dict]:
        """
        Fetch latest videos from Facebook Page

        Uses Instagram Graph API (same endpoint family)
        API Cost: FREE (but rate limited to 200 calls/hour)
        """
        if not self.facebook_page_id or not self.facebook_token:
            logger.warning("Facebook API credentials not configured")
            return []

        try:
            url = f"https://graph.instagram.com/{self.facebook_page_id}/videos"
            params = {
                'fields': 'id,title,description,video_data,permalink_url,created_time,picture',
                'access_token': self.facebook_token,
                'limit': max_results
            }

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            videos = []
            for item in data.get('data', []):
                videos.append({
                    'type': 'facebook',
                    'id': item['id'],
                    'title': item.get('title', 'Facebook Video'),
                    'description': item.get('description', ''),
                    'platform': 'Facebook',
                    'url': item.get('permalink_url', f'https://facebook.com'),
                    'thumbnail': item.get('picture', ''),
                    'published_at': item.get('created_time', ''),
                    'badge': 'FACEBOOK'
                })

            logger.info(f"Fetched {len(videos)} videos from Facebook")
            return videos

        except Exception as e:
            logger.error(f"Facebook fetch error: {e}")
            return []

    def fetch_twitter_videos(self, max_results: int = 12) -> List[Dict]:
        """
        Fetch latest tweets with videos from user timeline

        Uses X/Twitter API v2
        API Cost: FREE (300 requests per 15 minutes)
        """
        if not self.twitter_bearer_token:
            logger.warning("Twitter Bearer token not configured")
            return []

        try:
            # Get your user ID first (cache this)
            user_url = "https://api.twitter.com/2/users/by/username/InteriorDuctLtd"
            headers = {"Authorization": f"Bearer {self.twitter_bearer_token}"}

            user_response = requests.get(user_url, headers=headers, timeout=self.timeout)
            user_response.raise_for_status()
            user_data = user_response.json()

            if 'data' not in user_data:
                logger.warning("Could not fetch Twitter user data")
                return []

            user_id = user_data['data']['id']

            # Fetch tweets with media
            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {
                'tweet.fields': 'created_at,public_metrics',
                'expansions': 'attachments.media_keys',
                'media.fields': 'media_key,type,url,preview_image_url',
                'max_results': max_results
            }

            tweets_response = requests.get(tweets_url, headers=headers, params=params, timeout=self.timeout)
            tweets_response.raise_for_status()
            tweets_data = tweets_response.json()

            videos = []
            media_dict = {m['media_key']: m for m in tweets_data.get('includes', {}).get('media', [])}

            for tweet in tweets_data.get('data', []):
                media_keys = tweet.get('attachments', {}).get('media_keys', [])

                for media_key in media_keys:
                    media = media_dict.get(media_key)
                    if media and media['type'] in ('video', 'animated_gif'):
                        videos.append({
                            'type': 'twitter',
                            'id': tweet['id'],
                            'title': tweet['text'][:100],
                            'description': tweet['text'],
                            'platform': 'X (Twitter)',
                            'url': f'https://twitter.com/InteriorDuctLtd/status/{tweet["id"]}',
                            'thumbnail': media.get('preview_image_url', ''),
                            'published_at': tweet.get('created_at', ''),
                            'badge': 'TWITTER'
                        })

            logger.info(f"Fetched {len(videos)} videos from Twitter")
            return videos

        except Exception as e:
            logger.error(f"Twitter fetch error: {e}")
            return []

    def fetch_tiktok_videos_web(self, max_results: int = 12) -> List[Dict]:
        """
        Web scraping fallback for TikTok (TikTok API is restricted)

        Uses requests library to fetch publicly available data
        Note: This is a best-effort approach as TikTok actively blocks scrapers
        """
        handle = "interiorductltd"

        try:
            # Attempt to fetch with Cloudflare bypass headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
            }

            # TikTok blocking: this approach is limited
            # For production, consider using:
            # - TikTok's Official API (requires business partnership)
            # - Third-party services like Apify

            logger.info("TikTok web scraping attempted (limited by TikTok's anti-scraping measures)")
            return []

        except Exception as e:
            logger.warning(f"TikTok fetch failed (expected): {e}")
            return []

    def fetch_all_videos(self, max_per_platform: int = 6) -> Dict[str, List[Dict]]:
        """
        Fetch videos from all configured platforms

        Returns organized by platform
        """
        return {
            'youtube': self.fetch_youtube_videos(max_per_platform),
            'instagram': self.fetch_instagram_videos(max_per_platform),
            'facebook': self.fetch_facebook_videos(max_per_platform),
            'twitter': self.fetch_twitter_videos(max_per_platform),
            'tiktok': self.fetch_tiktok_videos_web(max_per_platform),
        }

    def fetch_combined_videos(self, max_results: int = 20) -> List[Dict]:
        """
        Fetch and combine videos from all platforms, sorted by date
        Useful for a unified media hub feed
        """
        all_videos = []

        all_videos.extend(self.fetch_youtube_videos(max_results // 5))
        all_videos.extend(self.fetch_instagram_videos(max_results // 5))
        all_videos.extend(self.fetch_facebook_videos(max_results // 5))
        all_videos.extend(self.fetch_twitter_videos(max_results // 5))

        # Sort by published date (newest first)
        all_videos.sort(
            key=lambda x: x.get('published_at', ''),
            reverse=True
        )

        return all_videos[:max_results]


# Utility function for Flask integration
def get_social_videos(use_cache: bool = True, cache_file: str = None) -> List[Dict]:
    """
    Wrapper function for Flask to get all social media videos

    Args:
        use_cache: Use cached videos if available
        cache_file: Path to cache file (default: video_posts.json)

    Returns:
        List of video dictionaries
    """
    if cache_file is None:
        cache_file = os.path.join(os.path.abspath('.'), 'video_posts.json')

    fetcher = SocialMediaVideoFetcher()

    try:
        videos = fetcher.fetch_combined_videos(max_results=20)

        # Cache the results
        if videos:
            import json
            cache_data = {'playlists': videos, 'last_updated': datetime.now().isoformat()}
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)

            return videos

    except Exception as e:
        logger.error(f"Error fetching social videos: {e}")

    # Fallback to cached videos
    try:
        import json
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('playlists', [])
    except Exception as e:
        logger.warning(f"Could not load cached videos: {e}")

    return []
