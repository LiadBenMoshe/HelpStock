from __future__ import annotations

from datetime import datetime

import yfinance as yf

from app.core.logging import get_logger
from app.models.analysis import (
    AnalystTarget,
    AnalystTargetStats,
    AnalystTargets,
    CompanyOverview,
    PEAnalysis,
    PriceLevel,
    RevenueAnalysis,
    Signal,
    SupportResistance,
    VixStatus,
)

logger = get_logger(__name__)


def get_ticker(symbol: str) -> yf.Ticker:
    return yf.Ticker(symbol.upper())


def get_company_overview(symbol: str) -> CompanyOverview:
    ticker = get_ticker(symbol)
    info = ticker.info or {}
    description = info.get("longBusinessSummary") or "Company description is not available."
    products = _extract_products(description)
    return CompanyOverview(
        name=info.get("shortName") or info.get("longName") or symbol.upper(),
        sector=info.get("sector"),
        industry=info.get("industry"),
        website=info.get("website"),
        description=description,
        products_services=products,
    )


def get_support_resistance(symbol: str) -> SupportResistance:
    ticker = get_ticker(symbol)
    history = ticker.history(period="6mo", interval="1d", auto_adjust=False)
    if history.empty:
        return SupportResistance(
            support_levels=[],
            resistance_levels=[],
            methodology="No historical price data was returned by the market data provider.",
        )

    history = history.dropna(subset=["High", "Low"])
    history["low_min"] = history["Low"].rolling(window=5, center=True).min()
    history["high_max"] = history["High"].rolling(window=5, center=True).max()

    support_candidates = history[history["Low"] == history["low_min"]]["Low"].tail(3).tolist()
    resistance_candidates = history[history["High"] == history["high_max"]]["High"].tail(3).tolist()

    current_close = float(history["Close"].iloc[-1])
    if not support_candidates:
        support_candidates = [float(history["Low"].tail(20).min())]
    if not resistance_candidates:
        resistance_candidates = [float(history["High"].tail(20).max())]

    support_levels = [
        PriceLevel(label=f"Support {idx + 1}", price=round(price, 2))
        for idx, price in enumerate(sorted(_dedupe_price_levels(support_candidates), reverse=True))
    ]
    resistance_levels = [
        PriceLevel(label=f"Resistance {idx + 1}", price=round(price, 2))
        for idx, price in enumerate(sorted(_dedupe_price_levels(resistance_candidates)))
    ]

    return SupportResistance(
        support_levels=support_levels,
        resistance_levels=resistance_levels,
        methodology=(
            f"Calculated from 6 months of daily candles using local highs/lows. "
            f"Latest close used for context: {current_close:.2f}."
        ),
    )


def get_revenue_analysis(symbol: str) -> RevenueAnalysis:
    ticker = get_ticker(symbol)
    quarterly_financials = ticker.quarterly_financials
    if quarterly_financials.empty or "Total Revenue" not in quarterly_financials.index:
        return RevenueAnalysis(
            interpretation="Quarterly revenue data is unavailable from the provider.",
            signal="neutral",
        )

    revenues = quarterly_financials.loc["Total Revenue"].dropna()
    if len(revenues) < 2:
        return RevenueAnalysis(
            interpretation="Not enough quarterly revenue history to compare against last year.",
            signal="neutral",
        )

    latest_date = revenues.index[0]
    latest_revenue = float(revenues.iloc[0])
    if len(revenues) >= 5:
        year_ago_date = revenues.index[4]
        year_ago_revenue = float(revenues.iloc[4])
    else:
        year_ago_date = revenues.index[-1]
        year_ago_revenue = float(revenues.iloc[-1])

    growth_percent = None
    if year_ago_revenue:
        growth_percent = round(((latest_revenue - year_ago_revenue) / year_ago_revenue) * 100, 2)

    signal: Signal = "neutral"
    interpretation = "Revenue is relatively stable year over year."
    if growth_percent is not None:
        if growth_percent >= 10:
            signal = "positive"
            interpretation = "Revenue is growing strongly versus the comparable period last year."
        elif growth_percent <= -5:
            signal = "negative"
            interpretation = "Revenue declined meaningfully versus the comparable period last year."

    return RevenueAnalysis(
        latest_quarter=_format_period(latest_date),
        year_ago_quarter=_format_period(year_ago_date),
        latest_revenue=latest_revenue,
        year_ago_revenue=year_ago_revenue,
        growth_percent=growth_percent,
        interpretation=interpretation,
        signal=signal,
    )


def get_pe_analysis(symbol: str) -> PEAnalysis:
    ticker = get_ticker(symbol)
    info = ticker.info or {}
    current_pe = _to_float(info.get("trailingPE"))

    history = ticker.history(period="1y", interval="1mo", auto_adjust=False)
    eps = _to_float(info.get("trailingEps"))
    previous_year_pe = None
    if eps and not history.empty:
        previous_year_price = float(history["Close"].iloc[0])
        previous_year_pe = round(previous_year_price / eps, 2) if eps else None

    interpretation = "P/E is within a typical range relative to its own recent history."
    signal: Signal = "neutral"
    if current_pe is None:
        interpretation = "Current P/E ratio is unavailable."
    elif previous_year_pe is not None:
        if current_pe <= previous_year_pe * 0.85:
            signal = "positive"
            interpretation = "The stock is trading at a lower multiple than a year ago, suggesting cheaper valuation."
        elif current_pe >= previous_year_pe * 1.15:
            signal = "negative"
            interpretation = "The stock trades at a richer multiple than a year ago, suggesting a more expensive valuation."
    elif current_pe >= 35:
        signal = "negative"
        interpretation = "The stock is trading at an elevated earnings multiple."
    elif current_pe <= 15:
        signal = "positive"
        interpretation = "The stock is trading at a modest earnings multiple."

    return PEAnalysis(
        current_pe=current_pe,
        previous_year_pe=previous_year_pe,
        interpretation=interpretation,
        signal=signal,
    )


def get_analyst_targets(symbol: str) -> AnalystTargets:
    ticker = get_ticker(symbol)
    analyst_targets: list[AnalystTarget] = []
    info = ticker.info or {}

    low_target = _to_float(info.get("targetLowPrice"))
    mean_target = _to_float(info.get("targetMeanPrice"))
    median_target = _to_float(info.get("targetMedianPrice"))
    high_target = _to_float(info.get("targetHighPrice"))

    derived_targets = [
        ("Low consensus", low_target),
        ("Mean consensus", mean_target),
        ("Median consensus", median_target),
        ("High consensus", high_target),
    ]
    for label, value in derived_targets:
        if value is not None:
            analyst_targets.append(
                AnalystTarget(
                    source="consensus",
                    analyst=label,
                    target_price=value,
                )
            )

    stats = AnalystTargetStats(
        minimum=low_target,
        maximum=high_target,
        average=mean_target,
        median=median_target,
    )
    return AnalystTargets(stats=stats, targets=analyst_targets)


def get_vix_status() -> VixStatus:
    vix = yf.Ticker("^VIX")
    history = vix.history(period="5d", interval="1d")
    value = None if history.empty else round(float(history["Close"].iloc[-1]), 2)

    if value is None:
        return VixStatus(
            value=None,
            label_he="ניטרלי",
            interpretation="VIX data is currently unavailable.",
            signal="neutral",
        )
    if value >= 25:
        return VixStatus(
            value=value,
            label_he="פחד",
            interpretation="Elevated volatility suggests a risk-off market tone.",
            signal="negative",
        )
    if value <= 15:
        return VixStatus(
            value=value,
            label_he="שאננות",
            interpretation="Low volatility suggests calm market conditions and possible complacency.",
            signal="positive",
        )
    return VixStatus(
        value=value,
        label_he="ניטרלי",
        interpretation="Volatility is in a balanced range.",
        signal="neutral",
    )


def _dedupe_price_levels(levels: list[float], tolerance: float = 0.01) -> list[float]:
    cleaned: list[float] = []
    for level in levels:
        if not any(abs(level - existing) / max(existing, 1) <= tolerance for existing in cleaned):
            cleaned.append(float(level))
    return cleaned[:3]


def _extract_products(description: str) -> list[str]:
    if not description:
        return []
    fragments = [description]
    for separator in [";", "."]:
        next_fragments: list[str] = []
        for fragment in fragments:
            next_fragments.extend(fragment.split(separator))
        fragments = next_fragments

    keywords = []
    for fragment in fragments:
        trimmed = fragment.strip()
        if 20 <= len(trimmed) <= 110:
            keywords.append(trimmed)
        if len(keywords) == 4:
            break
    return keywords


def _format_period(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)


def _to_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return round(float(value), 2)
    except (TypeError, ValueError):
        logger.debug("Could not parse numeric value: %s", value)
        return None
