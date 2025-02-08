# AI Trader

An AI-powered trading system that uses multiple specialized agents to make investment decisions. This project is for **educational purposes only** and is not intended for real trading or investment.

## Overview

This system employs several AI agents that work together to analyze stocks and make trading decisions:

1. **Bill Ackman Agent** - Applies activist investing principles
2. **Warren Buffett Agent** - Implements value investing strategies
3. **Valuation Agent** - Calculates intrinsic value using various methods
4. **Sentiment Agent** - Analyzes market sentiment from various sources
5. **Fundamentals Agent** - Evaluates company fundamentals
6. **Technicals Agent** - Analyzes technical indicators
7. **Risk Manager** - Manages portfolio risk and position sizing
8. **Portfolio Manager** - Makes final trading decisions

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-trader.git
cd ai-trader
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the setup script to download required data and initialize the environment:
```bash
python setup.py
```

5. Edit the `.env` file with your API keys:
- OPENAI_API_KEY - For LLM-based analysis
- ANTHROPIC_API_KEY - For LLM-based analysis
- FINNHUB_API_KEY - For additional financial data

## Usage

Run the trading system with:

```bash
python src/main.py --symbols AAPL MSFT GOOGL --start-date 2023-01-01 --end-date 2024-02-08
```

Options:
- `--symbols`: List of stock symbols to analyze
- `--start-date`: Start date for analysis (YYYY-MM-DD)
- `--end-date`: End date for analysis (YYYY-MM-DD)
- `--backtest`: Run backtesting simulation
- `--show-reasoning`: Show detailed reasoning from each agent
- `--initial-capital`: Initial capital for trading/backtesting (default: $1,000,000)

### Example

To run a backtest with detailed agent reasoning:

```bash
python src/main.py --symbols AAPL MSFT GOOGL --start-date 2023-01-01 --end-date 2024-02-08 --backtest --show-reasoning
```

## Backtesting Results

After running a backtest, the system will generate an interactive HTML report (`backtest_results.html`) showing:
- Portfolio value over time
- Asset allocation
- Performance metrics (returns, Sharpe ratio, max drawdown)
- Individual agent decisions and reasoning

## Project Structure

```
ai-trader/
├── src/
│   ├── agents/                   # Agent definitions and workflow
│   │   ├── bill_ackman.py       # Bill Ackman agent
│   │   ├── fundamentals.py      # Fundamental analysis agent
│   │   ├── portfolio_manager.py # Portfolio management agent
│   │   ├── risk_manager.py      # Risk management agent
│   │   ├── sentiment.py         # Sentiment analysis agent
│   │   ├── technicals.py        # Technical analysis agent
│   │   ├── valuation.py         # Valuation analysis agent
│   │   └── warren_buffett.py    # Warren Buffett agent
│   ├── tools/                   # Agent tools
│   │   └── api.py              # API tools
│   ├── backtester.py           # Backtesting tools
│   └── main.py                 # Main entry point
├── data/                       # Data storage
├── results/                    # Results and reports
├── setup.py                    # Setup script
├── requirements.txt            # Python dependencies
└── .env                       # Configuration file
```

## Disclaimer

This software is for educational and research purposes only. It is not intended to be used for actual trading. The creators and contributors are not responsible for any financial losses incurred from using this software. Always consult with a qualified financial advisor before making investment decisions.