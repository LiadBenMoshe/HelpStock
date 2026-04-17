from __future__ import annotations

from datetime import date, timedelta

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.analysis import InsiderActivity, InsiderTransaction, Signal

logger = get_logger(__name__)


async def get_insider_activity(symbol: str) -> InsiderActivity:
    settings = get_settings()
    if not settings.finnhub_api_key:
        return InsiderActivity(
            sentiment="neutral",
            summary="Finnhub API key is not configured, so insider trading data could not be fetched.",
            transactions=[],
        )

    today = date.today()
    start = today - timedelta(days=180)
    url = (
        "https://finnhub.io/api/v1/stock/insider-transactions"
        f"?symbol={symbol.upper()}&from={start.isoformat()}&to={today.isoformat()}&token={settings.finnhub_api_key}"
    )

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        logger.warning("Failed to fetch insider activity for %s: %s", symbol, exc)
        return InsiderActivity(
            sentiment="neutral",
            summary="Insider trading data could not be retrieved from Finnhub.",
            transactions=[],
        )

    transactions = []
    net_change = 0.0
    for item in (payload.get("data") or [])[:10]:
        change = _to_float(item.get("change"))
        net_change += change or 0.0
        transactions.append(
            InsiderTransaction(
                name=item.get("name") or "Unknown",
                relation=item.get("shareholder"),
                transaction_date=item.get("transactionDate") or "",
                transaction_type=item.get("transactionCode") or "N/A",
                shares=_to_float(item.get("share")),
                change=change,
                filing_url=item.get("filingUrl"),
            )
        )

    sentiment: Signal = "neutral"
    summary = "Insider transactions appear mixed over the recent period."
    if net_change > 0:
        sentiment = "positive"
        summary = "Recent insider activity tilts bullish, with net buying or positive share accumulation."
    elif net_change < 0:
        sentiment = "negative"
        summary = "Recent insider activity tilts bearish, with net selling or share reduction."

    return InsiderActivity(
        sentiment=sentiment,
        summary=summary,
        transactions=transactions,
    )


def _to_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None
