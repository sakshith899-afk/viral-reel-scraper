import os
import json
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class RelevanceEvaluation(BaseModel):
    is_relevant: bool
    reasoning: str

def filter_reels_for_niche(reels: list, niche: str) -> list:
    """
    Takes a list of scraped reels and uses an LLM to filter out spam,
    irrelevant content, and engagement bait.
    Keeps only reels that provide actual value for the given niche.
    """
    api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")
    is_github = bool(os.getenv("GITHUB_TOKEN"))

    if not api_key:
        print("Warning: Neither GITHUB_TOKEN nor OPENAI_API_KEY is set. Skipping AI filtering and using heuristics.")
        return _heuristic_filter(reels)

    if is_github:
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=api_key,
        )
        model_name = "gpt-4o-mini"
    else:
        client = OpenAI(api_key=api_key)
        model_name = "gpt-4o-mini"
    filtered_reels = []
    print(f"Starting AI filtering for {len(reels)} reels...")

    for reel in reels:
        # Calculate a basic engagement rate
        views = reel.get("viewCount", 1) # avoid division by zero
        likes = reel.get("likeCount", 0)
        comments = reel.get("commentCount", 0)
        engagement_rate = ((likes + comments) / views) * 100 if views > 0 else 0

        # We can pre-filter completely dead or clearly botted posts before calling OpenAI to save tokens
        if engagement_rate < 0.5 and views > 100000:
            print(f"Skipping Reel {reel['url']} due to extremely low engagement ({engagement_rate:.2f}%). Likely spam.")
            continue

        prompt = f"""
        You are a highly skilled social media analyst. Your job is to evaluate if an Instagram Reel is high-quality, relevant content for a specific niche, or if it's spam/engagement bait.

        Target Niche: {niche}

        Reel Data:
        Caption: {reel.get('caption', 'No caption')}
        Views: {views}
        Likes: {likes}
        Comments: {comments}
        Author: {reel.get('author', 'Unknown')}
        Engagement Rate: {engagement_rate:.2f}%

        Evaluate this reel. Is it genuinely about the target niche? Does it seem to provide value, or is it irrelevant, generic viral spam, or engagement bait?
        """

        try:
            response = client.beta.chat.completions.parse(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a strict data quality filter for social media content."},
                    {"role": "user", "content": prompt}
                ],
                response_format=RelevanceEvaluation,
            )

            evaluation = response.choices[0].message.parsed

            if evaluation.is_relevant:
                print(f"✅ Kept Reel {reel['url']} - Reason: {evaluation.reasoning}")
                filtered_reels.append(reel)
            else:
                print(f"❌ Discarded Reel {reel['url']} - Reason: {evaluation.reasoning}")

        except Exception as e:
            print(f"Error evaluating reel {reel['url']}: {e}")
            # If API fails, we might conservatively skip it or keep it depending on strictness
            pass

    return filtered_reels

def _heuristic_filter(reels: list) -> list:
    """A basic filter if OpenAI is unavailable."""
    filtered = []
    for reel in reels:
        views = reel.get("viewCount", 1)
        likes = reel.get("likeCount", 0)
        engagement_rate = (likes / views) * 100 if views > 0 else 0

        # Simple rule: if engagement is over 2%, we assume it's somewhat decent
        if engagement_rate >= 2.0:
            filtered.append(reel)

    return filtered
