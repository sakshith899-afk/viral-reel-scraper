import os
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class ReelIdea(BaseModel):
    title: str
    concept_explanation: str
    original_viral_reel_url: str
    why_it_works: str
    how_to_make_it_authentic: str


class IdeaGenerationResult(BaseModel):
    ideas: list[ReelIdea]


def generate_ideas_from_filtered_data(filtered_reels: list, niche: str) -> IdeaGenerationResult:
    """
    Sends the filtered viral reels to an LLM and asks for 10 actionable content ideas.
    Supports GitHub Models (free) or OpenAI (paid).
    """
    api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Warning: No API key set. Returning mock ideas.")
        return _get_mock_ideas()

    if not filtered_reels:
        print("No filtered reels to generate from.")
        return IdeaGenerationResult(ideas=[])

    is_github = bool(os.getenv("GITHUB_TOKEN"))
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com" if is_github else None,
        api_key=api_key,
    )

    valid_urls = {r.get("url", "") for r in filtered_reels}

    context_data = ""
    for i, reel in enumerate(filtered_reels, 1):
        context_data += (
            f"\nReel {i}:\n"
            f"  URL:        {reel.get('url', '')}\n"
            f"  Caption:    {reel.get('caption', '')}\n"
            f"  Engagement: {reel.get('likeCount', 0):,} likes, "
            f"{reel.get('commentCount', 0):,} comments on "
            f"{reel.get('viewCount', 0):,} views\n"
        )

    prompt = f"""
You are an expert Instagram content strategist.

Below is a list of verified viral Instagram Reels in the '{niche}' niche.
Generate exactly 10 unique, actionable ideas for new Reels based on these.

For EACH idea provide:
1. A catchy title.
2. A clear concept explanation (what the creator should do in the video).
3. The URL of the specific reel from the list below that inspired this idea — copy the URL exactly as shown, do not invent one.
4. Why the original reel worked (psychological trigger, visual hook, pain point, etc.).
5. How the creator can make it authentic to their own voice instead of just copying.

Verified viral data:
{context_data}
"""

    print(f"Generating ideas (source: {'GitHub Models' if is_github else 'OpenAI'})...")
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert Instagram content strategist."},
                {"role": "user",   "content": prompt},
            ],
            response_format=IdeaGenerationResult,
        )
        result = response.choices[0].message.parsed

        real_urls = list(valid_urls - {""})
        for idea in result.ideas:
            if idea.original_viral_reel_url not in valid_urls and real_urls:
                idea.original_viral_reel_url = real_urls[0]

        return result

    except Exception as e:
        print(f"Error generating ideas: {e}")
        return IdeaGenerationResult(ideas=[])


def _get_mock_ideas() -> IdeaGenerationResult:
    return IdeaGenerationResult(ideas=[
        ReelIdea(
            title="The Counter-Intuitive Tip",
            concept_explanation="State a common belief in your niche, then visually debunk it.",
            original_viral_reel_url="https://www.instagram.com/reel/mock3/",
            why_it_works="Pattern interruption — challenges what people think they know.",
            how_to_make_it_authentic="Share a personal story of when you believed the myth and how fixing it changed your results.",
        )
    ])
