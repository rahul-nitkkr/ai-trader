from typing import Dict, Tuple
import pandas as pd
import numpy as np
from .base_agent import BaseAgent

class PriceTargetAgent(BaseAgent):
    def __init__(self, show_reasoning: bool = False):
        super().__init__("Price Target Analysis", show_reasoning)
        # Price target parameters
        self.support_window = 20  # Days to look for support/resistance
        self.volatility_window = 20  # Days for volatility calculation
        self.margin_of_safety = 0.20  # 20% margin of safety for value-based targets
        self.profit_target = 0.30  # 30% profit target
        self.stop_loss = 0.15  # 15% stop loss
        
    def _calculate_support_resistance(self, data: pd.DataFrame) -> Tuple[float, float]:
        """Calculate support and resistance levels using recent price action."""
        recent_data = data.tail(self.support_window)
        
        # Find local minima and maxima
        highs = recent_data['High'].values
        lows = recent_data['Low'].values
        
        # Use rolling windows to identify support/resistance zones
        resistance_levels = []
        support_levels = []
        
        for i in range(2, len(recent_data) - 2):
            # Resistance: local high with lower highs on both sides
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and 
                highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                resistance_levels.append(highs[i])
            
            # Support: local low with higher lows on both sides
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and 
                lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                support_levels.append(lows[i])
        
        # Calculate weighted average of levels, giving more weight to recent ones
        if resistance_levels:
            resistance = np.average(resistance_levels, 
                                  weights=range(1, len(resistance_levels) + 1))
        else:
            resistance = recent_data['High'].max()
            
        if support_levels:
            support = np.average(support_levels,
                               weights=range(1, len(support_levels) + 1))
        else:
            support = recent_data['Low'].min()
            
        return support, resistance
        
    def _calculate_value_targets(self, symbol: str, current_price: float) -> Tuple[float, float]:
        """Calculate price targets based on fundamental value."""
        fundamentals = self.get_fundamentals(symbol)
        
        # Get valuation metrics
        pe_ratio = fundamentals.get('pe_ratio', 20)  # Default to market average
        pb_ratio = fundamentals.get('pb_ratio', 2)
        ev_to_ebitda = fundamentals.get('ev_to_ebitda', 12)
        
        # Calculate target prices using different methods
        targets = []
        
        # 1. P/E based target
        if fundamentals.get('earnings_per_share'):
            pe_target = fundamentals['earnings_per_share'] * min(pe_ratio * 1.2, 25)
            targets.append(pe_target)
        
        # 2. P/B based target
        if fundamentals.get('book_value_per_share'):
            pb_target = fundamentals['book_value_per_share'] * min(pb_ratio * 1.2, 3)
            targets.append(pb_target)
        
        # 3. EV/EBITDA based target
        if fundamentals.get('ebitda_per_share'):
            ev_target = fundamentals['ebitda_per_share'] * min(ev_to_ebitda * 1.2, 15)
            targets.append(ev_target)
        
        if targets:
            # Use median to avoid outliers
            value_target = np.median(targets)
            # Add margin of safety for entry
            entry_target = value_target * (1 - self.margin_of_safety)
            # Add profit target for exit
            exit_target = value_target * (1 + self.profit_target)
            
            return entry_target, exit_target
        else:
            # If no fundamental data, use technical levels
            return current_price * 0.8, current_price * 1.3
        
    def _calculate_volatility_bands(self, data: pd.DataFrame) -> Tuple[float, float]:
        """Calculate price targets based on volatility."""
        recent_data = data.tail(self.volatility_window)
        returns = recent_data['Close'].pct_change().dropna()
        
        # Calculate volatility
        daily_volatility = returns.std()
        annual_volatility = daily_volatility * np.sqrt(252)
        
        current_price = data.iloc[-1]['Close']
        lower_band = current_price * (1 - annual_volatility)
        upper_band = current_price * (1 + annual_volatility)
        
        return lower_band, upper_band
        
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Calculate recommended entry and exit prices."""
        if data.empty:
            raise ValueError(f"No price data available for {symbol}")
            
        current_price = data.iloc[-1]['Close']
        
        # Get different price targets
        support, resistance = self._calculate_support_resistance(data)
        value_entry, value_exit = self._calculate_value_targets(symbol, current_price)
        vol_entry, vol_exit = self._calculate_volatility_bands(data)
        
        # Combine targets (weighted average)
        weights = {
            'technical': 0.3,
            'value': 0.5,
            'volatility': 0.2
        }
        
        entry_targets = {
            'technical': support,
            'value': value_entry,
            'volatility': vol_entry
        }
        
        exit_targets = {
            'technical': resistance,
            'value': value_exit,
            'volatility': vol_exit
        }
        
        # Calculate weighted average targets
        entry_price = sum(price * weights[method] 
                         for method, price in entry_targets.items())
        exit_price = sum(price * weights[method] 
                        for method, price in exit_targets.items())
        
        # Calculate stop loss
        stop_loss_price = entry_price * (1 - self.stop_loss)
        
        # Determine if current price is within buy/sell range
        if current_price <= entry_price:
            signal = 1
            action = "BUY"
            price_target = exit_price
        elif current_price >= exit_price:
            signal = -1
            action = "SELL"
            price_target = entry_price
        else:
            signal = 0
            action = "HOLD"
            price_target = exit_price if current_price > entry_price else entry_price
        
        # Calculate confidence based on price distances
        price_range = exit_price - entry_price
        if price_range > 0:
            if signal == 1:
                confidence = min((entry_price - current_price) / price_range + 0.5, 1.0)
            elif signal == -1:
                confidence = min((current_price - exit_price) / price_range + 0.5, 1.0)
            else:
                confidence = 0.5
        else:
            confidence = 0.5
            
        # Prepare reasoning
        reasons = [
            f"Current price: ${current_price:.2f}",
            f"Entry target: ${entry_price:.2f} (Support: ${support:.2f}, Value: ${value_entry:.2f}, Vol: ${vol_entry:.2f})",
            f"Exit target: ${exit_price:.2f} (Resistance: ${resistance:.2f}, Value: ${value_exit:.2f}, Vol: ${vol_exit:.2f})",
            f"Stop loss: ${stop_loss_price:.2f}"
        ]
        
        if signal == 1:
            reasons.append(f"Potential upside: {((exit_price/current_price - 1) * 100):.1f}%")
        elif signal == -1:
            reasons.append(f"Potential downside: {((entry_price/current_price - 1) * 100):.1f}%")
            
        reasoning = f"{action} recommendation with {confidence:.1%} confidence. " + " ".join(reasons)
        self.log_reasoning(reasoning)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning,
            'metadata': {
                'current_price': current_price,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'stop_loss': stop_loss_price,
                'targets': {
                    'technical': {'entry': support, 'exit': resistance},
                    'value': {'entry': value_entry, 'exit': value_exit},
                    'volatility': {'entry': vol_entry, 'exit': vol_exit}
                }
            }
        } 