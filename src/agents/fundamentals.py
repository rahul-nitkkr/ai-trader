from typing import Dict, List
import pandas as pd
import numpy as np
from datetime import datetime
from .base_agent import BaseAgent
from src.tools.alpha_vantage.client import AlphaVantageClient

class FundamentalsAgent(BaseAgent):
    def __init__(self, show_reasoning: bool = False):
        super().__init__("Fundamentals Analysis", show_reasoning)
        # Initialize Alpha Vantage client
        self.alpha_vantage = AlphaVantageClient()
        # Fundamental analysis thresholds
        self.min_current_ratio = 1.5
        self.max_debt_to_equity = 2.0
        self.min_gross_margin = 0.20
        self.min_operating_margin = 0.10
        self.min_net_margin = 0.05
        self.min_roe = 0.12
        self.min_roa = 0.05
        
    def get_fundamentals(self, symbol: str) -> Dict:
        """Get fundamental data from Alpha Vantage."""
        try:
            # Get company overview
            overview = self.alpha_vantage.get_company_overview(symbol)
            if not isinstance(overview, dict):
                self.logger.error(f"Invalid overview data format for {symbol}")
                return {}
            
            # Get income statement
            income_stmt = self.alpha_vantage.get_income_statement(symbol)
            if not isinstance(income_stmt, list) or not income_stmt:
                self.logger.error(f"Invalid income statement data format for {symbol}")
                return {}
            latest_income = income_stmt[0]
            
            # Get balance sheet
            balance_sheet = self.alpha_vantage.get_balance_sheet(symbol)
            if not isinstance(balance_sheet, list) or not balance_sheet:
                self.logger.error(f"Invalid balance sheet data format for {symbol}")
                return {}
            latest_balance = balance_sheet[0]
            
            # Get cash flow
            cash_flow = self.alpha_vantage.get_cash_flow(symbol)
            if not isinstance(cash_flow, list) or not cash_flow:
                self.logger.error(f"Invalid cash flow data format for {symbol}")
                return {}
            latest_cash_flow = cash_flow[0]
            
            # Calculate growth rates if we have multiple periods
            revenue_growth = 0
            earnings_growth = 0
            fcf_growth = 0
            
            if len(income_stmt) >= 2:
                try:
                    current_revenue = float(latest_income.get('totalRevenue', 0))
                    prev_revenue = float(income_stmt[1].get('totalRevenue', 0))
                    if prev_revenue > 0:
                        revenue_growth = (current_revenue - prev_revenue) / prev_revenue
                    
                    current_earnings = float(latest_income.get('netIncome', 0))
                    prev_earnings = float(income_stmt[1].get('netIncome', 0))
                    if prev_earnings > 0:
                        earnings_growth = (current_earnings - prev_earnings) / prev_earnings
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Error calculating growth rates: {str(e)}")
            
            if len(cash_flow) >= 2:
                try:
                    current_fcf = float(latest_cash_flow.get('operatingCashflow', 0)) - float(latest_cash_flow.get('capitalExpenditures', 0))
                    prev_fcf = float(cash_flow[1].get('operatingCashflow', 0)) - float(cash_flow[1].get('capitalExpenditures', 0))
                    if prev_fcf > 0:
                        fcf_growth = (current_fcf - prev_fcf) / prev_fcf
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Error calculating FCF growth: {str(e)}")
            
            # Helper function to safely convert to float
            def safe_float(value, default=0.0):
                try:
                    return float(value) if value is not None else default
                except (ValueError, TypeError):
                    return default
            
            return {
                # Overview metrics
                'market_cap': safe_float(overview.get('MarketCapitalization')),
                'pe_ratio': safe_float(overview.get('PERatio')),
                'peg_ratio': safe_float(overview.get('PEGRatio')),
                'profit_margins': safe_float(overview.get('ProfitMargin')),
                'operating_margin': safe_float(overview.get('OperatingMarginTTM')),
                'roa': safe_float(overview.get('ReturnOnAssetsTTM')),
                'roe': safe_float(overview.get('ReturnOnEquityTTM')),
                'revenue_ttm': safe_float(overview.get('RevenueTTM')),
                'gross_profit_ttm': safe_float(overview.get('GrossProfitTTM')),
                
                # Balance sheet metrics
                'current_ratio': safe_float(latest_balance.get('currentRatio')),
                'debt_to_equity': safe_float(latest_balance.get('totalDebt')) / safe_float(latest_balance.get('totalShareholderEquity'), 1),
                'total_assets': safe_float(latest_balance.get('totalAssets')),
                'total_debt': safe_float(latest_balance.get('totalDebt')),
                
                # Income statement metrics
                'revenue': safe_float(latest_income.get('totalRevenue')),
                'gross_profit': safe_float(latest_income.get('grossProfit')),
                'operating_income': safe_float(latest_income.get('operatingIncome')),
                'net_income': safe_float(latest_income.get('netIncome')),
                
                # Cash flow metrics
                'operating_cash_flow': safe_float(latest_cash_flow.get('operatingCashflow')),
                'free_cash_flow': safe_float(latest_cash_flow.get('operatingCashflow')) - safe_float(latest_cash_flow.get('capitalExpenditures')),
                
                # Growth metrics
                'revenue_growth': revenue_growth,
                'earnings_growth': earnings_growth,
                'fcf_growth': fcf_growth
            }
        except Exception as e:
            self.logger.error(f"Error fetching fundamentals for {symbol}: {str(e)}")
            return {}
    
    def _calculate_growth_rates(self, fundamentals: Dict) -> Dict:
        """Calculate year-over-year growth rates."""
        return {
            'revenue_growth': fundamentals.get('revenue_growth', 0),
            'earnings_growth': fundamentals.get('earnings_growth', 0),
            'fcf_growth': fundamentals.get('fcf_growth', 0)
        }
        
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