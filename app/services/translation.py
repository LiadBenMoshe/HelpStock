from __future__ import annotations

import asyncio
import re

from deep_translator import GoogleTranslator

from app.core.logging import get_logger
from app.models.analysis import AnalysisResponse

logger = get_logger(__name__)

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}")
URL_PATTERN = re.compile(r"^(https?://|www\.)", re.IGNORECASE)


async def localize_analysis(response: AnalysisResponse, language: str) -> AnalysisResponse:
    if language == "en":
        return response
    if language != "he":
        return response

    return await asyncio.to_thread(_translate_analysis_to_hebrew, response)


def _translate_analysis_to_hebrew(response: AnalysisResponse) -> AnalysisResponse:
    translator = GoogleTranslator(source="auto", target="iw")
    payload = response.model_dump()

    payload["language"] = "he"
    payload["company_overview"] = _translate_company_overview(payload["company_overview"], translator)
    payload["support_resistance"] = _translate_support_resistance(payload["support_resistance"], translator)
    payload["insider_activity"] = _translate_insider_activity(payload["insider_activity"], translator)
    payload["revenue_analysis"] = _translate_selected_fields(payload["revenue_analysis"], translator, ["interpretation"])
    payload["pe_analysis"] = _translate_selected_fields(payload["pe_analysis"], translator, ["interpretation"])
    payload["google_trends"] = _translate_selected_fields(
        payload["google_trends"], translator, ["direction", "interpretation"]
    )
    payload["analyst_targets"] = _translate_analyst_targets(payload["analyst_targets"], translator)
    payload["vix_status"] = _translate_selected_fields(
        payload["vix_status"], translator, ["interpretation"]
    )
    payload["news_summaries"] = [
        _translate_selected_fields(item, translator, ["title", "summary"]) for item in payload["news_summaries"]
    ]
    payload["partnerships_and_contracts"] = [
        _translate_selected_fields(item, translator, ["title", "summary", "confidence"])
        for item in payload["partnerships_and_contracts"]
    ]
    payload["product_relevance"] = _translate_product_relevance(payload["product_relevance"], translator)

    return AnalysisResponse.model_validate(payload)


def _translate_company_overview(item: dict, translator: GoogleTranslator) -> dict:
    translated = dict(item)
    for field in ["sector", "industry", "description"]:
        translated[field] = _translate_text(item.get(field), translator)
    translated["products_services"] = [
        _translate_text(entry, translator) for entry in item.get("products_services", [])
    ]
    return translated


def _translate_support_resistance(item: dict, translator: GoogleTranslator) -> dict:
    translated = dict(item)
    translated["methodology"] = _translate_text(item.get("methodology"), translator)
    translated["support_levels"] = [
        {**level, "label": _translate_text(level.get("label"), translator)}
        for level in item.get("support_levels", [])
    ]
    translated["resistance_levels"] = [
        {**level, "label": _translate_text(level.get("label"), translator)}
        for level in item.get("resistance_levels", [])
    ]
    return translated


def _translate_insider_activity(item: dict, translator: GoogleTranslator) -> dict:
    translated = dict(item)
    translated["summary"] = _translate_text(item.get("summary"), translator)
    translated["transactions"] = [
        _translate_selected_fields(entry, translator, ["relation", "transaction_type"])
        for entry in item.get("transactions", [])
    ]
    return translated


def _translate_analyst_targets(item: dict, translator: GoogleTranslator) -> dict:
    translated = dict(item)
    translated["targets"] = [
        _translate_selected_fields(entry, translator, ["analyst"])
        for entry in item.get("targets", [])
    ]
    return translated


def _translate_product_relevance(item: dict, translator: GoogleTranslator) -> dict:
    translated = dict(item)
    translated["interpretation"] = _translate_text(item.get("interpretation"), translator)
    translated["drivers"] = [_translate_text(driver, translator) for driver in item.get("drivers", [])]
    return translated


def _translate_selected_fields(item: dict, translator: GoogleTranslator, fields: list[str]) -> dict:
    translated = dict(item)
    for field in fields:
        translated[field] = _translate_text(item.get(field), translator)
    return translated


def _translate_text(value: str | None, translator: GoogleTranslator) -> str | None:
    if not value:
        return value
    if _should_skip_translation(value):
        return value

    try:
        return translator.translate(value)
    except Exception as exc:
        logger.warning("Translation failed for text '%s': %s", value[:60], exc)
        return value


def _should_skip_translation(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if URL_PATTERN.match(stripped):
        return True
    if DATE_PATTERN.match(stripped):
        return True
    if "@" in stripped or stripped.startswith("^"):
        return True
    return False
