from typing import Dict
import pandas as pd
import numpy as np
from .base_agent import BaseAgent

class FundamentalsAgent(BaseAgent):
    def __init__(self, show_reasoning: bool = False):
        super().__init__("Fundamentals Analysis", show_reasoning)
        # Fundamental analysis thresholds
        self.min_current_ratio = 1.5
        self.max_debt_to_equity = 2.0
        self.min_gross_margin = 0.20
        self.min_operating_margin = 0.10
        self.min_net_margin = 0.05
        self.min_roe = 0.12
        self.min_roa = 0.05
        
    def _calculate_growth_rates(self, fundamentals: Dict) -> Dict:
        """Calculate year-over-year growth rates."""
        metrics = {}
        
        if fundamentals.get('revenue_growth'):
            metrics['revenue_growth'] = fundamentals['revenue_growth']
        
        if fundamentals.get('earnings_growth'):
            metrics['earnings_growth'] = fundamentals['earnings_growth']
            
        if fundamentals.get('free_cash_flow_growth'):
            metrics['fcf_growth'] = fundamentals['free_cash_flow_growth']
            
        return metrics
        
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Analyze company fundamentals."""
        fundamentals = self.get_fundamentals(symbol)
        
        # Initialize scoring
        score = 0
        max_score = 8
        reasons = []
        
        # 1. Profitability Margins
        if fundamentals.get('profit_margins', 0) > self.min_net_margin:
            score += 1
            reasons.append(f"Strong net margin at {fundamentals['profit_margins']:.1%}")
        else:
            reasons.append("Weak profitability")
            
        # 2. Return on Equity
        if fundamentals.get('roe', 0) > self.min_roe:
            score += 1
            reasons.append(f"Good ROE at {fundamentals['roe']:.1%}")
        else:
            reasons.append("Poor return on equity")
            
        # 3. Return on Assets
        if fundamentals.get('roa', 0) > self.min_roa:
            score += 1
            reasons.append(f"Efficient asset utilization (ROA: {fundamentals['roa']:.1%})")
        else:
            reasons.append("Inefficient asset utilization")
            
        # 4. Debt Levels
        if fundamentals.get('debt_to_equity', float('inf')) < self.max_debt_to_equity:
            score += 1
            reasons.append(f"Manageable debt levels (D/E: {fundamentals['debt_to_equity']:.2f})")
        else:
            reasons.append("High debt burden")
            
        # 5. Growth Metrics
        growth_rates = self._calculate_growth_rates(fundamentals)
        
        if growth_rates.get('revenue_growth', 0) > 0.05:  # 5% growth threshold
            score += 1
            reasons.append(f"Strong revenue growth at {growth_rates['revenue_growth']:.1%}")
        else:
            reasons.append("Weak revenue growth")
            
        if growth_rates.get('earnings_growth', 0) > 0.10:  # 10% growth threshold
            score += 1
            reasons.append(f"Strong earnings growth at {growth_rates['earnings_growth']:.1%}")
        else:
            reasons.append("Weak earnings growth")
            
        # 6. Cash Flow Analysis
        if fundamentals.get('free_cash_flow', 0) > 0:
            score += 1
            reasons.append("Positive free cash flow")
            
            if growth_rates.get('fcf_growth', 0) > 0:
                score += 1
                reasons.append(f"Growing free cash flow at {growth_rates['fcf_growth']:.1%}")
            else:
                reasons.append("Declining free cash flow")
        else:
            reasons.append("Negative free cash flow")
            
        # Calculate confidence based on data availability and score
        available_metrics = sum(1 for v in [
            fundamentals.get('profit_margins'),
            fundamentals.get('roe'),
            fundamentals.get('roa'),
            fundamentals.get('debt_to_equity'),
            fundamentals.get('free_cash_flow'),
            growth_rates.get('revenue_growth'),
            growth_rates.get('earnings_growth'),
            growth_rates.get('fcf_growth')
        ] if v is not None)
        
        data_confidence = available_metrics / 8  # Normalize by total metrics
        score_confidence = score / max_score
        confidence = (data_confidence + score_confidence) / 2
        
        # Determine signal based on score
        if score / max_score > 0.7:
            signal = 1
            action = "BUY"
        elif score / max_score < 0.4:
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
                'fundamentals': fundamentals,
                'growth_rates': growth_rates,
                'available_metrics': available_metrics
            }
        } 