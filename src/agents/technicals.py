from typing import Dict
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from .base_agent import BaseAgent

class TechnicalsAgent(BaseAgent):
    def __init__(self, show_reasoning: bool = False):
        super().__init__("Technical Analysis", show_reasoning)
        # Technical analysis parameters
        self.short_window = 20
        self.long_window = 50
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bb_period = 20
        self.bb_std = 2
        
    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
        # Make sure we have enough data
        if len(data) < self.long_window:
            raise ValueError(f"Not enough data points. Need at least {self.long_window}")
            
        # Moving averages
        data['SMA_short'] = SMAIndicator(data['Close'], self.short_window).sma_indicator()
        data['SMA_long'] = SMAIndicator(data['Close'], self.long_window).sma_indicator()
        data['EMA_short'] = EMAIndicator(data['Close'], self.short_window).ema_indicator()
        
        # MACD
        macd = MACD(data['Close'], 
                    window_slow=self.macd_slow,
                    window_fast=self.macd_fast,
                    window_sign=self.macd_signal)
        data['MACD'] = macd.macd()
        data['MACD_signal'] = macd.macd_signal()
        
        # RSI
        data['RSI'] = RSIIndicator(data['Close'], self.rsi_period).rsi()
        
        # Stochastic Oscillator
        stoch = StochasticOscillator(data['High'], data['Low'], data['Close'])
        data['Stoch_k'] = stoch.stoch()
        data['Stoch_d'] = stoch.stoch_signal()
        
        # Bollinger Bands
        bb = BollingerBands(data['Close'], self.bb_period, self.bb_std)
        data['BB_upper'] = bb.bollinger_hband()
        data['BB_lower'] = bb.bollinger_lband()
        
        return data
        
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Analyze stock using technical indicators."""
        # Calculate technical indicators
        df = self._calculate_indicators(data.copy())
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Initialize scoring
        score = 0
        max_score = 6
        reasons = []
        
        # 1. Moving Average Crossover
        if current['SMA_short'] > current['SMA_long'] and prev['SMA_short'] <= prev['SMA_long']:
            score += 1
            reasons.append("Bullish SMA crossover")
        elif current['SMA_short'] < current['SMA_long'] and prev['SMA_short'] >= prev['SMA_long']:
            score -= 1
            reasons.append("Bearish SMA crossover")
        else:
            reasons.append("No significant MA signals")
            
        # 2. MACD
        if current['MACD'] > current['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
            score += 1
            reasons.append("Bullish MACD crossover")
        elif current['MACD'] < current['MACD_signal'] and prev['MACD'] >= prev['MACD_signal']:
            score -= 1
            reasons.append("Bearish MACD crossover")
        else:
            reasons.append("No significant MACD signals")
            
        # 3. RSI
        if 30 <= current['RSI'] <= 70:
            score += 1
            reasons.append(f"RSI in neutral zone at {current['RSI']:.1f}")
        elif current['RSI'] < 30:
            score += 1
            reasons.append(f"Oversold RSI at {current['RSI']:.1f}")
        else:
            score -= 1
            reasons.append(f"Overbought RSI at {current['RSI']:.1f}")
            
        # 4. Stochastic
        if current['Stoch_k'] < 20:
            score += 1
            reasons.append("Oversold stochastic")
        elif current['Stoch_k'] > 80:
            score -= 1
            reasons.append("Overbought stochastic")
        else:
            reasons.append("Neutral stochastic")
            
        # 5. Bollinger Bands
        price = current['Close']
        if price < current['BB_lower']:
            score += 1
            reasons.append("Price below lower Bollinger Band")
        elif price > current['BB_upper']:
            score -= 1
            reasons.append("Price above upper Bollinger Band")
        else:
            reasons.append("Price within Bollinger Bands")
            
        # 6. Trend Strength
        price_trend = (current['Close'] - df['Close'].rolling(window=self.short_window).mean().iloc[-1]) / \
                     df['Close'].rolling(window=self.short_window).std().iloc[-1]
        if abs(price_trend) > 1:
            if price_trend > 0:
                score += 1
                reasons.append("Strong upward trend")
            else:
                score -= 1
                reasons.append("Strong downward trend")
        else:
            reasons.append("Weak trend")
            
        # Normalize score to [-1, 1] range
        normalized_score = score / max_score
        
        # Calculate confidence based on indicator agreement
        confidence = abs(normalized_score)
        
        # Determine signal
        if normalized_score > 0.3:
            signal = 1
            action = "BUY"
        elif normalized_score < -0.3:
            signal = -1
            action = "SELL"
        else:
            signal = 0
            action = "HOLD"
            
        reasoning = f"{action} recommendation with {confidence:.1%} confidence. " + " ".join(reasons)
        self.log_reasoning(reasoning)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning,
            'metadata': {
                'score': score,
                'max_score': max_score,
                'indicators': {
                    'rsi': current['RSI'],
                    'macd': current['MACD'],
                    'macd_signal': current['MACD_signal'],
                    'stoch_k': current['Stoch_k'],
                    'stoch_d': current['Stoch_d'],
                    'sma_short': current['SMA_short'],
                    'sma_long': current['SMA_long']
                }
            }
        } 