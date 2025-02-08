from enum import Enum, auto

class Function(str, Enum):
    """Alpha Vantage API Functions"""
    NEWS_SENTIMENT = "NEWS_SENTIMENT"
    INSIDER_TRANSACTIONS = "INSIDER_TRANSACTIONS"
    OVERVIEW = "OVERVIEW"
    ETF_PROFILE = "ETF_PROFILE"
    DIVIDENDS = "DIVIDENDS"
    SPLITS = "SPLITS"
    INCOME_STATEMENT = "INCOME_STATEMENT"
    BALANCE_SHEET = "BALANCE_SHEET"
    CASH_FLOW = "CASH_FLOW"
    EARNINGS = "EARNINGS"
    LISTING_STATUS = "LISTING_STATUS"
    EARNINGS_CALENDAR = "EARNINGS_CALENDAR"
    IPO_CALENDAR = "IPO_CALENDAR"
    SMA = "SMA"
    EMA = "EMA"
    STOCH = "STOCH"
    RSI = "RSI"
    ADX = "ADX"
    CCI = "CCI"
    AROON = "AROON"
    BBANDS = "BBANDS"
    AD = "AD"
    OBV = "OBV"

class Interval(str, Enum):
    """Time intervals for technical indicators"""
    ONE_MIN = "1min"
    FIVE_MIN = "5min"
    FIFTEEN_MIN = "15min"
    THIRTY_MIN = "30min"
    SIXTY_MIN = "60min"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class SeriesType(str, Enum):
    """Series types for technical indicators"""
    CLOSE = "close"
    OPEN = "open"
    HIGH = "high"
    LOW = "low"

class DataType(str, Enum):
    """Response data types"""
    JSON = "json"
    CSV = "csv"

class SortType(str, Enum):
    """Sort types for news sentiment"""
    LATEST = "LATEST"
    EARLIEST = "EARLIEST"
    RELEVANCE = "RELEVANCE"

class ListingState(str, Enum):
    """Listing status states"""
    ACTIVE = "active"
    DELISTED = "delisted"

class EarningsHorizon(str, Enum):
    """Earnings calendar horizons"""
    THREE_MONTH = "3month"
    SIX_MONTH = "6month"
    TWELVE_MONTH = "12month"

class MAType(int, Enum):
    """Moving average types"""
    SMA = 0
    EMA = 1
    WMA = 2
    DEMA = 3
    TEMA = 4
    TRIMA = 5
    T3 = 6
    KAMA = 7
    MAMA = 8 