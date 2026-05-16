def filter_reels_for_niche(reels: list, niche: str) -> list:
    """
    Filters reels using tiered viral thresholds.
    Real viral content starts at 200k+ views — we use that as the primary bar.
    Falls back to lower tiers only if the scrape returns thin results.
    """
    def engagement_rate(r):
        views = r.get("viewCount", 1) or 1
        return ((r.get("likeCount", 0) or 0) + (r.get("commentCount", 0) or 0)) / views * 100

    tiers = [
        (200_000, 2.0),   # real viral: 200k views + 2% engagement
        (50_000,  2.0),   # decent: 50k views + engagement
        (20_000,  0.0),   # last resort: any 20k+ post
    ]

    for min_views, min_eng in tiers:
        result = [r for r in reels if r.get("viewCount", 0) >= min_views and engagement_rate(r) >= min_eng]
        if len(result) >= 3:
            print(f"Filter: kept {len(result)} reels (≥{min_views//1000}k views, ≥{min_eng}% eng)")
            return result

    # If absolutely nothing passes, return top 3 by views rather than empty
    top3 = sorted(reels, key=lambda r: r.get("viewCount", 0), reverse=True)[:3]
    print(f"Filter: all reels below viral thresholds — returning top {len(top3)} by views anyway")
    return top3
