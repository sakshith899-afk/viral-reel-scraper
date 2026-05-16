import os
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class ReelIdea(BaseModel):
    title: str
    hook: str
    concept_explanation: str
    suggested_format: str
    suggested_audio: str
    original_viral_reel_url: str
    source_reel_stats: str
    why_it_worked: str
    the_pattern: str
    how_to_make_it_authentic: str


class IdeaGenerationResult(BaseModel):
    ideas: list[ReelIdea]


def generate_ideas_from_filtered_data(filtered_reels: list, niche: str) -> IdeaGenerationResult:
    """
    Sends filtered viral reels to gpt-4o and generates 10 actionable ideas with
    specific hooks, patterns, source stats, and strong traceable reasoning.
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
        views    = reel.get("viewCount", 0)
        likes    = reel.get("likeCount", 0)
        comments = reel.get("commentCount", 0)
        eng_rate = ((likes + comments) / max(views, 1)) * 100
        duration = reel.get("duration")
        audio    = reel.get("audio") or "Original audio"
        days_old = reel.get("daysOld")

        fmt_label = ""
        if duration:
            if duration < 15:
                fmt_label = f"{duration}s — hook-driven"
            elif duration < 30:
                fmt_label = f"{duration}s — story/demo"
            else:
                fmt_label = f"{duration}s — tutorial"

        velocity = ""
        if days_old and views:
            vpd = views // days_old
            velocity = f" | {vpd:,} views/day"

        context_data += (
            f"\nReel {i}:\n"
            f"  URL:        {reel.get('url', '')}\n"
            f"  Caption:    {reel.get('caption', '')[:300]}\n"
            f"  Views:      {views:,}{velocity}\n"
            f"  Engagement: {likes:,} likes, {comments:,} comments ({eng_rate:.1f}%)\n"
            f"  Format:     {fmt_label or 'unknown'}\n"
            f"  Audio:      {audio}\n"
        )

    prompt = f"""
You are an expert Instagram content strategist and viral content analyst.

Below are verified viral Instagram Reels in the '{niche}' niche — these genuinely performed well.
Generate exactly 10 unique, actionable ideas for new Reels based on these.

CRITICAL RULES:
- Every idea must cite the SPECIFIC reel number and URL that inspired it.
- "hook" must be the EXACT opening line or visual description (first 3 seconds). Not vague — write the actual sentence or shot.
- "the_pattern" must be a reusable template a creator can apply to any topic. Example: "Myth-bust: state wrong belief → show consequences → reveal truth → quick CTA"
- "source_reel_stats" must quote the real numbers from the data above (e.g. "1.2M views, 4.1% engagement, 18s reel")
- "suggested_audio" must either name the specific trending audio from the source reel OR explain why original audio works better here.
- "why_it_worked" must name a specific psychological trigger (curiosity gap, identity threat, social proof, FOMO, aspirational contrast, relatability shock, etc.)
- Do NOT invent reel URLs. Use the exact URLs from the data below.

Verified viral data:
{context_data}
"""

    print(f"Generating ideas (source: {'GitHub Models' if is_github else 'OpenAI'})...")
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert Instagram content strategist who gives specific, actionable advice — never vague platitudes."},
                {"role": "user",   "content": prompt},
            ],
            response_format=IdeaGenerationResult,
        )
        result = response.choices[0].message.parsed

        # Validate URLs — replace hallucinated ones with a real source URL
        real_urls = [u for u in valid_urls if u]
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
            title="The Myth Everyone in Your Niche Believes",
            hook="'Everyone told me this was the right way — I did it for 6 months and got zero results.'",
            concept_explanation="Open with the myth, show the negative outcome you experienced, then reveal the counterintuitive truth with a quick visual demonstration.",
            suggested_format="18–22s, talking head with text overlay on the myth, B-roll on the result",
            suggested_audio="Use original audio — personal confession hooks work better without music competing for attention",
            original_viral_reel_url="https://www.instagram.com/reel/mock3/",
            source_reel_stats="500k views, 8.1% engagement, 22s reel",
            why_it_worked="Identity threat — challenges something the viewer already does and makes them question their approach (curiosity gap + pain point).",
            the_pattern="Myth-bust: state common wrong belief → personal cost of believing it → reveal truth → one-sentence CTA",
            how_to_make_it_authentic="Use your own real experience — the specific mistake you made and for how long. Numbers make it real.",
        )
    ])
