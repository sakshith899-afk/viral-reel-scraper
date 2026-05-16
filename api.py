"""
FastAPI server — exposes POST /generate for the frontend.
Run: uvicorn api:app --reload
"""
import os
import httpx
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError

from scraper.instagram import scrape_instagram_reels
from ai.filter import filter_reels_for_niche
from ai.generator import generate_ideas_from_filtered_data

CLERK_JWKS_URL = "https://cuddly-hawk-22.clerk.accounts.dev/.well-known/jwks.json"
_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        _jwks_cache = httpx.get(CLERK_JWKS_URL).json()
    return _jwks_cache

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            get_jwks(),
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please sign in again.")


app = FastAPI(title="Viral Reel Idea Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://viral-reel-scraper.netlify.app",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
    ],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    niche: str


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/status")
def status(user=Depends(verify_token)):
    gh = os.getenv("GITHUB_TOKEN", "")
    ap = os.getenv("APIFY_API_TOKEN", "")
    def mask(s):
        if not s:
            return "not set"
        return f"{'•' * (len(s) - 6)}{s[-6:]}" if len(s) > 6 else s
    return {
        "github_token": mask(gh),
        "apify_token": mask(ap),
    }


@app.post("/generate")
def generate(req: GenerateRequest, user=Depends(verify_token)):
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
