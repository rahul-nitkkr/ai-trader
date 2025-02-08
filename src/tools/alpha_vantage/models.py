from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class BaseResponse:
    """Base class for all Alpha Vantage API responses"""
    status_code: int
    raw_response: Dict[str, Any]

@dataclass
class NewsArticle:
    title: str
    url: str
    time_published: datetime
    authors: List[str]
    summary: str
    source: str
    category_within_source: str
    source_domain: str
    topics: List[str]
    overall_sentiment_score: float
    overall_sentiment_label: str
    ticker_sentiment: List[Dict[str, Any]]

@dataclass
class NewsSentimentResponse(BaseResponse):
    items: List[NewsArticle]
    total_count: int

@dataclass
class InsiderTransaction:
    symbol: str
    filing_date: datetime
    transaction_date: datetime
    transaction_type: str
    shares: int
    price: float
    insider_name: str
    insider_title: str

@dataclass
class InsiderTransactionsResponse(BaseResponse):
    transactions: List[InsiderTransaction]

@dataclass
class CompanyOverview:
    symbol: str
    name: str
    description: str
    exchange: str
    currency: str
    country: str
    sector: str
    industry: str
    market_cap: float
    pe_ratio: float
    pb_ratio: float
    dividend_yield: float
    eps: float
    revenue_ttm: float
    profit_margin: float
    beta: float
    fifty_two_week_high: float
    fifty_two_week_low: float

@dataclass
class ETFProfile:
    symbol: str
    name: str
    asset_class: str
    expense_ratio: float
    nav: float
    shares_outstanding: int
    avg_daily_volume: int
    holdings: List[Dict[str, Any]]
    sector_weights: Dict[str, float]
    country_weights: Dict[str, float]

@dataclass
class FinancialStatement:
    symbol: str
    fiscal_date_ending: datetime
    reported_currency: str
    items: Dict[str, float]

@dataclass
class IncomeStatement(FinancialStatement):
    pass

@dataclass
class BalanceSheet(FinancialStatement):
    pass

@dataclass
class CashFlow(FinancialStatement):
    pass

@dataclass
class EarningsData:
    symbol: str
    fiscal_date_ending: datetime
    reported_eps: float
    estimated_eps: float
    surprise: float
    surprise_percentage: float

@dataclass
class ListingStatus:
    symbol: str
    name: str
    exchange: str
    asset_type: str
    ipo_date: datetime
    delisting_date: Optional[datetime]
    status: str

@dataclass
class EarningsCalendarEvent:
    symbol: str
    name: str
    report_date: datetime
    fiscal_date_ending: datetime
    estimate: float
    currency: str

@dataclass
class IPOCalendarEvent:
    symbol: str
    name: str
    ipo_date: datetime
    price_range: str
    currency: str
    exchange: str
    shares_offered: int
    estimated_volume: float 