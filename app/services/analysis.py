from __future__ import annotations

from datetime import datetime, timezone

from app.core.logging import get_logger
from app.models.analysis import (
    AnalysisResponse,
    AnalystTargetStats,
    AnalystTargets,
    CompanyOverview,
    GoogleTrendsAnalysis,
    InsiderActivity,
    PEAnalysis,
    ProductRelevance,
    RevenueAnalysis,
    SupportResistance,
    VixStatus,
)
from app.services.insider import get_insider_activity
from app.services.market_data import (
    get_analyst_targets,
    get_company_overview,
    get_pe_analysis,
    get_revenue_analysis,
    get_support_resistance,
    get_vix_status,
)
from app.services.news import get_news_and_insights
from app.services.translation import localize_analysis
from app.services.trends import get_google_trends

logger = get_logger(__name__)


async def analyze_symbol(symbol: str, lang: str = "en") -> AnalysisResponse:
    normalized_symbol = symbol.upper().strip()
    logger.info("Running full analysis for %s", normalized_symbol)

    overview = _safe_sync_call(
        lambda: get_company_overview(normalized_symbol),
        "company overview",
        CompanyOverview(
            name=normalized_symbol,
            description="Company overview is currently unavailable.",
            products_services=[],
        ),
    )
    support_resistance = _safe_sync_call(
        lambda: get_support_resistance(normalized_symbol),
        "support and resistance",
        SupportResistance(
            support_levels=[],
            resistance_levels=[],
            methodology="Support and resistance data is currently unavailable.",
        ),
    )
    revenue_analysis = _safe_sync_call(
        lambda: get_revenue_analysis(normalized_symbol),
        "revenue analysis",
        RevenueAnalysis(
            interpretation="Revenue analysis is currently unavailable.",
            signal="neutral",
        ),
    )
    pe_analysis = _safe_sync_call(
        lambda: get_pe_analysis(normalized_symbol),
        "P/E analysis",
        PEAnalysis(
            interpretation="P/E analysis is currently unavailable.",
            signal="neutral",
        ),
    )
    analyst_targets = _safe_sync_call(
        lambda: get_analyst_targets(normalized_symbol),
        "analyst targets",
        AnalystTargets(stats=AnalystTargetStats(), targets=[]),
    )
    vix_status = _safe_sync_call(
        get_vix_status,
        "VIX status",
        VixStatus(
            value=None,
            label_he="ניטרלי",
            interpretation="VIX status is currently unavailable.",
            signal="neutral",
        ),
    )
    google_trends = _safe_sync_call(
        lambda: get_google_trends(overview.name, normalized_symbol),
        "Google Trends",
        GoogleTrendsAnalysis(
            keyword=overview.name,
            score=None,
            direction="unknown",
            interpretation="Google Trends data is currently unavailable.",
            signal="neutral",
        ),
    )
    insider_activity = await _safe_async_call(
        lambda: get_insider_activity(normalized_symbol),
        "insider activity",
        InsiderActivity(
            sentiment="neutral",
            summary="Insider activity is currently unavailable.",
            transactions=[],
        ),
    )
    news_summaries, partnerships, product_relevance = _safe_sync_call(
        lambda: get_news_and_insights(normalized_symbol, overview.name, overview.description),
        "news and product relevance",
        (
            [],
            [],
            ProductRelevance(
                score=50,
                interpretation="Product relevance could not be determined.",
                signal="neutral",
                drivers=[],
            ),
        ),
    )

    result = AnalysisResponse(
        symbol=normalized_symbol,
        language="en",
        generated_at=datetime.now(timezone.utc).isoformat(),
        company_overview=overview,
        support_resistance=support_resistance,
        insider_activity=insider_activity,
        revenue_analysis=revenue_analysis,
        pe_analysis=pe_analysis,
        google_trends=google_trends,
        analyst_targets=analyst_targets,
        vix_status=vix_status,
        news_summaries=news_summaries,
        partnerships_and_contracts=partnerships,
        product_relevance=product_relevance,
    )
    return await localize_analysis(result, lang)


def _safe_sync_call(func, label: str, fallback):
    try:
        return func()
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", label, exc)
        return fallback


async def _safe_async_call(func, label: str, fallback):
    try:
        return await func()
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", label, exc)
        return fallback
