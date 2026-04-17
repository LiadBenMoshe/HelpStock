from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


Signal = Literal["positive", "negative", "neutral"]


class PriceLevel(BaseModel):
    label: str
    price: float


class SupportResistance(BaseModel):
    support_levels: List[PriceLevel] = Field(default_factory=list)
    resistance_levels: List[PriceLevel] = Field(default_factory=list)
    methodology: str


class InsiderTransaction(BaseModel):
    name: str
    relation: str | None = None
    transaction_date: str
    transaction_type: str
    shares: float | None = None
    change: float | None = None
    filing_url: str | None = None


class InsiderActivity(BaseModel):
    sentiment: Signal
    summary: str
    transactions: List[InsiderTransaction] = Field(default_factory=list)


class RevenueAnalysis(BaseModel):
    latest_quarter: str | None = None
    year_ago_quarter: str | None = None
    latest_revenue: float | None = None
    year_ago_revenue: float | None = None
    growth_percent: float | None = None
    interpretation: str
    signal: Signal


class PEAnalysis(BaseModel):
    current_pe: float | None = None
    previous_year_pe: float | None = None
    interpretation: str
    signal: Signal


class GoogleTrendsAnalysis(BaseModel):
    keyword: str
    score: int | None = None
    direction: str
    interpretation: str
    signal: Signal


class AnalystTargetStats(BaseModel):
    minimum: float | None = None
    maximum: float | None = None
    average: float | None = None
    median: float | None = None


class AnalystTarget(BaseModel):
    source: str
    target_price: float
    published_at: str | None = None
    analyst: str | None = None


class AnalystTargets(BaseModel):
    stats: AnalystTargetStats
    targets: List[AnalystTarget] = Field(default_factory=list)


class VixStatus(BaseModel):
    value: float | None = None
    label_he: str
    interpretation: str
    signal: Signal


class NewsSummary(BaseModel):
    title: str
    publisher: str | None = None
    link: str | None = None
    published_at: str | None = None
    summary: str
    sentiment: Signal


class PartnershipItem(BaseModel):
    title: str
    summary: str
    link: str | None = None
    confidence: str


class ProductRelevance(BaseModel):
    score: int
    interpretation: str
    signal: Signal
    drivers: List[str] = Field(default_factory=list)


class CompanyOverview(BaseModel):
    name: str
    sector: str | None = None
    industry: str | None = None
    website: str | None = None
    description: str
    products_services: List[str] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    symbol: str
    language: str = "en"
    generated_at: str
    company_overview: CompanyOverview
    support_resistance: SupportResistance
    insider_activity: InsiderActivity
    revenue_analysis: RevenueAnalysis
    pe_analysis: PEAnalysis
    google_trends: GoogleTrendsAnalysis
    analyst_targets: AnalystTargets
    vix_status: VixStatus
    news_summaries: List[NewsSummary] = Field(default_factory=list)
    partnerships_and_contracts: List[PartnershipItem] = Field(default_factory=list)
    product_relevance: ProductRelevance
