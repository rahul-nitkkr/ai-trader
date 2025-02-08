from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, agents: List, initial_capital: float):
        self.agents = agents
        self.initial_capital = initial_capital
        self.portfolio = {
            'cash': initial_capital,
            'positions': {},  # symbol -> {'shares': n, 'cost_basis': price}
            'history': []     # List of portfolio states over time
        }
        
    def run(self, symbols: List[str], start_date: str, end_date: str) -> Dict:
        """Run backtest simulation for given symbols and time period."""
        logger.info(f"Starting backtest simulation for {symbols} from {start_date} to {end_date}")
        
        # Get historical data for all symbols
        data = {}
        for symbol in symbols:
            # Use the first agent's data fetching method (they all inherit from BaseAgent)
            data[symbol] = self.agents[0].get_historical_data(symbol, start_date, end_date)
        
        # Combine all dates across all symbols
        all_dates = sorted(set().union(*[df.index for df in data.values()]))
        
        # Simulate trading for each day
        for date in all_dates:
            self._simulate_trading_day(date, data)
            
        # Calculate performance metrics
        results = self._calculate_performance()
        self._plot_results(results)
        
        return results
    
    def _simulate_trading_day(self, date: datetime, data: Dict[str, pd.DataFrame]) -> None:
        """Simulate a single trading day."""
        # Get signals from all agents for all symbols
        signals = {}
        for symbol, df in data.items():
            if date in df.index:
                symbol_signals = []
                for agent in self.agents:
                    signal = agent.analyze(symbol, df.loc[:date])
                    symbol_signals.append(signal)
                
                # Aggregate signals (simple average for now)
                confidence_weighted_signal = sum(s['signal'] * s['confidence'] for s in symbol_signals) / len(symbol_signals)
                signals[symbol] = confidence_weighted_signal
        
        # Execute trades based on signals
        self._execute_trades(date, signals, data)
        
        # Record portfolio state
        self._record_portfolio_state(date, data)
    
    def _execute_trades(self, date: datetime, signals: Dict[str, float], data: Dict[str, pd.DataFrame]) -> None:
        """Execute trades based on signals."""
        for symbol, signal in signals.items():
            if date not in data[symbol].index:
                continue
                
            price = data[symbol].loc[date, 'Close']
            position = self.portfolio['positions'].get(symbol, {'shares': 0, 'cost_basis': 0})
            
            # Determine position size based on signal strength
            target_position_value = abs(signal) * self.initial_capital * 0.1  # Max 10% per position
            target_shares = int(target_position_value / price)
            
            if signal > 0.3:  # Buy signal
                shares_to_buy = target_shares - position['shares']
                if shares_to_buy > 0:
                    cost = shares_to_buy * price
                    if cost <= self.portfolio['cash']:
                        self.portfolio['cash'] -= cost
                        position['shares'] += shares_to_buy
                        position['cost_basis'] = ((position['cost_basis'] * (position['shares'] - shares_to_buy) +
                                                 cost) / position['shares'])
                        self.portfolio['positions'][symbol] = position
                        
            elif signal < -0.3:  # Sell signal
                if position['shares'] > 0:
                    proceeds = position['shares'] * price
                    self.portfolio['cash'] += proceeds
                    del self.portfolio['positions'][symbol]
    
    def _record_portfolio_state(self, date: datetime, data: Dict[str, pd.DataFrame]) -> None:
        """Record the portfolio state for the given date."""
        total_value = self.portfolio['cash']
        positions_value = {}
        
        for symbol, position in self.portfolio['positions'].items():
            if date in data[symbol].index:
                price = data[symbol].loc[date, 'Close']
                position_value = position['shares'] * price
                total_value += position_value
                positions_value[symbol] = position_value
        
        self.portfolio['history'].append({
            'date': date,
            'total_value': total_value,
            'cash': self.portfolio['cash'],
            'positions_value': positions_value
        })
    
    def _calculate_performance(self) -> Dict:
        """Calculate performance metrics."""
        history_df = pd.DataFrame(self.portfolio['history'])
        returns = history_df['total_value'].pct_change()
        
        return {
            'total_return': (history_df['total_value'].iloc[-1] / self.initial_capital - 1),
            'sharpe_ratio': np.sqrt(252) * returns.mean() / returns.std(),
            'max_drawdown': (history_df['total_value'] / history_df['total_value'].cummax() - 1).min(),
            'history': history_df
        }
    
    def _plot_results(self, results: Dict) -> None:
        """Create interactive plots of backtest results."""
        history_df = results['history']
        
        fig = make_subplots(rows=2, cols=1, 
                           subplot_titles=('Portfolio Value', 'Asset Allocation'),
                           vertical_spacing=0.15)
        
        # Portfolio value plot
        fig.add_trace(
            go.Scatter(x=history_df['date'], y=history_df['total_value'],
                      name='Portfolio Value'),
            row=1, col=1
        )
        
        # Asset allocation plot
        cash_pct = history_df['cash'] / history_df['total_value'] * 100
        fig.add_trace(
            go.Scatter(x=history_df['date'], y=cash_pct,
                      name='Cash %', stackgroup='allocation'),
            row=2, col=1
        )
        
        # Add position allocations
        for symbol in history_df['positions_value'].iloc[0].keys():
            position_pct = history_df['positions_value'].apply(
                lambda x: x.get(symbol, 0)) / history_df['total_value'] * 100
            fig.add_trace(
                go.Scatter(x=history_df['date'], y=position_pct,
                          name=f'{symbol} %', stackgroup='allocation'),
                row=2, col=1
            )
        
        fig.update_layout(
            title='Backtest Results',
            height=800,
            showlegend=True
        )
        
        # Save the plot
        fig.write_html('backtest_results.html') 