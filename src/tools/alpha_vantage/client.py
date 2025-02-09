import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
import requests

from .models import (
    NewsArticle, NewsSentimentResponse, InsiderTransaction, InsiderTransactionsResponse,
    CompanyOverview, ETFProfile, FinancialStatement, IncomeStatement, BalanceSheet,
    CashFlow, EarningsData, ListingStatus, EarningsCalendarEvent, IPOCalendarEvent
)
from .enums import (
    Function, Interval, SeriesType, DataType, SortType, ListingState,
    EarningsHorizon, MAType
)
from .parsers import parse_insider_transactions

class AlphaVantageClient:
    """Alpha Vantage API Client"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client with API key"""
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set ALPHA_VANTAGE_API_KEY environment variable or pass it directly.")
        
        self.session = requests.Session()
    
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Alpha Vantage API"""
        params["apikey"] = self.api_key
        response = self.session.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.json(), response.status_code
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol"""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol
        }
        response, _ = self._make_request(params)
        quote_data = response.get("Global Quote", {})
        return {
            "price": quote_data.get("05. price", "0"),
            "volume": quote_data.get("06. volume", "0"),
            "change": quote_data.get("09. change", "0"),
            "change_percent": quote_data.get("10. change percent", "0%"),
            "timestamp": quote_data.get("07. latest trading day", "")
        }
    
    def get_news_sentiment(
        self,
        tickers: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        time_from: Optional[datetime] = None,
        time_to: Optional[datetime] = None,
        sort: Optional[SortType] = None,
        limit: int = 50
    ) -> NewsSentimentResponse:
        """Get news and sentiment data"""
        params = {"function": Function.NEWS_SENTIMENT}
        
        if tickers:
            params["tickers"] = ",".join(tickers)
        if topics:
            params["topics"] = ",".join(topics)
        if time_from:
            params["time_from"] = time_from.strftime("%Y%m%dT%H%M")
        if time_to:
            params["time_to"] = time_to.strftime("%Y%m%dT%H%M")
        if sort:
            params["sort"] = sort.value
        if limit:
            params["limit"] = str(limit)
            
        response, status_code = self._make_request(params)
        return response  # TODO: Add parser for news sentiment
    
    def get_insider_transactions(self, symbol: str) -> InsiderTransactionsResponse:
        """Get insider transactions for a symbol"""
        params = {
            "function": Function.INSIDER_TRANSACTIONS,
            "symbol": symbol
        }
        response, status_code = self._make_request(params)
        return parse_insider_transactions(response, status_code)
    
    def get_company_overview(self, symbol: str) -> CompanyOverview:
        """Get company overview"""
        params = {
            "function": Function.OVERVIEW,
            "symbol": symbol
        }
        response, status_code = self._make_request(params)
        return response  # TODO: Add parser for company overview
    
    def get_etf_profile(self, symbol: str) -> ETFProfile:
        """Get ETF profile and holdings"""
        params = {
            "function": Function.ETF_PROFILE,
            "symbol": symbol
        }
        response, status_code = self._make_request(params)
        return response  # TODO: Add parser for ETF profile
    
    def get_income_statement(self, symbol: str) -> List[IncomeStatement]:
        """Get income statement data"""
        params = {
            "function": Function.INCOME_STATEMENT,
            "symbol": symbol
        }
        response, status_code = self._make_request(params)
        return response  # TODO: Add parser for income statement
    
    def get_balance_sheet(self, symbol: str) -> List[BalanceSheet]:
        """Get balance sheet data"""
        params = {
            "function": Function.BALANCE_SHEET,
            "symbol": symbol
        }
        response, status_code = self._make_request(params)
        return response  # TODO: Add parser for balance sheet
    
    def get_cash_flow(self, symbol: str) -> List[CashFlow]:
        """Get cash flow data"""
        params = {
            "function": Function.CASH_FLOW,
            "symbol": symbol
        }
        response, status_code = self._make_request(params)
        return response  # TODO: Add parser for cash flow
    
    def get_earnings(self, symbol: str) -> List[EarningsData]:
        """Get earnings data"""
        params = {
            "function": Function.EARNINGS,
            "symbol": symbol
        }
        response, status_code = self._make_request(params)
        return response  # TODO: Add parser for earnings
    
    def get_listing_status(
        self,
        date: Optional[datetime] = None,
        state: Optional[ListingState] = None
    ) -> List[ListingStatus]:
        """Get listing status"""
        params = {"function": Function.LISTING_STATUS}
        
        if date:
            params["date"] = date.strftime("%Y-%m-%d")
        if state:
            params["state"] = state.value
            
        response, status_code = self._make_request(params)
        return response  # TODO: Add parser for listing status
    
    def get_earnings_calendar(
        self,
        symbol: Optional[str] = None,
        horizon: Optional[EarningsHorizon] = None
    ) -> List[EarningsCalendarEvent]:
        """Get earnings calendar"""
        params = {"function": Function.EARNINGS_CALENDAR}
        
        if symbol:
            params["symbol"] = symbol
        if horizon:
            params["horizon"] = horizon.value
            
        response, status_code = self._make_request(params)
        return response  # TODO: Add parser for earnings calendar
    
    def get_ipo_calendar(self) -> List[IPOCalendarEvent]:
        """Get IPO calendar"""
        params = {"function": Function.IPO_CALENDAR}
        response, status_code = self._make_request(params)
        return response  # TODO: Add parser for IPO calendar
    
    def get_technical_indicator(
        self,
        function: Function,
        symbol: str,
        interval: Interval,
        time_period: Optional[int] = None,
        series_type: Optional[SeriesType] = None,
        fastk_period: Optional[int] = None,
        slowk_period: Optional[int] = None,
        slowd_period: Optional[int] = None,
        slowk_matype: Optional[MAType] = None,
        slowd_matype: Optional[MAType] = None,
        fastperiod: Optional[int] = None,
        slowperiod: Optional[int] = None,
        signalperiod: Optional[int] = None,
        datatype: DataType = DataType.JSON
    ) -> Dict[str, Any]:
        """Get technical indicator data"""
        params = {
            "function": function,
            "symbol": symbol,
            "interval": interval.value,
            "datatype": datatype.value
        }
        
        if time_period:
            params["time_period"] = str(time_period)
        if series_type:
            params["series_type"] = series_type.value
        if fastk_period:
            params["fastk_period"] = str(fastk_period)
        if slowk_period:
            params["slowk_period"] = str(slowk_period)
        if slowd_period:
            params["slowd_period"] = str(slowd_period)
        if slowk_matype:
            params["slowk_matype"] = str(slowk_matype.value)
        if slowd_matype:
            params["slowd_matype"] = str(slowd_matype.value)
        if fastperiod:
            params["fastperiod"] = str(fastperiod)
        if slowperiod:
            params["slowperiod"] = str(slowperiod)
        if signalperiod:
            params["signalperiod"] = str(signalperiod)
            
        response, status_code = self._make_request(params)
        return response  # TODO: Add parser for technical indicators 