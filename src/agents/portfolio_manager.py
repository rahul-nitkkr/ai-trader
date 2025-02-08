from typing import Dict, List
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from .base_agent import BaseAgent

class PortfolioManager(BaseAgent):
    def __init__(self, agents: List[BaseAgent], initial_capital: float, show_reasoning: bool = False):
        super().__init__("Portfolio Manager", show_reasoning)
        self.agents = agents
        self.initial_capital = initial_capital
        self.portfolio = {
            'cash': initial_capital,
            'positions': {},  # symbol -> {'shares': n, 'cost_basis': price}
        }
        
        # Agent weights for signal aggregation
        self.agent_weights = {
            'Warren Buffett': 0.20,
            'Bill Ackman': 0.15,
            'Technical Analysis': 0.15,
            'Sentiment Analysis': 0.10,
            'Risk Manager': 0.40
        }
        
    def _get_agent_by_name(self, name: str) -> BaseAgent:
        """Get agent instance by name."""
        for agent in self.agents:
            if agent.name == name:
                return agent
        raise ValueError(f"Agent not found: {name}")
        
    def _aggregate_signals(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Aggregate signals from all agents."""
        signals = {}
        total_weight = 0
        
        for agent in self.agents:
            try:
                signal = agent.analyze(symbol, data)
                weight = self.agent_weights.get(agent.name, 0)
                signals[agent.name] = {
                    'signal': signal['signal'],
                    'confidence': signal['confidence'],
                    'weight': weight,
                    'reasoning': signal['reasoning'],
                    'metadata': signal['metadata']
                }
                total_weight += weight
            except Exception as e:
                self.logger.error(f"Error getting signal from {agent.name}: {str(e)}")
                
        if total_weight == 0:
            raise ValueError("No valid signals received from agents")
            
        # Normalize weights
        for signal in signals.values():
            signal['weight'] /= total_weight
            
        return signals
        
    def _calculate_order_size(self, symbol: str, price: float, signals: Dict) -> int:
        """Calculate order size based on signals and risk management."""
        # Get risk manager's position size recommendation
        risk_manager = self._get_agent_by_name('Risk Manager')
        risk_signal = signals[risk_manager.name]
        max_position_size = risk_signal['metadata']['position_size']
        
        # Calculate weighted signal
        weighted_signal = sum(s['signal'] * s['confidence'] * s['weight'] 
                            for s in signals.values())
        
        # Calculate target position value
        target_value = self.initial_capital * max_position_size * abs(weighted_signal)
        
        # Get current position
        current_position = self.portfolio['positions'].get(symbol, {'shares': 0})
        current_shares = current_position.get('shares', 0)
        
        # Calculate target shares
        target_shares = int(target_value / price)
        
        # Return difference in shares
        return target_shares - current_shares
        
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Make final trading decision for a symbol."""
        if data.empty:
            raise ValueError(f"No data provided for {symbol}")
            
        current_price = data.iloc[-1]['Close']
        
        # Get signals from all agents
        signals = self._aggregate_signals(symbol, data)
        
        # Calculate order size
        order_size = self._calculate_order_size(symbol, current_price, signals)
        
        # Prepare reasoning
        reasons = [f"{name}: {s['reasoning']}" for name, s in signals.items()]
        
        # Calculate weighted confidence
        confidence = sum(s['confidence'] * s['weight'] for s in signals.values())
        
        # Determine final action
        if order_size > 0:
            signal = 1
            action = f"BUY {order_size} shares"
        elif order_size < 0:
            signal = -1
            action = f"SELL {abs(order_size)} shares"
        else:
            signal = 0
            action = "HOLD position"
            
        reasoning = f"{action} with {confidence:.1%} confidence.\n" + "\n".join(reasons)
        self.log_reasoning(reasoning)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning,
            'metadata': {
                'signals': signals,
                'order_size': order_size,
                'current_price': current_price,
                'portfolio': self.portfolio
            }
        }
        
    def execute_trade(self, symbol: str, order_size: int, price: float) -> bool:
        """Execute a trade and update portfolio."""
        try:
            cost = order_size * price
            
            if order_size > 0:  # Buy
                if cost > self.portfolio['cash']:
                    self.logger.warning(f"Insufficient cash for {symbol} buy order")
                    return False
                    
                self.portfolio['cash'] -= cost
                position = self.portfolio['positions'].get(symbol, {'shares': 0, 'cost_basis': 0})
                new_shares = position['shares'] + order_size
                position['cost_basis'] = ((position['cost_basis'] * position['shares'] + cost) / 
                                        new_shares)
                position['shares'] = new_shares
                self.portfolio['positions'][symbol] = position
                
            else:  # Sell
                position = self.portfolio['positions'].get(symbol)
                if not position or abs(order_size) > position['shares']:
                    self.logger.warning(f"Insufficient shares for {symbol} sell order")
                    return False
                    
                self.portfolio['cash'] += abs(cost)
                position['shares'] += order_size  # order_size is negative for sells
                
                if position['shares'] == 0:
                    del self.portfolio['positions'][symbol]
                else:
                    self.portfolio['positions'][symbol] = position
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {str(e)}")
            return False 