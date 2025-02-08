from typing import Dict
import pandas as pd
from .base_agent import BaseAgent

class WarrenBuffettAgent(BaseAgent):
    def __init__(self, show_reasoning: bool = False):
        super().__init__("Warren Buffett", show_reasoning)
        # Buffett's criteria thresholds
        self.min_market_cap = 1e9  # $1B minimum market cap
        self.max_pe_ratio = 15
        self.min_roe = 0.15  # 15% minimum return on equity
        self.min_profit_margin = 0.10  # 10% minimum profit margin
        self.max_debt_to_equity = 0.5  # Conservative debt level
        
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Analyze stock using Warren Buffett's investment principles."""
        fundamentals = self.get_fundamentals(symbol)
        
        # Initialize scoring
        score = 0
        max_score = 6
        reasons = []
        
        # 1. Business Understanding & Competitive Advantage
        if fundamentals['profit_margins'] and fundamentals['profit_margins'] > self.min_profit_margin:
            score += 1
            reasons.append(f"Strong profit margins at {fundamentals['profit_margins']:.1%}")
        else:
            reasons.append("Insufficient profit margins")
            
        # 2. Management Quality (ROE as a proxy)
        if fundamentals['roe'] and fundamentals['roe'] > self.min_roe:
            score += 1
            reasons.append(f"Good management indicated by ROE of {fundamentals['roe']:.1%}")
        else:
            reasons.append("Suboptimal return on equity")
            
        # 3. Financial Health
        if fundamentals['debt_to_equity'] and fundamentals['debt_to_equity'] < self.max_debt_to_equity:
            score += 1
            reasons.append("Conservative debt levels")
        else:
            reasons.append("High debt levels")
            
        # 4. Value (P/E Ratio)
        if fundamentals['pe_ratio'] and fundamentals['pe_ratio'] < self.max_pe_ratio:
            score += 1
            reasons.append(f"Attractive P/E ratio of {fundamentals['pe_ratio']:.1f}")
        else:
            reasons.append("Expensive valuation")
            
        # 5. Market Position
        if fundamentals['market_cap'] and fundamentals['market_cap'] > self.min_market_cap:
            score += 1
            reasons.append("Strong market position")
        else:
            reasons.append("Insufficient market presence")
            
        # 6. Growth and Cash Flow
        if fundamentals['free_cash_flow'] and fundamentals['free_cash_flow'] > 0:
            score += 1
            reasons.append("Positive free cash flow")
        else:
            reasons.append("Poor cash flow generation")
            
        # Calculate confidence and determine signal
        confidence = score / max_score
        
        # Determine signal based on confidence
        if confidence >= 0.8:  # Strong buy
            signal = 1
            action = "BUY"
        elif confidence >= 0.6:  # Hold/mild buy
            signal = 0
            action = "HOLD"
        else:  # Avoid/sell
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
                'fundamentals': fundamentals
            }
        } 