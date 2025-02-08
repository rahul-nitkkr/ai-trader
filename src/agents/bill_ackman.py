from typing import Dict
import pandas as pd
from .base_agent import BaseAgent

class BillAckmanAgent(BaseAgent):
    def __init__(self, show_reasoning: bool = False):
        super().__init__("Bill Ackman", show_reasoning)
        # Ackman's investment criteria
        self.min_market_cap = 5e9  # $5B minimum market cap
        self.min_daily_volume = 1e6  # Minimum daily volume for liquidity
        self.max_pe_ratio = 20
        self.min_operating_margin = 0.15  # 15% minimum operating margin
        self.min_cash_flow_growth = 0.10  # 10% minimum cash flow growth
        
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Analyze stock using Bill Ackman's investment principles."""
        fundamentals = self.get_fundamentals(symbol)
        
        # Initialize scoring
        score = 0
        max_score = 7
        reasons = []
        
        # Calculate average daily volume
        avg_volume = data['Volume'].mean() if not data.empty else 0
        
        # 1. Size and Liquidity
        if fundamentals['market_cap'] and fundamentals['market_cap'] > self.min_market_cap:
            score += 1
            reasons.append("Sufficient market cap for activist position")
        else:
            reasons.append("Too small for meaningful activist position")
            
        if avg_volume > self.min_daily_volume:
            score += 1
            reasons.append("Adequate trading liquidity")
        else:
            reasons.append("Insufficient trading volume")
            
        # 2. Business Quality
        if fundamentals['profit_margins'] and fundamentals['profit_margins'] > self.min_operating_margin:
            score += 1
            reasons.append(f"Strong operating margins at {fundamentals['profit_margins']:.1%}")
        else:
            reasons.append("Weak operating performance")
            
        # 3. Growth Potential
        if fundamentals['revenue_growth'] and fundamentals['revenue_growth'] > self.min_cash_flow_growth:
            score += 1
            reasons.append(f"Strong revenue growth at {fundamentals['revenue_growth']:.1%}")
        else:
            reasons.append("Insufficient growth")
            
        # 4. Value Creation Potential
        if fundamentals['pe_ratio'] and fundamentals['pe_ratio'] < self.max_pe_ratio:
            score += 1
            reasons.append(f"Reasonable valuation with P/E of {fundamentals['pe_ratio']:.1f}")
        else:
            reasons.append("Expensive valuation")
            
        # 5. Capital Allocation
        if fundamentals['free_cash_flow'] and fundamentals['free_cash_flow'] > 0:
            score += 1
            reasons.append("Positive free cash flow generation")
        else:
            reasons.append("Poor cash flow generation")
            
        # 6. Return on Capital
        if fundamentals['roe'] and fundamentals['roe'] > 0.12:  # 12% ROE threshold
            score += 1
            reasons.append(f"Good return on equity at {fundamentals['roe']:.1%}")
        else:
            reasons.append("Poor capital efficiency")
            
        # Calculate confidence and determine signal
        confidence = score / max_score
        
        # Determine signal based on confidence
        if confidence >= 0.75:  # Strong activist potential
            signal = 1
            action = "BUY"
        elif confidence >= 0.6:  # Potential but needs more analysis
            signal = 0
            action = "HOLD"
        else:  # Not suitable for activist strategy
            signal = -1
            action = "SELL"
            
        reasoning = f"{action} recommendation with {confidence:.1%} confidence. " + " ".join(reasons)
        self.log_reasoning(reasoning)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning,
            'metadata': {
                'score': score,
                'max_score': max_score,
                'fundamentals': fundamentals,
                'avg_volume': avg_volume
            }
        } 