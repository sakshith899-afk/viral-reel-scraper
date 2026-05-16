import os
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class HashtagExpansion(BaseModel):
    hashtags: list[str]


class ProfileNiche(BaseModel):
    niche: str
    hashtags: list[str]


def _make_client():
    api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, None
    is_github = bool(os.getenv("GITHUB_TOKEN"))
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com" if is_github else None,
        api_key=api_key,
    )
    return client, is_github


def expand_hashtags(niche: str) -> list[str]:
    """Expand a niche keyword into 3-4 specific community hashtags where viral content lives."""
    client, _ = _make_client()
    if not client:
        return [niche.lower().replace(" ", "")]

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an Instagram hashtag expert. Return community-specific hashtags, not generic ones."},
                {"role": "user", "content": f"""
For the niche "{niche}", give exactly 4 Instagram hashtags that are:
- Specific enough to have a tight community (not #fitness with 500M posts)
- Where viral content actually gets discovered by real niche audiences
- No spaces, no #, all lowercase

Examples:
- "fitness" → ["gymmotivation","workoutroutine","fitnesstips","homeworkout"]
- "cooking" → ["mealprep","easyrecipes","cookingathome","foodhacks"]
- "travel" → ["travelhacks","solotravel","budgettravel","travelreels"]

Return only the hashtags array.
"""},
            ],
            response_format=HashtagExpansion,
        )
        tags = response.choices[0].message.parsed.hashtags[:4]
        print(f"Expanded '{niche}' → {tags}")
        return tags
    except Exception as e:
        print(f"Hashtag expansion failed: {e}. Using niche as-is.")
        return [niche.lower().replace(" ", "")]


def derive_niche_from_profile(profile_reels: list) -> dict:
    """
    Analyze a creator's own reels to derive their specific niche and best research hashtags.
    Returns {"niche": str, "hashtags": list[str]}.
    """
    client, _ = _make_client()
    if not client or not profile_reels:
        return {"niche": "general content", "hashtags": ["reels", "viral", "trending", "instagram"]}

    summary = ""
    for i, reel in enumerate(profile_reels[:12], 1):
        caption = (reel.get("caption") or "")[:200]
        hashtags_used = ", ".join((reel.get("hashtags") or [])[:8])
        views = reel.get("viewCount", 0)
        summary += f"\nPost {i}: Caption: {caption} | Views: {views:,} | Tags: {hashtags_used}"

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an Instagram content strategist who specializes in precise niche identification."},
                {"role": "user", "content": f"""
Analyze this Instagram creator's content and return:
1. Their specific niche — be precise, not broad. E.g. "budget meal prep for college students" not just "food".
2. The 4 best hashtags to find viral content in that exact niche (no spaces, no #, lowercase).

Their recent posts:
{summary}
"""},
            ],
            response_format=ProfileNiche,
        )
        result = response.choices[0].message.parsed
        print(f"Derived niche: '{result.niche}' | Hashtags: {result.hashtags[:4]}")
        return {"niche": result.niche, "hashtags": result.hashtags[:4]}
    except Exception as e:
        print(f"Niche derivation failed: {e}.")
        return {"niche": "general content", "hashtags": ["reels", "viral", "trending", "instagram"]}
