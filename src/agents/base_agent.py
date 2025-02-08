from abc import ABC, abstractmethod
import logging
from typing import Dict, List, Optional, Tuple
import yfinance as yf
import pandas as pd

class BaseAgent(ABC):
    def __init__(self, name: str, show_reasoning: bool = False):
        self.name = name
        self.show_reasoning = show_reasoning
        self.logger = logging.getLogger(f"Agent.{name}")
    
    def log_reasoning(self, message: str) -> None:
        """Log agent's reasoning if show_reasoning is enabled."""
        if self.show_reasoning:
            self.logger.info(f"{self.name} reasoning: {message}")
    
    @abstractmethod
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """
        Analyze the given data and return trading signals.
        
        Args:
            symbol: The stock symbol being analyzed
            data: DataFrame containing historical price and volume data
            
        Returns:
            Dict containing:
                - signal: 1 (buy), -1 (sell), 0 (hold)
                - confidence: float between 0 and 1
                - reasoning: str explaining the decision
                - metadata: Dict with additional analysis data
        """
        pass
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical data for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            return data
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise
    
    def get_fundamentals(self, symbol: str) -> Dict:
        """Fetch fundamental data for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('forwardPE'),
                'pb_ratio': info.get('priceToBook'),
                'dividend_yield': info.get('dividendYield'),
                'profit_margins': info.get('profitMargins'),
                'revenue_growth': info.get('revenueGrowth'),
                'debt_to_equity': info.get('debtToEquity'),
                'free_cash_flow': info.get('freeCashflow'),
                'roa': info.get('returnOnAssets'),
                'roe': info.get('returnOnEquity')
            }
        except Exception as e:
            self.logger.error(f"Error fetching fundamentals for {symbol}: {str(e)}")
            raise
    
    def validate_signal(self, signal: Dict) -> bool:
        """Validate the structure and values of a trading signal."""
        required_keys = {'signal', 'confidence', 'reasoning', 'metadata'}
        if not all(key in signal for key in required_keys):
            return False
        
        if signal['signal'] not in [-1, 0, 1]:
            return False
        
        if not (0 <= signal['confidence'] <= 1):
            return False
        
        return True 