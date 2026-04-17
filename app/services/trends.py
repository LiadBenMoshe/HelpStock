from __future__ import annotations

import re

from pytrends.request import TrendReq

from app.core.logging import get_logger
from app.models.analysis import GoogleTrendsAnalysis, Signal

logger = get_logger(__name__)

COMPANY_SUFFIXES = (
    " inc",
    " inc.",
    " corporation",
    " corp",
    " corp.",
    " ltd",
    " ltd.",
    " limited",
    " plc",
    " holdings",
    " group",
    " co",
    " co.",
)


def get_google_trends(company_name: str, symbol: str) -> GoogleTrendsAnalysis:
    candidates = _build_candidates(company_name, symbol)
    pytrends = TrendReq(hl="en-US", tz=0)

    best_result = None
    last_error: Exception | None = None

    for keyword in candidates:
        for timeframe in ("today 3-m", "today 12-m"):
            try:
                pytrends.build_payload([keyword], timeframe=timeframe, geo="US")
                interest = pytrends.interest_over_time()
                if interest.empty or keyword not in interest.columns:
                    continue

                series = interest[keyword].dropna()
                if series.empty:
                    continue

                recent = series.tail(min(4, len(series)))
                score = int(series.iloc[-1])
                delta = int(recent.iloc[-1] - recent.iloc[0]) if len(recent) > 1 else 0
                momentum = abs(delta) + int(series.mean())
                result = _build_trends_result(keyword, score, delta)

                if best_result is None or momentum > best_result["momentum"]:
                    best_result = {"momentum": momentum, "result": result}
            except Exception as exc:
                last_error = exc
                logger.debug("Google Trends lookup failed for %s (%s): %s", keyword, timeframe, exc)

    if best_result is not None:
        return best_result["result"]

    if last_error:
        logger.warning("Failed to fetch Google Trends for %s: %s", symbol, last_error)

    fallback_keyword = candidates[0] if candidates else symbol.upper()
    return GoogleTrendsAnalysis(
        keyword=fallback_keyword,
        score=None,
        direction="unknown",
        interpretation="Google Trends data is unavailable right now. Try a broader company name or check API connectivity.",
        signal="neutral",
    )


def _build_candidates(company_name: str, symbol: str) -> list[str]:
    cleaned_name = _clean_company_name(company_name)
    candidates = [
        cleaned_name,
        symbol.upper(),
        f"{cleaned_name} stock" if cleaned_name else "",
        company_name.strip() if company_name else "",
    ]

    unique = []
    seen = set()
    for item in candidates:
        normalized = item.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(normalized)
    return unique


def _clean_company_name(company_name: str) -> str:
    cleaned = re.sub(r"\s+", " ", (company_name or "").strip())
    lowered = cleaned.lower()
    for suffix in COMPANY_SUFFIXES:
        if lowered.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip(", ")
            lowered = cleaned.lower()
    return cleaned


def _build_trends_result(keyword: str, score: int, delta: int) -> GoogleTrendsAnalysis:
    signal: Signal = "neutral"
    direction = "stable"
    interpretation = "Search interest is holding relatively steady."

    if delta >= 10:
        signal = "positive"
        direction = "increasing"
        interpretation = "Search interest is rising, which can indicate improving retail attention."
    elif delta <= -10:
        signal = "negative"
        direction = "decreasing"
        interpretation = "Search interest is fading, suggesting lower recent attention."

    return GoogleTrendsAnalysis(
        keyword=keyword,
        score=score,
        direction=direction,
        interpretation=interpretation,
        signal=signal,
    )
