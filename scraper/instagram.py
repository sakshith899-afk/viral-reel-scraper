import os
from datetime import datetime, timezone
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()


def _extract_reel(item: dict) -> dict | None:
    """Normalize a raw Apify item into our internal reel dict. Returns None if not a video."""
    if not (item.get("type") == "Video" or item.get("isVideo") or item.get("videoUrl")):
        return None

    views    = int(item.get("videoViewCount") or item.get("playCount") or item.get("videoPlayCount") or 0)
    likes    = int(item.get("likesCount") or item.get("likeCount") or 0)
    comments = int(item.get("commentsCount") or item.get("commentCount") or 0)

    # Velocity: views per day since posted
    ts = item.get("timestamp") or item.get("taken_at_timestamp")
    days_old = None
    if ts:
        try:
            if isinstance(ts, (int, float)):
                posted = datetime.fromtimestamp(ts, tz=timezone.utc)
            else:
                posted = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            days_old = max((datetime.now(tz=timezone.utc) - posted).days, 1)
        except Exception:
            pass

    # Audio / music
    music = item.get("musicInfo") or item.get("music") or {}
    audio = None
    if music:
        artist = music.get("artistName") or music.get("artist_name") or ""
        song   = music.get("songName") or music.get("title") or ""
        if artist or song:
            audio = f"{artist} — {song}".strip(" —")

    short_code = item.get("shortCode") or item.get("shortcode") or ""
    url = item.get("url") or (f"https://www.instagram.com/reel/{short_code}/" if short_code else "")

    return {
        "id":           item.get("id", ""),
        "url":          url,
        "caption":      (item.get("caption") or "")[:500],
        "viewCount":    views,
        "likeCount":    likes,
        "commentCount": comments,
        "author":       item.get("ownerUsername") or item.get("username") or "",
        "duration":     item.get("videoDuration") or item.get("duration") or None,
        "audio":        audio,
        "daysOld":      days_old,
    }


def scrape_instagram_reels(niche: str, hashtags: list | None = None, max_results: int = 30) -> list:
    """
    Scrapes TOP posts from Instagram hashtag pages using apify/instagram-hashtag-scraper.
    Accepts pre-expanded hashtags from ai/hashtags.expand_hashtags().
    """
    apify_token = os.getenv("APIFY_API_TOKEN")

    if not apify_token:
        print("Warning: APIFY_API_TOKEN not set. Returning mock data.")
        return _get_mock_data(niche)

    if not hashtags:
        hashtags = [niche.lower().replace(" ", "")]

    client = ApifyClient(apify_token)
    all_results = []
    seen_urls: set = set()

    for tag in hashtags:
        print(f"Scraping top posts for #{tag}...")
        run_input = {
            "hashtags": [tag],
            "resultsType": "posts",
            "resultsLimit": max_results,
        }
        try:
            run = client.actor("apify/instagram-hashtag-scraper").call(run_input=run_input)
        except Exception as e:
            print(f"Apify scrape failed for #{tag}: {e}")
            continue

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            # instagram-hashtag-scraper wraps posts under topPosts / latestPosts arrays
            for post in item.get("topPosts", []):
                reel = _extract_reel(post)
                if reel and reel["url"] and reel["url"] not in seen_urls:
                    seen_urls.add(reel["url"])
                    all_results.append(reel)

    all_results.sort(key=lambda r: r["viewCount"], reverse=True)
    print(f"Total reels collected: {len(all_results)} across {len(hashtags)} hashtag(s)")
    return all_results


def scrape_profile_reels(profile_url: str, max_results: int = 20) -> list:
    """
    Scrapes reels from a specific Instagram profile URL.
    Used when the user pastes their own account URL to auto-derive their niche.
    """
    apify_token = os.getenv("APIFY_API_TOKEN")

    if not apify_token:
        print("Warning: APIFY_API_TOKEN not set. Returning mock profile data.")
        return _get_mock_data("your niche")

    client = ApifyClient(apify_token)
    print(f"Scraping profile: {profile_url}")
    run_input = {
        "directUrls": [profile_url.rstrip("/") + "/"],
        "resultsType": "posts",
        "resultsLimit": max_results,
    }
    try:
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
    except Exception as e:
        print(f"Profile scrape failed: {e}")
        return []

    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        reel = _extract_reel(item)
        if not reel:
            # For profile analysis we keep all posts (images too), not just videos
            results.append({
                "id":           item.get("id", ""),
                "url":          item.get("url", ""),
                "caption":      (item.get("caption") or "")[:500],
                "viewCount":    int(item.get("videoViewCount") or item.get("likesCount") or 0),
                "likeCount":    int(item.get("likesCount") or 0),
                "commentCount": int(item.get("commentsCount") or 0),
                "hashtags":     item.get("hashtags") or [],
            })
        else:
            results.append(reel)

    results.sort(key=lambda r: r.get("viewCount", 0), reverse=True)
    print(f"Profile posts collected: {len(results)}")
    return results


def _get_mock_data(niche: str):
    return [
        {
            "id": "1", "url": "https://www.instagram.com/reel/mock1/",
            "caption": f"Top 3 tips for {niche} nobody talks about! #viral",
            "viewCount": 850_000, "likeCount": 42_000, "commentCount": 2_100,
            "author": f"{niche.replace(' ', '_')}_expert", "duration": 18,
            "audio": "Trending Sound — Popular Artist", "daysOld": 5,
        },
        {
            "id": "2", "url": "https://www.instagram.com/reel/mock2/",
            "caption": f"This changed everything about {niche} for me.",
            "viewCount": 1_200_000, "likeCount": 61_000, "commentCount": 4_400,
            "author": f"top_{niche.replace(' ', '')}creator", "duration": 28,
            "audio": None, "daysOld": 12,
        },
        {
            "id": "3", "url": "https://www.instagram.com/reel/mock3/",
            "caption": f"Why everyone is doing {niche} wrong. Here is the right way.",
            "viewCount": 500_000, "likeCount": 38_000, "commentCount": 3_200,
            "author": f"real_{niche.replace(' ', '_')}_creator", "duration": 22,
            "audio": "Original Audio", "daysOld": 8,
        },
    ]
