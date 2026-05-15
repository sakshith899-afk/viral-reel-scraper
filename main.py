import sys
import json
from scraper.instagram import scrape_instagram_reels
from ai.filter import filter_reels_for_niche
from ai.generator import generate_ideas_from_filtered_data

def main():
    print("=== Instagram Content Idea Generator ===")

    # 1. Get niche from user or use default
    niche = input("Enter your niche (e.g., 'fitness routines', 'indie hacking', 'home baking'): ").strip()
    if not niche:
        niche = "indie hacking"
        print(f"No niche provided. Defaulting to '{niche}'.")

    # 2. Scrape raw data
    print("\n--- STEP 1: Scraping Data ---")
    raw_reels = scrape_instagram_reels(niche, max_results=30)
    print(f"Scraped {len(raw_reels)} raw reels.")

    if not raw_reels:
        print("No reels found. Exiting.")
        return

    # 3. Filter data with AI
    print("\n--- STEP 2: AI Quality Filtering ---")
    filtered_reels = filter_reels_for_niche(raw_reels, niche)
    print(f"Filtering complete. Kept {len(filtered_reels)} high-quality reels.")

    if not filtered_reels:
        print("No reels passed the quality filter. Try a different niche or scraping strategy.")
        return

    # 4. Generate Ideas
    print("\n--- STEP 3: Generating Ideas ---")
    result = generate_ideas_from_filtered_data(filtered_reels, niche)

    # 5. Output results
    print("\n==================================================")
    print(f"         10 REEL IDEAS FOR: {niche.upper()}")
    print("==================================================\n")

    for i, idea in enumerate(result.ideas, 1):
        print(f"💡 IDEA {i}: {idea.title}")
        print(f"   📝 Concept: {idea.concept_explanation}")
        print(f"   🔗 Proof (Original Viral Reel): {idea.original_viral_reel_url}")
        print(f"   🧠 Why it works: {idea.why_it_works}")
        print(f"   ✨ How to make it authentic: {idea.how_to_make_it_authentic}")
        print("-" * 50)

if __name__ == "__main__":
    main()
