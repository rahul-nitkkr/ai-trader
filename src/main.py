#!/usr/bin/env python3
import os
import argparse
from datetime import datetime
from dotenv import load_dotenv
import logging

# Import agents
from agents.warren_buffett import WarrenBuffettAgent
from agents.bill_ackman import BillAckmanAgent
from agents.technicals import TechnicalsAgent
from agents.sentiment import SentimentAgent
from agents.fundamentals import FundamentalsAgent
from agents.valuation import ValuationAgent
from agents.price_target import PriceTargetAgent
from agents.risk_manager import RiskManager
from agents.portfolio_manager import PortfolioManager
from backtester import Backtester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables and validate required keys."""
    load_dotenv()
    required_vars = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'FINNHUB_API_KEY',
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def initialize_agents(show_reasoning: bool = False) -> list:
    """Initialize all trading agents."""
    agents = [
        WarrenBuffettAgent(show_reasoning),
        BillAckmanAgent(show_reasoning),
        TechnicalsAgent(show_reasoning),
        SentimentAgent(show_reasoning),
        FundamentalsAgent(show_reasoning),
        ValuationAgent(show_reasoning),
        PriceTargetAgent(show_reasoning),
        RiskManager(show_reasoning)
    ]
    return agents

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='AI Trading System')
    parser.add_argument('--symbols', type=str, nargs='+', required=True,
                      help='List of stock symbols to analyze')
    parser.add_argument('--start-date', type=str,
                      default=os.getenv('DEFAULT_START_DATE', '2020-01-01'),
                      help='Start date for analysis (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                      default=os.getenv('DEFAULT_END_DATE', datetime.now().strftime('%Y-%m-%d')),
                      help='End date for analysis (YYYY-MM-DD)')
    parser.add_argument('--backtest', action='store_true',
                      help='Run backtesting simulation')
    parser.add_argument('--show-reasoning', action='store_true',
                      help='Show detailed reasoning from each agent')
    parser.add_argument('--initial-capital', type=float,
                      default=float(os.getenv('INITIAL_CAPITAL', 1000000)),
                      help='Initial capital for trading/backtesting')
    
    return parser.parse_args()

def main():
    """Main entry point for the AI trading system."""
    try:
        # Load and validate environment
        load_environment()
        
        # Parse command line arguments
        args = parse_args()
        
        # Initialize agents
        agents = initialize_agents(args.show_reasoning)
        
        # Initialize portfolio manager
        portfolio_manager = PortfolioManager(agents, args.initial_capital, args.show_reasoning)
        
        if args.backtest:
            logger.info(f"Running backtest from {args.start_date} to {args.end_date}")
            # Run backtesting simulation
            backtester = Backtester(agents, args.initial_capital)
            results = backtester.run(args.symbols, args.start_date, args.end_date)
            
            # Log backtest results
            logger.info("\nBacktest Results:")
            logger.info(f"Total Return: {results['total_return']:.2%}")
            logger.info(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
            logger.info(f"Max Drawdown: {results['max_drawdown']:.2%}")
            logger.info("\nDetailed results saved to backtest_results.html")
        else:
            logger.info("Running live analysis")
            # Run live analysis for each symbol
            for symbol in args.symbols:
                try:
                    # Get historical data using the first agent's data fetching method
                    data = agents[0].get_historical_data(symbol, args.start_date, args.end_date)
                    
                    # Get trading decision
                    decision = portfolio_manager.analyze(symbol, data)
                    
                    # Log decision
                    logger.info(f"\nAnalysis for {symbol}:")
                    logger.info(decision['reasoning'])
                    
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {str(e)}")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 