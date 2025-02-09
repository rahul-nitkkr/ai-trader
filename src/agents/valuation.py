from typing import Dict
import pandas as pd
import numpy as np
from datetime import datetime
from .base_agent import BaseAgent
from src.tools.alpha_vantage.client import AlphaVantageClient

class ValuationAgent(BaseAgent):
    def __init__(self, show_reasoning: bool = False):
        super().__init__("Valuation Analysis", show_reasoning)
        # Initialize Alpha Vantage client
        self.alpha_vantage = AlphaVantageClient()
        # Valuation parameters
        self.required_return = float(0.10)  # 10% required return
        self.perpetual_growth = float(0.03)  # 3% perpetual growth rate
        self.margin_of_safety = float(0.20)  # 20% margin of safety
        
    def get_fundamentals(self, symbol: str) -> Dict:
        """Get fundamental data from Alpha Vantage."""
        try:
            # Get company overview
            overview = self.alpha_vantage.get_company_overview(symbol)
            
            # Get income statement
            income_stmt = self.alpha_vantage.get_income_statement(symbol)
            latest_income = income_stmt[0] if income_stmt else {}
            
            # Get balance sheet
            balance_sheet = self.alpha_vantage.get_balance_sheet(symbol)
            latest_balance = balance_sheet[0] if balance_sheet else {}
            
            # Get cash flow
            cash_flow = self.alpha_vantage.get_cash_flow(symbol)
            latest_cash_flow = cash_flow[0] if cash_flow else {}
            
            # Calculate free cash flow growth if we have multiple periods
            fcf_growth = 0
            if len(cash_flow) >= 2:
                current_fcf = float(latest_cash_flow.get('operatingCashflow', 0)) - float(latest_cash_flow.get('capitalExpenditures', 0))
                prev_fcf = float(cash_flow[1].get('operatingCashflow', 0)) - float(cash_flow[1].get('capitalExpenditures', 0))
                if prev_fcf > 0:
                    fcf_growth = (current_fcf - prev_fcf) / prev_fcf
            
            # Calculate EBITDA
            ebitda = float(latest_income.get('ebitda', 0))
            enterprise_value = float(overview.get('MarketCapitalization', 0)) + float(latest_balance.get('totalDebt', 0)) - float(latest_balance.get('cashAndShortTermInvestments', 0))
            
            return {
                # Overview metrics
                'market_cap': float(overview.get('MarketCapitalization', 0)),
                'pe_ratio': float(overview.get('PERatio', 0)),
                'peg_ratio': float(overview.get('PEGRatio', 0)),
                'pb_ratio': float(overview.get('PriceToBookRatio', 0)),
                
                # Calculated metrics
                'ev_to_ebitda': enterprise_value / ebitda if ebitda > 0 else 0,
                'free_cash_flow': float(latest_cash_flow.get('operatingCashflow', 0)) - float(latest_cash_flow.get('capitalExpenditures', 0)),
                'free_cash_flow_growth': fcf_growth
            }
        except Exception as e:
            self.logger.error(f"Error fetching fundamentals for {symbol}: {str(e)}")
            return {}
        
    def _calculate_dcf_value(self, fundamentals: Dict) -> float:
        """Calculate Discounted Cash Flow value."""
        try:
            fcf = fundamentals.get('free_cash_flow', 0)
            if fcf <= 0:
                return 0
                
            growth_rate = fundamentals.get('free_cash_flow_growth', 0.05)
            growth_rate = min(max(growth_rate, 0), 0.15)  # Cap growth between 0% and 15%
            
            # Project cash flows for 5 years
            projected_fcf = []
            current_fcf = fcf
            for _ in range(5):
                current_fcf *= (1 + growth_rate)
                projected_fcf.append(current_fcf)
            
            # Terminal value using perpetual growth
            terminal_value = projected_fcf[-1] * (1 + self.perpetual_growth) / \
                           (self.required_return - self.perpetual_growth)
            
            # Discount all cash flows
            present_value = 0
            for i, cf in enumerate(projected_fcf):
                present_value += cf / ((1 + self.required_return) ** (i + 1))
            
            # Add discounted terminal value
            present_value += terminal_value / ((1 + self.required_return) ** 5)
            
            return present_value
            
        except Exception as e:
            self.logger.error(f"Error calculating DCF value: {str(e)}")
            return 0
            
    def _calculate_relative_value(self, fundamentals: Dict, current_price: float) -> Dict:
        """Calculate relative valuation metrics."""
        metrics = {}
        
        # P/E ratio analysis
        if fundamentals.get('pe_ratio'):
            metrics['pe_ratio'] = fundamentals['pe_ratio']
            metrics['pe_percentile'] = self._calculate_percentile(fundamentals['pe_ratio'], 
                                                               [10, 15, 20, 25, 30])
            
        # P/B ratio analysis
        if fundamentals.get('pb_ratio'):
            metrics['pb_ratio'] = fundamentals['pb_ratio']
            metrics['pb_percentile'] = self._calculate_percentile(fundamentals['pb_ratio'],
                                                               [1, 2, 3, 4, 5])
            
        # EV/EBITDA analysis
        if fundamentals.get('ev_to_ebitda'):
            metrics['ev_to_ebitda'] = fundamentals['ev_to_ebitda']
            metrics['ev_ebitda_percentile'] = self._calculate_percentile(fundamentals['ev_to_ebitda'],
                                                                      [5, 8, 12, 15, 18])
            
        return metrics
        
    def _calculate_percentile(self, value: float, ranges: list) -> float:
        """Calculate percentile based on typical ranges."""
        if value <= ranges[0]:
            return 0.0
        elif value >= ranges[-1]:
            return 1.0
            
        for i in range(len(ranges) - 1):
            if ranges[i] <= value <= ranges[i + 1]:
                return (i + (value - ranges[i]) / (ranges[i + 1] - ranges[i])) / (len(ranges) - 1)
                
        return 0.5
        
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Analyze stock valuation using multiple methods."""
        if data.empty:
            raise ValueError(f"No price data available for {symbol}")
            
        current_price = data.iloc[-1]['Close']
        fundamentals = self.get_fundamentals(symbol)
        
        # Initialize scoring
        score = 0
        max_score = 5
        reasons = []
        
        # 1. DCF Valuation
        dcf_value = self._calculate_dcf_value(fundamentals)
        if dcf_value > 0:
            dcf_upside = (dcf_value / current_price - 1)
            if dcf_upside > self.margin_of_safety:
                score += 1
                reasons.append(f"DCF indicates {dcf_upside:.1%} upside")
            elif dcf_upside < -self.margin_of_safety:
                score -= 1
                reasons.append(f"DCF indicates {-dcf_upside:.1%} downside")
            else:
                reasons.append("DCF indicates fair value")
        else:
            reasons.append("Unable to calculate DCF value")
            
        # 2. Relative Valuation
        relative_metrics = self._calculate_relative_value(fundamentals, current_price)
        
        # P/E Analysis
        if 'pe_ratio' in relative_metrics:
            pe_score = 1 - relative_metrics['pe_percentile']
            if pe_score > 0.7:
                score += 1
                reasons.append(f"Attractive P/E ratio of {relative_metrics['pe_ratio']:.1f}")
            elif pe_score < 0.3:
                score -= 1
                reasons.append(f"Expensive P/E ratio of {relative_metrics['pe_ratio']:.1f}")
            else:
                reasons.append(f"Average P/E ratio of {relative_metrics['pe_ratio']:.1f}")
                
        # P/B Analysis
        if 'pb_ratio' in relative_metrics:
            pb_score = 1 - relative_metrics['pb_percentile']
            if pb_score > 0.7:
                score += 1
                reasons.append(f"Attractive P/B ratio of {relative_metrics['pb_ratio']:.1f}")
            elif pb_score < 0.3:
                score -= 1
                reasons.append(f"Expensive P/B ratio of {relative_metrics['pb_ratio']:.1f}")
            else:
                reasons.append(f"Average P/B ratio of {relative_metrics['pb_ratio']:.1f}")
                
        # EV/EBITDA Analysis
        if 'ev_to_ebitda' in relative_metrics:
            ev_ebitda_score = 1 - relative_metrics['ev_ebitda_percentile']
            if ev_ebitda_score > 0.7:
                score += 1
                reasons.append(f"Attractive EV/EBITDA of {relative_metrics['ev_to_ebitda']:.1f}")
            elif ev_ebitda_score < 0.3:
                score -= 1
                reasons.append(f"Expensive EV/EBITDA of {relative_metrics['ev_to_ebitda']:.1f}")
            else:
                reasons.append(f"Average EV/EBITDA of {relative_metrics['ev_to_ebitda']:.1f}")
                
        # 3. Growth vs. Value
        if fundamentals.get('peg_ratio'):
            if fundamentals['peg_ratio'] < 1:
                score += 1
                reasons.append(f"Growth exceeds valuation (PEG: {fundamentals['peg_ratio']:.1f})")
            elif fundamentals['peg_ratio'] > 2:
                score -= 1
                reasons.append(f"Expensive relative to growth (PEG: {fundamentals['peg_ratio']:.1f})")
            else:
                reasons.append(f"Fair value relative to growth (PEG: {fundamentals['peg_ratio']:.1f})")
                
        # Calculate confidence based on available metrics
        available_metrics = sum(1 for _ in [
            dcf_value > 0,
            'pe_ratio' in relative_metrics,
            'pb_ratio' in relative_metrics,
            'ev_to_ebitda' in relative_metrics,
            fundamentals.get('peg_ratio')
        ] if _)
        
        data_confidence = available_metrics / 5  # Normalize by total metrics
        score_confidence = abs(score) / max_score
        confidence = (data_confidence + score_confidence) / 2
        
        # Determine signal based on score
        normalized_score = score / max_score
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
                'dcf_value': dcf_value,
                'relative_metrics': relative_metrics,
                'current_price': current_price
            }
        } 