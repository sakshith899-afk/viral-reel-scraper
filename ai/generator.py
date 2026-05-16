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
    Takes the highly relevant, filtered list of viral reels and asks the LLM
    to generate 10 distinct, actionable content ideas based on them.
    """
    api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")
    is_github = bool(os.getenv("GITHUB_TOKEN"))

    if not api_key:
        print("Warning: Neither GITHUB_TOKEN nor OPENAI_API_KEY is set. Returning mock ideas.")
        return _get_mock_ideas()

    if is_github:
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=api_key,
        )
        model_name = "gpt-4o"
    else:
        client = OpenAI(api_key=api_key)
        model_name = "gpt-4o"

    if not filtered_reels:
        print("Error: No filtered reels available to generate ideas from.")
        return IdeaGenerationResult(ideas=[])

    print("Generating ideas based on verified viral content...")

    # Prepare the context for the LLM
    context_data = ""
    for i, reel in enumerate(filtered_reels, 1):
        context_data += f"\nReel {i}:\n"
        context_data += f"URL: {reel['url']}\n"
        context_data += f"Caption: {reel['caption']}\n"
        context_data += f"Engagement: {reel.get('likeCount', 0)} likes, {reel.get('commentCount', 0)} comments on {reel.get('viewCount', 0)} views\n"

    prompt = f"""
    You are an expert social media strategist.
    I will provide you with a list of verified, high-quality viral Instagram Reels in the '{niche}' niche.

    Your task is to analyze these proven concepts and generate exactly 10 unique, actionable ideas for new Instagram Reels.

    For EACH idea, you must provide:
    1. A catchy title.
    2. A clear explanation of the concept (what the creator should do in the video).
    3. The URL of the specific viral reel from the provided list that inspired this idea (as 'proof' that the concept works).
    4. An explanation of *why* the original reel worked so well (e.g., psychological trigger, visual hook, relatable pain point).
    5. Specific advice on how the creator can rewrite or present this concept to make it *authentic* to their own voice, rather than just blindly copying the original.

    Here is the verified viral data:
    {context_data}
    """

    try:
        response = client.beta.chat.completions.parse(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an expert Instagram content strategist."},
                {"role": "user", "content": prompt}
            ],
            response_format=IdeaGenerationResult,
        )
        return response.choices[0].message.parsed

    except Exception as e:
        print(f"Error generating ideas: {e}")
        return IdeaGenerationResult(ideas=[])

def _get_mock_ideas():
    return IdeaGenerationResult(ideas=[
        ReelIdea(
            title="The 'Counter-Intuitive' Tip",
            concept_explanation="Start by stating a common belief in your niche, then debunk it visually.",
            original_viral_reel_url="https://instagram.com/reel/mock3",
            why_it_works="Pattern interruption. It challenges what people think they know.",
            how_to_make_it_authentic="Share a personal story of when you made the common mistake and how fixing it changed your results."
        )
    ])
