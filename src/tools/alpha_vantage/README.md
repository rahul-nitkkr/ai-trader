# Alpha Vantage API Tools

This module provides a Python interface to the Alpha Vantage API, offering access to financial market data, technical indicators, and fundamental analysis tools.

## Features

- Market News & Sentiment Analysis
- Insider Transactions
- Company Fundamentals (Overview, Income Statement, Balance Sheet, Cash Flow)
- ETF Data
- Technical Indicators (SMA, EMA, RSI, MACD, etc.)
- Corporate Actions (Dividends, Splits)
- Market Status (Listings, IPOs, Earnings Calendar)

## Installation

The module is part of the AI Trader project. All dependencies are listed in the root `requirements.txt` file.

## Usage

```python
from src.tools.alpha_vantage import AlphaVantageClient, Function, Interval

# Initialize the client
client = AlphaVantageClient(api_key="YOUR_API_KEY")
# Or set ALPHA_VANTAGE_API_KEY environment variable

# Get company overview
overview = client.get_company_overview("AAPL")

# Get news and sentiment
news = client.get_news_sentiment(
    tickers=["AAPL", "MSFT"],
    topics=["technology"],
    limit=10
)

# Get technical indicators
sma = client.get_technical_indicator(
    function=Function.SMA,
    symbol="AAPL",
    interval=Interval.DAILY,
    time_period=20,
    series_type="close"
)
```

## API Rate Limits

The free API key from Alpha Vantage has the following limits:
- 5 API calls per minute
- 500 API calls per day

For higher limits, consider getting a premium API key from Alpha Vantage.

## Error Handling

The client includes proper error handling for:
- Invalid API keys
- Rate limiting
- Network errors
- Invalid parameters
- API response parsing

## Data Models

All API responses are mapped to proper Python dataclasses for better type safety and code completion:

- `NewsArticle` & `NewsSentimentResponse`
- `InsiderTransaction` & `InsiderTransactionsResponse`
- `CompanyOverview`
- `ETFProfile`
- `FinancialStatement` (base class for Income Statement, Balance Sheet, Cash Flow)
- `EarningsData`
- `ListingStatus`
- `EarningsCalendarEvent`
- `IPOCalendarEvent`

## Environment Variables

- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key (optional, can be passed directly to client) 