from typing import Dict, List
import pandas as pd
import numpy as np
from datetime import datetime
import os
from .base_agent import BaseAgent

class RiskManager(BaseAgent):
    def __init__(self, show_reasoning: bool = False):
        super().__init__("Risk Manager", show_reasoning)
        # Load risk parameters from environment
        self.max_position_size = float(os.getenv('MAX_POSITION_SIZE', 0.20))
        self.stop_loss_threshold = float(os.getenv('STOP_LOSS_THRESHOLD', 0.15))
        self.risk_free_rate = float(os.getenv('RISK_FREE_RATE', 0.02))
        
        # Risk metrics thresholds
        self.max_portfolio_var = 0.25  # Maximum portfolio variance
        self.min_sharpe_ratio = 1.0    # Minimum Sharpe ratio
        self.max_drawdown_limit = 0.25  # Maximum drawdown limit
        self.beta_threshold = 1.5       # Maximum acceptable beta
        
    def _calculate_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate risk metrics for a symbol."""
        # Calculate daily returns
        returns = data['Close'].pct_change().dropna()
        
        # Calculate metrics
        volatility = returns.std() * np.sqrt(252)  # Annualized volatility
        sharpe_ratio = (returns.mean() * 252 - self.risk_free_rate) / volatility if volatility != 0 else 0
        
        # Calculate maximum drawdown
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = cumulative_returns / rolling_max - 1
        max_drawdown = drawdowns.min()
        
        # Calculate beta using SPY as market proxy
        try:
            market_data = self.get_historical_data('SPY', 
                                                 data.index[0].strftime('%Y-%m-%d'),
                                                 data.index[-1].strftime('%Y-%m-%d'))
            market_returns = market_data['Close'].pct_change().dropna()
            
            # Align the return series
            common_index = returns.index.intersection(market_returns.index)
            if len(common_index) > 0:
                stock_returns = returns[common_index]
                market_returns = market_returns[common_index]
                covariance = np.cov(stock_returns, market_returns)[0][1]
                market_variance = np.var(market_returns)
                beta = covariance / market_variance if market_variance != 0 else 1
            else:
                beta = 1
        except Exception:
            beta = 1
            
        return {
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'beta': beta,
            'var_95': np.percentile(returns, 5),  # 95% VaR
            'recent_volatility': returns.tail(20).std() * np.sqrt(252)  # Recent volatility
        }
        
    def _calculate_position_size(self, metrics: Dict, confidence: float) -> float:
        """Calculate recommended position size based on risk metrics."""
        # Start with maximum position size
        size = self.max_position_size
        
        # Adjust based on volatility
        if metrics['volatility'] > 0.4:  # High volatility
            size *= 0.5
        elif metrics['volatility'] > 0.3:
            size *= 0.7
            
        # Adjust based on beta
        if metrics['beta'] > self.beta_threshold:
            size *= 0.7
            
        # Adjust based on Sharpe ratio
        if metrics['sharpe_ratio'] < self.min_sharpe_ratio:
            size *= 0.8
            
        # Adjust based on maximum drawdown
        if abs(metrics['max_drawdown']) > self.max_drawdown_limit:
            size *= 0.6
            
        # Scale by confidence
        size *= confidence
        
        return min(size, self.max_position_size)
        
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Analyze risk metrics and provide position sizing recommendations."""
        # Calculate risk metrics
        metrics = self._calculate_metrics(data)
        
        # Initialize scoring
        score = 0
        max_score = 5
        reasons = []
        
        # 1. Volatility Assessment
        if metrics['volatility'] < 0.2:
            score += 1
            reasons.append(f"Low volatility ({metrics['volatility']:.1%})")
        elif metrics['volatility'] > 0.4:
            score -= 1
            reasons.append(f"High volatility ({metrics['volatility']:.1%})")
        else:
            reasons.append(f"Moderate volatility ({metrics['volatility']:.1%})")
            
        # 2. Sharpe Ratio
        if metrics['sharpe_ratio'] > self.min_sharpe_ratio:
            score += 1
            reasons.append(f"Good risk-adjusted returns (Sharpe: {metrics['sharpe_ratio']:.2f})")
        else:
            score -= 1
            reasons.append(f"Poor risk-adjusted returns (Sharpe: {metrics['sharpe_ratio']:.2f})")
            
        # 3. Maximum Drawdown
        if abs(metrics['max_drawdown']) < self.max_drawdown_limit:
            score += 1
            reasons.append(f"Acceptable drawdown ({metrics['max_drawdown']:.1%})")
        else:
            score -= 1
            reasons.append(f"Excessive drawdown ({metrics['max_drawdown']:.1%})")
            
        # 4. Beta Assessment
        if metrics['beta'] < self.beta_threshold:
            score += 1
            reasons.append(f"Moderate market sensitivity (Beta: {metrics['beta']:.2f})")
        else:
            score -= 1
            reasons.append(f"High market sensitivity (Beta: {metrics['beta']:.2f})")
            
        # 5. Recent Volatility Trend
        if metrics['recent_volatility'] < metrics['volatility']:
            score += 1
            reasons.append("Decreasing volatility trend")
        elif metrics['recent_volatility'] > metrics['volatility'] * 1.2:
            score -= 1
            reasons.append("Increasing volatility trend")
        else:
            reasons.append("Stable volatility trend")
            
        # Calculate confidence and normalize score
        confidence = abs(score) / max_score
        normalized_score = score / max_score
        
        # Calculate position size
        position_size = self._calculate_position_size(metrics, confidence)
        
        # Determine signal based on risk assessment
        if normalized_score > 0.3 and metrics['sharpe_ratio'] > self.min_sharpe_ratio:
            signal = 1
            action = "RISK ACCEPTABLE"
        elif normalized_score < -0.3 or metrics['sharpe_ratio'] < 0:
            signal = -1
            action = "HIGH RISK"
        else:
            signal = 0
            action = "MODERATE RISK"
            
        reasoning = f"{action} with {confidence:.1%} confidence. Recommended position size: {position_size:.1%}. " + " ".join(reasons)
        self.log_reasoning(reasoning)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning,
            'metadata': {
                'score': score,
                'max_score': max_score,
                'metrics': metrics,
                'position_size': position_size,
                'stop_loss': self.stop_loss_threshold
            }
        } 