from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Tender:
    number: str
    title: str
    nmc: float
    customer: str
    region: str
    publish_date: str
    url: str
    delivery_deadline: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "new"
    cost_estimate: Optional[float] = None
    margin_percent: Optional[float] = None
    rating: Optional[str] = None
    analysis_text: Optional[str] = None
    analyzed_at: Optional[str] = None


@dataclass
class AnalysisResult:
    tender_number: str
    cost_estimate: float
    margin_percent: float
    rating: str
    risks: list
    summary: str
    disclaimer: str = "⚠️ Оценка, требует проверки. Расчёт на основе % от НМЦ."
