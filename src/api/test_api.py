import requests
import json
from datetime import datetime

def test_api():
    """Test the AI Trader API endpoints"""
    base_url = "http://localhost:5000"
    
    def print_response(description, response):
        print(f"\n{description}")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        print("-" * 80)
    
    # Test health check
    print("\nTesting health check endpoint...")
    response = requests.get(f"{base_url}/health")
    print_response("Health Check", response)
    
    # Test stock analysis
    print("\nTesting stock analysis endpoint...")
    analysis_data = {
        "symbol": "AAPL"
    }
    response = requests.post(f"{base_url}/api/analyze/stock", json=analysis_data)
    print_response("Stock Analysis", response)
    
    # Test portfolio holdings
    print("\nTesting portfolio holdings endpoint...")
    response = requests.get(f"{base_url}/api/portfolio/holdings")
    print_response("Portfolio Holdings", response)
    
    # Test trade execution
    print("\nTesting trade execution endpoint...")
    trade_data = {
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 10
    }
    response = requests.post(f"{base_url}/api/portfolio/trade", json=trade_data)
    print_response("Trade Execution", response)
    
    # Test market data
    print("\nTesting market data endpoint...")
    response = requests.get(f"{base_url}/api/market/data", params={
        "symbol": "AAPL",
        "type": "overview"
    })
    print_response("Market Data (Overview)", response)
    
    response = requests.get(f"{base_url}/api/market/data", params={
        "symbol": "AAPL",
        "type": "insider"
    })
    print_response("Market Data (Insider)", response)
    
    # Test stock screener
    print("\nTesting stock screener endpoint...")
    screener_data = {
        "criteria": {
            "technical": {
                "rsi_threshold": 30,
                "moving_average_period": 50,
                "price_above_ma": True
            },
            "fundamental": {
                "min_market_cap": 1000000000,
                "max_pe_ratio": 20,
                "min_dividend_yield": 2.0
            }
        }
    }
    response = requests.post(f"{base_url}/api/screener", json=screener_data)
    print_response("Stock Screener", response)

if __name__ == "__main__":
    test_api() 