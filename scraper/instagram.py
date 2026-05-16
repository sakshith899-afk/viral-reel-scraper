import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()


def scrape_instagram_reels(niche: str, max_results: int = 20):
    """
    Scrapes Instagram reels based on a given niche/keyword via Apify.
    Falls back to mock data if APIFY_API_TOKEN is not set.
    """
    # Read token inside the function so load_dotenv() above always runs first
    apify_token = os.getenv("APIFY_API_TOKEN")

    if not apify_token:
        print("Warning: APIFY_API_TOKEN not set. Returning mock data for demonstration.")
        return _get_mock_data(niche)

    client = ApifyClient(apify_token)

    # Use directUrls to go straight to the hashtag page — avoids Google search
    # which gets blocked and returns 0 results
    hashtag = niche.lower().replace(" ", "")
    run_input = {
        "directUrls": [f"https://www.instagram.com/explore/tags/{hashtag}/"],
        "resultsType": "posts",
        "resultsLimit": max_results,
    }

    print(f"Starting Instagram scraper for niche: '{niche}'")
    try:
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
    except Exception as e:
        print(f"Apify scrape failed: {e}. Falling back to mock data.")
        return _get_mock_data(niche)

    print("Scraping completed. Fetching results...")
    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        # Only keep video/reel content
        if item.get("type") == "Video" or item.get("isVideo"):
            results.append({
                "id":           item.get("id", ""),
                "url":          item.get("url", ""),
                "caption":      item.get("caption", ""),
                "viewCount":    item.get("videoViewCount", 0) or 0,
                "likeCount":    item.get("likesCount", 0) or 0,
                "commentCount": item.get("commentsCount", 0) or 0,
                "author":       item.get("ownerUsername", ""),
            })

    # Sort by views descending so the most viral reels go first
    results.sort(key=lambda r: r["viewCount"], reverse=True)
    return results


def _get_mock_data(niche: str):
    """Sample data for testing the pipeline without API credentials."""
    return [
        {
            "id": "1",
            "url": "https://www.instagram.com/reel/mock1/",
            "caption": f"Top 3 tips for {niche}! #viral #{niche.replace(' ', '')}",
            "viewCount": 500_000,
            "likeCount": 25_000,
            "commentCount": 1_200,
            "author": f"{niche.replace(' ', '_')}_expert",
        },
        {
            "id": "2",
            "url": "https://www.instagram.com/reel/mock2/",
            "caption": "You won't believe this hack! #trending",
            "viewCount": 1_000_000,
            "likeCount": 5_000,
            "commentCount": 50,
            "author": "spammy_page",
        },
        {
            "id": "3",
            "url": "https://www.instagram.com/reel/mock3/",
            "caption": f"Why everyone is doing {niche} wrong. Here is the right way.",
            "viewCount": 300_000,
            "likeCount": 45_000,
            "commentCount": 3_000,
            "author": f"real_{niche.replace(' ', '_')}_creator",
        },
    ]
