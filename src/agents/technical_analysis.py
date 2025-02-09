from typing import Dict
import pandas as pd
import numpy as np
from datetime import datetime
from .base_agent import BaseAgent
from src.tools.alpha_vantage.client import AlphaVantageClient
from src.tools.alpha_vantage.enums import Function, Interval, SeriesType, MAType

class TechnicalAnalysisAgent(BaseAgent):
    def __init__(self, show_reasoning: bool = False):
        super().__init__("Technical Analysis", show_reasoning)
        # Initialize Alpha Vantage client
        self.alpha_vantage = AlphaVantageClient()
        
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get historical price data and technical indicators."""
        try:
            # Get historical price data
            price_data = self.alpha_vantage.get_technical_indicator(
                function=Function.TIME_SERIES_DAILY,
                symbol=symbol,
                interval=Interval.DAILY
            )
            
            # Create DataFrame with price data
            if 'Time Series (Daily)' in price_data:
                df = pd.DataFrame.from_dict(price_data['Time Series (Daily)'], orient='index')
                df.index = pd.to_datetime(df.index)
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                df = df.astype(float)
                
                # Filter by date range
                df = df[start_date:end_date]
                
                if df.empty:
                    self.logger.error(f"No price data found for {symbol} in date range")
                    return pd.DataFrame()
                
                # Get RSI
                rsi_data = self.alpha_vantage.get_technical_indicator(
                    function=Function.RSI,
                    symbol=symbol,
                    interval=Interval.DAILY,
                    time_period=14,
                    series_type=SeriesType.CLOSE
                )
                
                # Get MACD
                macd_data = self.alpha_vantage.get_technical_indicator(
                    function=Function.MACD,
                    symbol=symbol,
                    interval=Interval.DAILY,
                    series_type=SeriesType.CLOSE,
                    fastperiod=12,
                    slowperiod=26,
                    signalperiod=9
                )
                
                # Get SMA 50
                sma50_data = self.alpha_vantage.get_technical_indicator(
                    function=Function.SMA,
                    symbol=symbol,
                    interval=Interval.DAILY,
                    time_period=50,
                    series_type=SeriesType.CLOSE
                )
                
                # Get SMA 200
                sma200_data = self.alpha_vantage.get_technical_indicator(
                    function=Function.SMA,
                    symbol=symbol,
                    interval=Interval.DAILY,
                    time_period=200,
                    series_type=SeriesType.CLOSE
                )
                
                # Add RSI
                if 'Technical Analysis: RSI' in rsi_data:
                    rsi_series = pd.Series({
                        k: float(v['RSI'])
                        for k, v in rsi_data['Technical Analysis: RSI'].items()
                    })
                    rsi_series.index = pd.to_datetime(rsi_series.index)
                    df['RSI'] = rsi_series
                
                # Add MACD
                if 'Technical Analysis: MACD' in macd_data:
                    macd_series = pd.Series({
                        k: float(v['MACD'])
                        for k, v in macd_data['Technical Analysis: MACD'].items()
                    })
                    macd_signal_series = pd.Series({
                        k: float(v['MACD_Signal'])
                        for k, v in macd_data['Technical Analysis: MACD'].items()
                    })
                    macd_series.index = pd.to_datetime(macd_series.index)
                    macd_signal_series.index = pd.to_datetime(macd_signal_series.index)
                    df['MACD'] = macd_series
                    df['MACD_Signal'] = macd_signal_series
                
                # Add SMAs
                if 'Technical Analysis: SMA' in sma50_data:
                    sma50_series = pd.Series({
                        k: float(v['SMA'])
                        for k, v in sma50_data['Technical Analysis: SMA'].items()
                    })
                    sma50_series.index = pd.to_datetime(sma50_series.index)
                    df['SMA_50'] = sma50_series
                
                if 'Technical Analysis: SMA' in sma200_data:
                    sma200_series = pd.Series({
                        k: float(v['SMA'])
                        for k, v in sma200_data['Technical Analysis: SMA'].items()
                    })
                    sma200_series.index = pd.to_datetime(sma200_series.index)
                    df['SMA_200'] = sma200_series
                
                return df
            else:
                self.logger.error(f"Invalid price data format for {symbol}")
                return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error fetching technical data for {symbol}: {str(e)}")
            return pd.DataFrame()
        
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Analyze stock using technical indicators."""
        if data.empty:
            raise ValueError(f"No data provided for {symbol}")
        
        # Generate signals based on indicators
        signal, confidence, reasoning = self._generate_signals(data)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning,
            'metadata': {
                'rsi': data['RSI'].iloc[-1] if 'RSI' in data else None,
                'macd': data['MACD'].iloc[-1] if 'MACD' in data else None,
                'macd_signal': data['MACD_Signal'].iloc[-1] if 'MACD_Signal' in data else None,
                'sma_50': data['SMA_50'].iloc[-1] if 'SMA_50' in data else None,
                'sma_200': data['SMA_200'].iloc[-1] if 'SMA_200' in data else None
            }
        }
        
    def _generate_signals(self, data: pd.DataFrame) -> tuple[int, float, str]:
        """Generate trading signals based on technical indicators."""
        current_price = data['Close'].iloc[-1]
        rsi = data['RSI'].iloc[-1]
        macd = data['MACD'].iloc[-1]
        macd_signal = data['MACD_Signal'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1]
        sma_200 = data['SMA_200'].iloc[-1]
        
        signals = []
        confidences = []
        reasons = []
        
        # RSI signals
        if rsi < 30:
            signals.append(1)
            confidences.append(0.7)
            reasons.append(f"RSI is oversold at {rsi:.1f}")
        elif rsi > 70:
            signals.append(-1)
            confidences.append(0.7)
            reasons.append(f"RSI is overbought at {rsi:.1f}")
            
        # MACD signals
        if macd > macd_signal:
            signals.append(1)
            confidences.append(0.6)
            reasons.append("MACD crossed above signal line")
        elif macd < macd_signal:
            signals.append(-1)
            confidences.append(0.6)
            reasons.append("MACD crossed below signal line")
            
        # Moving Average signals
        if current_price > sma_50 > sma_200:
            signals.append(1)
            confidences.append(0.5)
            reasons.append("Price above both moving averages in bullish alignment")
        elif current_price < sma_50 < sma_200:
            signals.append(-1)
            confidences.append(0.5)
            reasons.append("Price below both moving averages in bearish alignment")
            
        if not signals:
            return 0, 0.5, "No clear technical signals"
            
        # Aggregate signals
        final_signal = np.sign(sum(signals))
        avg_confidence = sum(confidences) / len(confidences)
        reasoning = " | ".join(reasons)
        
        return final_signal, avg_confidence, reasoning
        
    def screen_stocks(self, criteria: Dict) -> list:
        """Screen stocks based on technical criteria."""
        # This would typically query a database of stocks
        # and filter based on the technical criteria
        # For now, return empty list as it's not implemented
        return [] 