from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.core.cache import TTLCache
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.analysis import AnalysisResponse
from app.services.analysis import analyze_symbol

router = APIRouter(prefix="/analyze", tags=["analyze"])
logger = get_logger(__name__)
cache = TTLCache(ttl_seconds=get_settings().cache_ttl_seconds)


@router.get("/{symbol}", response_model=AnalysisResponse)
async def analyze_stock(
    symbol: str,
    lang: Literal["en", "he"] = Query(default="en"),
) -> AnalysisResponse:
    normalized_symbol = symbol.upper().strip()
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-")
    if not normalized_symbol or any(char not in allowed for char in normalized_symbol):
        raise HTTPException(status_code=400, detail="Stock symbol contains unsupported characters.")

    cache_key = f"{normalized_symbol}:{lang}"
    cached = cache.get(cache_key)
    if cached:
        logger.info("Returning cached analysis for %s (%s)", normalized_symbol, lang)
        return cached

    try:
        result = await analyze_symbol(normalized_symbol, lang=lang)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to analyze %s", normalized_symbol)
        raise HTTPException(
            status_code=502,
            detail=f"Unable to complete analysis for {normalized_symbol}: {exc}",
        ) from exc

    cache.set(cache_key, result)
    return result
