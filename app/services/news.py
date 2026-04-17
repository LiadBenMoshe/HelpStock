from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Iterable

import httpx
import yfinance as yf

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.analysis import NewsSummary, PartnershipItem, ProductRelevance, Signal

logger = get_logger(__name__)

POSITIVE_WORDS = {"growth", "beats", "partnership", "deal", "launch", "expands", "surge", "wins"}
NEGATIVE_WORDS = {"cuts", "lawsuit", "delay", "decline", "misses", "drops", "risk", "weak"}
PARTNERSHIP_WORDS = {"partnership", "partner", "agreement", "contract", "collaboration", "deal", "supply"}
RELEVANCE_WORDS = {
    "ai": 15,
    "cloud": 12,
    "cybersecurity": 10,
    "semiconductor": 10,
    "automation": 10,
    "electric": 10,
    "software": 8,
    "digital": 8,
    "consumer": 6,
    "platform": 6,
}


def get_news_and_insights(
    symbol: str, company_name: str, description: str
) -> tuple[list[NewsSummary], list[PartnershipItem], ProductRelevance]:
    articles = _collect_articles(symbol, company_name)
    news_items = []
    partnerships = []
    relevance_score = 45
    relevance_drivers = []

    for article in articles[:8]:
        title = article.get("title") or "Untitled article"
        publisher = article.get("publisher")
        link = article.get("link")
        published = article.get("published_at")
        body = article.get("summary") or article.get("description") or article.get("content") or ""
        summary = _summarize_article(title, body, description)
        sentiment = _score_sentiment(" ".join([title, body]))
        news_items.append(
            NewsSummary(
                title=title,
                publisher=publisher,
                link=link,
                published_at=published,
                summary=summary,
                sentiment=sentiment,
            )
        )

        if _contains_keywords(title, body, keywords=PARTNERSHIP_WORDS):
            partnerships.append(
                PartnershipItem(
                    title=title,
                    summary=summary,
                    link=link,
                    confidence="medium",
                )
            )

    combined_text = f"{description} {' '.join(item.title for item in news_items)}".lower()
    for keyword, weight in RELEVANCE_WORDS.items():
        if keyword in combined_text:
            relevance_score += weight
            relevance_drivers.append(f"Exposure to {keyword}-related demand themes.")

    if any(item.sentiment == "positive" for item in news_items):
        relevance_score += 5
        relevance_drivers.append("Recent headlines include constructive catalysts.")
    if not relevance_drivers:
        relevance_drivers.append("Assessment is based mainly on the business description and broad market fit.")

    relevance_score = max(0, min(100, relevance_score))
    relevance_signal: Signal = "neutral"
    relevance_interpretation = "The product mix looks reasonably relevant to current market demand."
    if relevance_score >= 70:
        relevance_signal = "positive"
        relevance_interpretation = "The company appears well aligned with current market narratives and demand trends."
    elif relevance_score <= 40:
        relevance_signal = "negative"
        relevance_interpretation = "The company appears less connected to current high-interest market themes."

    product_relevance = ProductRelevance(
        score=relevance_score,
        interpretation=relevance_interpretation,
        signal=relevance_signal,
        drivers=_dedupe(relevance_drivers)[:4],
    )

    return news_items, partnerships[:4], product_relevance


def _collect_articles(symbol: str, company_name: str) -> list[dict]:
    articles = []
    articles.extend(_fetch_yfinance_news(symbol))
    articles.extend(_fetch_finnhub_news(symbol))
    articles.extend(_fetch_newsapi_news(symbol, company_name))
    return _dedupe_articles(articles)


def _fetch_yfinance_news(symbol: str) -> list[dict]:
    try:
        ticker = yf.Ticker(symbol.upper())
        raw_news = getattr(ticker, "news", None) or []
    except Exception as exc:
        logger.warning("Failed to fetch Yahoo Finance news for %s: %s", symbol, exc)
        return []

    normalized = []
    for article in raw_news:
        content = article.get("content") or {}
        normalized.append(
            {
                "title": article.get("title") or content.get("title"),
                "publisher": article.get("publisher") or content.get("provider", {}).get("displayName"),
                "link": article.get("link") or content.get("canonicalUrl", {}).get("url"),
                "published_at": _format_timestamp(
                    article.get("providerPublishTime") or content.get("pubDate")
                ),
                "summary": article.get("summary") or content.get("summary"),
                "description": content.get("description"),
                "content": content.get("body"),
            }
        )
    return normalized


def _fetch_finnhub_news(symbol: str) -> list[dict]:
    settings = get_settings()
    if not settings.finnhub_api_key:
        return []

    today = date.today()
    start = today - timedelta(days=21)
    url = (
        "https://finnhub.io/api/v1/company-news"
        f"?symbol={symbol.upper()}&from={start.isoformat()}&to={today.isoformat()}&token={settings.finnhub_api_key}"
    )

    try:
        with httpx.Client(timeout=15) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        logger.warning("Failed to fetch Finnhub news for %s: %s", symbol, exc)
        return []

    normalized = []
    for article in payload[:8]:
        normalized.append(
            {
                "title": article.get("headline"),
                "publisher": article.get("source"),
                "link": article.get("url"),
                "published_at": _format_timestamp(article.get("datetime")),
                "summary": article.get("summary"),
                "description": article.get("summary"),
                "content": "",
            }
        )
    return normalized


def _fetch_newsapi_news(symbol: str, company_name: str) -> list[dict]:
    settings = get_settings()
    if not settings.newsapi_api_key:
        return []

    query = f'"{company_name}" OR {symbol.upper()}'
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 8,
        "apiKey": settings.newsapi_api_key,
    }

    try:
        with httpx.Client(timeout=15) as client:
            response = client.get("https://newsapi.org/v2/everything", params=params)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        logger.warning("Failed to fetch NewsAPI news for %s: %s", symbol, exc)
        return []

    normalized = []
    for article in payload.get("articles", [])[:8]:
        normalized.append(
            {
                "title": article.get("title"),
                "publisher": (article.get("source") or {}).get("name"),
                "link": article.get("url"),
                "published_at": article.get("publishedAt"),
                "summary": article.get("description"),
                "description": article.get("description"),
                "content": article.get("content"),
            }
        )
    return normalized


def _dedupe_articles(items: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for item in items:
        title = (item.get("title") or "").strip()
        link = (item.get("link") or "").strip()
        key = (title.lower(), link.lower())
        if not title or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _summarize_article(title: str, body: str, description: str) -> str:
    content = (body or description or "").strip()
    if not content:
        return f"{title}. Limited article metadata was available, so the summary is based on the headline context."

    normalized = content.replace("\n", " ").replace("…", ". ")
    sentences = [sentence.strip(" -") for sentence in normalized.split(".") if sentence.strip()]
    chosen = sentences[:2]
    if not chosen:
        chosen = [normalized[:220].strip()]
    summary = ". ".join(chosen)
    if len(summary) > 260:
        summary = summary[:257].rstrip() + "..."
    if not summary.endswith((".", "!", "?")):
        summary += "."
    return summary


def _score_sentiment(text: str) -> Signal:
    lowered = text.lower()
    pos = sum(1 for word in POSITIVE_WORDS if word in lowered)
    neg = sum(1 for word in NEGATIVE_WORDS if word in lowered)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def _contains_keywords(*parts: str, keywords: Iterable[str]) -> bool:
    merged = " ".join(parts).lower()
    return any(keyword in merged for keyword in keywords)


def _format_timestamp(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return str(value)


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
