import os
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class RelevanceEvaluation(BaseModel):
    is_relevant: bool
    reasoning: str


def filter_reels_for_niche(reels: list, niche: str) -> list:
    """
    Uses an LLM to filter out spam, irrelevant content, and engagement bait.
    Supports GitHub Models (free) or OpenAI (paid). Falls back to heuristics.
    """
    api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Warning: Neither GITHUB_TOKEN nor OPENAI_API_KEY is set. Using heuristic filter.")
        return _heuristic_filter(reels)

    is_github = bool(os.getenv("GITHUB_TOKEN"))
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com" if is_github else None,
        api_key=api_key,
    )

    filtered_reels = []
    print(f"AI filtering {len(reels)} reels (source: {'GitHub Models' if is_github else 'OpenAI'})...")

    for reel in reels:
        views    = reel.get("viewCount", 1) or 1
        likes    = reel.get("likeCount", 0) or 0
        comments = reel.get("commentCount", 0) or 0
        engagement_rate = ((likes + comments) / views) * 100

        if views > 100_000 and engagement_rate < 0.5:
            print(f"Pre-filter skip (low engagement {engagement_rate:.2f}%): {reel.get('url')}")
            continue

        prompt = f"""
You are a strict social media quality analyst.

Target niche: {niche}

Reel data:
  Caption:         {reel.get('caption', 'No caption')}
  Views:           {views:,}
  Likes:           {likes:,}
  Comments:        {comments:,}
  Author:          {reel.get('author', 'Unknown')}
  Engagement rate: {engagement_rate:.2f}%

Is this reel genuinely relevant to the niche and providing real value?
Or is it spam, off-topic, or engagement bait?
"""

        try:
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a strict data quality filter for social media content."},
                    {"role": "user",   "content": prompt},
                ],
                response_format=RelevanceEvaluation,
            )
            evaluation = response.choices[0].message.parsed

            if evaluation.is_relevant:
                print(f"KEPT    {reel.get('url')} — {evaluation.reasoning}")
                filtered_reels.append(reel)
            else:
                print(f"DROPPED {reel.get('url')} — {evaluation.reasoning}")

        except Exception as e:
            print(f"Filter API error for {reel.get('url')}: {e} — keeping reel to avoid data loss")
            filtered_reels.append(reel)

    return filtered_reels


def _heuristic_filter(reels: list) -> list:
    """Simple engagement-rate fallback when no AI key is available."""
    return [
        r for r in reels
        if ((r.get("likeCount", 0) + r.get("commentCount", 0)) / max(r.get("viewCount", 1), 1)) * 100 >= 2.0
    ]
