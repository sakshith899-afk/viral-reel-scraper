import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

# We will use the `adams_sarah/instagram-scraper` or similar robust Apify actor
# for searching by keywords/hashtags or user profiles.
# Note: For real-world usage, an Apify API token is required.
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

def scrape_instagram_reels(niche: str, max_results: int = 20):
    """
    Scrapes Instagram reels based on a given niche/keyword.
    We fetch slightly more results than we need because we will filter them down.
    """
    if not APIFY_API_TOKEN:
        print("Warning: APIFY_API_TOKEN not set. Returning mock data for demonstration.")
        return _get_mock_data(niche)

    client = ApifyClient(APIFY_API_TOKEN)

    # Using a popular and reliable instagram scraper from Apify
    # The exact run input depends on the actor chosen.
    # Let's assume we are using a general Instagram scraper by hashtag/keyword
    run_input = {
        "search": niche,
        "searchType": "hashtag", # Can also be "user" if we target specific creators
        "resultsType": "posts",
        "searchLimit": max_results,
    }

    print(f"Starting Instagram scraper for niche: {niche}")
    # Replace 'apify_actor_id' with the actual ID of the scraper you use,
    # e.g., 'apify/instagram-scraper' or similar
    run = client.actor("apify/instagram-scraper").call(run_input=run_input)

    print("Scraping completed. Fetching results...")
    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        # We only want video/reel content
        if item.get("type") == "Video" or item.get("isVideo"):
            reel_data = {
                "id": item.get("id"),
                "url": item.get("url"),
                "caption": item.get("caption", ""),
                "viewCount": item.get("videoViewCount", 0),
                "likeCount": item.get("likesCount", 0),
                "commentCount": item.get("commentsCount", 0),
                "author": item.get("ownerUsername", ""),
            }
            results.append(reel_data)

    return results

def _get_mock_data(niche: str):
    """Provides mock data if Apify token isn't provided for testing the pipeline."""
    return [
        {
            "id": "1",
            "url": "https://instagram.com/reel/mock1",
            "caption": f"Top 3 tips for {niche}! #viral #{niche}",
            "viewCount": 500000,
            "likeCount": 25000,
            "commentCount": 1200,
            "author": f"{niche}_expert",
        },
        {
            "id": "2",
            "url": "https://instagram.com/reel/mock2",
            "caption": "You won't believe this hack! 🤯 #trending",
            "viewCount": 1000000,
            "likeCount": 5000, # Low engagement
            "commentCount": 50,
            "author": "spammy_page",
        },
        {
             "id": "3",
            "url": "https://instagram.com/reel/mock3",
            "caption": f"Why everyone is doing {niche} wrong. Here is the right way.",
            "viewCount": 300000,
            "likeCount": 45000, # High engagement
            "commentCount": 3000,
            "author": f"real_{niche}_creator",
        }
    ]
