"""
FastAPI server — exposes POST /generate for the frontend.
Run: uvicorn api:app --reload
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scraper.instagram import scrape_instagram_reels
from ai.filter import filter_reels_for_niche
from ai.generator import generate_ideas_from_filtered_data

app = FastAPI(title="Viral Reel Idea Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    niche: str


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/generate")
def generate(req: GenerateRequest):
    niche = req.niche.strip()
    if not niche:
        raise HTTPException(status_code=400, detail="Niche cannot be empty.")

    raw_reels = scrape_instagram_reels(niche, max_results=30)
    if not raw_reels:
        raise HTTPException(status_code=404, detail="No reels found for this niche.")

    filtered_reels = filter_reels_for_niche(raw_reels, niche)
    if not filtered_reels:
        raise HTTPException(status_code=404, detail="No reels passed the quality filter. Try a broader niche.")

    result = generate_ideas_from_filtered_data(filtered_reels, niche)
    return {"ideas": [idea.model_dump() for idea in result.ideas]}
