from __future__ import annotations

from pydantic import BaseModel


class CallMetrics(BaseModel):
    total_calls: int = 0
    answered_calls: int = 0
    missed_calls: int = 0
    average_duration: float = 0.0
    recording_success_rate: float = 0.0
    transcription_success_rate: float = 0.0
    callback_rate: float = 0.0


class UrgencyDistribution(BaseModel):
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0
    unknown: int = 0


class SentimentDistribution(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    mixed: int = 0
    unknown: int = 0


class CategoryDistribution(BaseModel):
    sales_inquiry: int = 0
    support: int = 0
    complaint: int = 0
    quotation: int = 0
    partnership: int = 0
    vendor: int = 0
    recruitment: int = 0
    personal: int = 0
    spam: int = 0
    unknown: int = 0


class DailyTrend(BaseModel):
    date: str
    total_calls: int
    answered_calls: int
    missed_calls: int


class WeeklyTrend(BaseModel):
    week: str
    total_calls: int
    average_duration: float


class MonthlyTrend(BaseModel):
    month: str
    total_calls: int
    top_category: str


class AnalyticsDashboard(BaseModel):
    metrics: CallMetrics
    urgency_distribution: UrgencyDistribution
    sentiment_distribution: SentimentDistribution
    category_distribution: CategoryDistribution
    daily_trends: list[DailyTrend]
    weekly_trends: list[WeeklyTrend]
    monthly_trends: list[MonthlyTrend]
    peak_hours: dict
    top_devices: list[dict]
