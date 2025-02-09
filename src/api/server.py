import os
import sys
import random
import string
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import requests
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv, set_key
import json
from flask import Flask, request, jsonify
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_server.log')
    ]
)
logger = logging.getLogger('AITrader.API')

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types"""
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                          np.int16, np.int32, np.int64, np.uint8,
                          np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# Configure Flask to use custom JSON encoder
app = Flask(__name__)
app.json_encoder = JSONEncoder
logger.info("Flask application initialized with custom JSON encoder")

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)
logger.info(f"Added project root to Python path: {project_root}")

from src.agents.sentiment import SentimentAgent
from src.agents.fundamentals import FundamentalsAgent
from src.agents.valuation import ValuationAgent
from src.agents.technical_analysis import TechnicalAnalysisAgent
from src.agents.portfolio_manager import PortfolioManager
from src.tools.alpha_vantage.client import AlphaVantageClient

def generate_random_email():
    """Generate a random email for API key registration"""
    username_length = random.randint(6, 12)
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=username_length))
    year = random.randint(1980, 2000)
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    domain = random.choice(domains)
    return f"{username}+{year}@{domain}"

def generate_api_key():
    """Generate a new Alpha Vantage API key"""
    url = "https://www.alphavantage.co/create_post/"
    email = generate_random_email()
    
    # Get CSRF token first
    session = requests.Session()
    support_url = "https://www.alphavantage.co/support/"
    session.get(support_url)
    csrf_token = session.cookies.get('csrftoken')
    
    if not csrf_token:
        return None, "Failed to get CSRF token"
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.alphavantage.co',
        'referer': 'https://www.alphavantage.co/support/',
        'x-requested-with': 'XMLHttpRequest',
        'x-csrftoken': csrf_token
    }
    
    data = {
        'csrfmiddlewaretoken': csrf_token,
        'first_text': 'deprecated',
        'last_text': 'deprecated',
        'occupation_text': 'Investor',
        'organization_text': 'Trading Corp',
        'email_text': email
    }
    
    try:
        response = session.post(url, headers=headers, data=data)
        response.raise_for_status()
        response_data = response.json()
        
        if 'text' in response_data:
            # Try different patterns to extract API key
            patterns = [
                'API key: ',
                'Your API key is: ',
                'Your dedicated access key is: ',
                'access key: '
            ]
            
            for pattern in patterns:
                if pattern in response_data['text']:
                    api_key = response_data['text'].split(pattern)[1].split('.')[0].strip()
                    return api_key, None
            
            return None, "Could not find API key in response"
        else:
            return None, "Invalid response format"
            
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def update_env_file(api_key: str) -> bool:
    """Update the .env file with the Alpha Vantage API key."""
    try:
        env_path = Path(project_root) / '.env'
        if not env_path.exists():
            logger.error(f".env file not found at {env_path}")
            return False
        
        set_key(str(env_path), 'ALPHA_VANTAGE_API_KEY', api_key)
        logger.info("Successfully updated .env file with Alpha Vantage API key")
        return True
    except Exception as e:
        logger.error(f"Error updating .env file: {str(e)}")
        return False

def ensure_api_key() -> bool:
    """Ensure a valid Alpha Vantage API key exists, generate if needed."""
    load_dotenv()
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key or api_key == 'your_alpha_vantage_api_key_here':
        logger.info("No valid Alpha Vantage API key found. Generating new key...")
        api_key, error = generate_api_key()
        
        if not api_key:
            logger.error(f"Failed to generate API key: {error}")
            return False
            
        if not update_env_file(api_key):
            logger.error("Failed to update .env file with new API key")
            return False
            
        load_dotenv()  # Reload environment variables
        logger.info("Successfully generated and configured new API key")
        
    return True

@app.route('/api/alpha-vantage/key', methods=['POST'])
def create_alpha_vantage_key():
    """Generate a new Alpha Vantage API key and update .env file"""
    try:
        logger.info("Generating new Alpha Vantage API key")
        api_key, error = generate_api_key()
        
        if not api_key:
            logger.error(f"Failed to generate API key: {error}")
            return jsonify({
                'success': False,
                'error': error,
                'message': 'Failed to generate API key'
            }), 500
        
        # Update .env file
        if update_env_file(api_key):
            # Reload environment variables
            load_dotenv()
            
            # Reinitialize Alpha Vantage client
            global alpha_vantage_client
            alpha_vantage_client = AlphaVantageClient()
            
            return jsonify({
                'success': True,
                'api_key': api_key,
                'generated_at': datetime.utcnow().isoformat(),
                'message': 'API key generated and configured successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update .env file',
                'message': 'API key generated but configuration failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in create_alpha_vantage_key: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error'
        }), 500

# Initialize clients and agents
try:
    logger.info("Initializing Alpha Vantage client...")
    
    # Ensure we have a valid API key
    if not ensure_api_key():
        raise ValueError("Failed to ensure valid Alpha Vantage API key")
    
    alpha_vantage_client = AlphaVantageClient()
    logger.info("Alpha Vantage client initialized successfully")
    
    logger.info("Initializing trading agents...")
    sentiment_agent = SentimentAgent()
    fundamentals_agent = FundamentalsAgent()
    valuation_agent = ValuationAgent()
    technical_agent = TechnicalAnalysisAgent()
    
    # Initialize portfolio manager with agents and initial capital
    agents = [sentiment_agent, fundamentals_agent, valuation_agent, technical_agent]
    portfolio_manager = PortfolioManager(agents=agents, initial_capital=100000.0)
    logger.info("All agents and portfolio manager initialized successfully")
except Exception as e:
    logger.error(f"Error during initialization: {str(e)}")
    raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/analyze/stock', methods=['POST'])
def analyze_stock():
    """Analyze a stock using all available agents"""
    data = request.get_json()
    symbol = data.get('symbol')
    
    if not symbol:
        logger.warning("Stock analysis request missing symbol")
        return jsonify({
            'error': 'Symbol is required'
        }), 400
    
    try:
        logger.info(f"Analyzing stock: {symbol}")
        # Get historical data for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        logger.debug(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
        historical_data = technical_agent.get_historical_data(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        analyses = {}
        
        # Gather analysis from each agent with error handling
        try:
            logger.debug(f"Running sentiment analysis for {symbol}")
            analyses['sentiment'] = sentiment_agent.analyze(symbol, data=historical_data)
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            analyses['sentiment'] = {'error': str(e)}
        
        try:
            logger.debug(f"Running fundamental analysis for {symbol}")
            analyses['fundamentals'] = fundamentals_agent.analyze(symbol, data=historical_data)
        except Exception as e:
            logger.error(f"Error in fundamental analysis: {str(e)}")
            analyses['fundamentals'] = {'error': str(e)}
        
        try:
            logger.debug(f"Running valuation analysis for {symbol}")
            analyses['valuation'] = valuation_agent.analyze(symbol, data=historical_data)
        except Exception as e:
            logger.error(f"Error in valuation analysis: {str(e)}")
            analyses['valuation'] = {'error': str(e)}
        
        try:
            logger.debug(f"Running technical analysis for {symbol}")
            analyses['technical'] = technical_agent.analyze(symbol, data=historical_data)
        except Exception as e:
            logger.error(f"Error in technical analysis: {str(e)}")
            analyses['technical'] = {'error': str(e)}
        
        logger.info(f"Analysis completed for {symbol}")
        return jsonify({
            'symbol': symbol,
            'timestamp': datetime.now(UTC).isoformat(),
            'analysis': analyses
        })
    except Exception as e:
        logger.error(f"Error analyzing stock {symbol}: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/portfolio/holdings', methods=['GET'])
def get_portfolio_holdings():
    """Get current portfolio holdings"""
    try:
        logger.debug("Fetching portfolio holdings")
        holdings = portfolio_manager.portfolio['positions']
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'holdings': holdings
        })
    except Exception as e:
        logger.error(f"Error fetching portfolio holdings: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/portfolio/trade', methods=['POST'])
def execute_trade():
    """Execute a trade"""
    data = request.get_json()
    symbol = data.get('symbol')
    action = data.get('action')  # 'buy' or 'sell'
    quantity = data.get('quantity')
    
    if not all([symbol, action, quantity]):
        logger.warning("Trade request missing required parameters")
        return jsonify({
            'error': 'Symbol, action, and quantity are required'
        }), 400
    
    try:
        logger.info(f"Executing trade: {action} {quantity} shares of {symbol}")
        # Get current price
        price = float(alpha_vantage_client.get_quote(symbol)['price'])
        order_size = quantity if action == 'buy' else -quantity
        
        result = portfolio_manager.execute_trade(symbol, order_size, price)
        logger.info(f"Trade executed successfully: {action} {quantity} shares of {symbol} at ${price}")
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'trade_result': result
        })
    except Exception as e:
        logger.error(f"Error executing trade for {symbol}: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/market/data', methods=['GET'])
def get_market_data():
    """Get market data for a symbol"""
    symbol = request.args.get('symbol')
    data_type = request.args.get('type', 'overview')  # overview, insider, news, etc.
    
    if not symbol:
        logger.warning("Market data request missing symbol")
        return jsonify({
            'error': 'Symbol is required'
        }), 400
    
    try:
        logger.info(f"Fetching {data_type} data for {symbol}")
        if data_type == 'overview':
            data = alpha_vantage_client.get_company_overview(symbol)
        elif data_type == 'insider':
            data = alpha_vantage_client.get_insider_transactions(symbol)
        elif data_type == 'news':
            data = alpha_vantage_client.get_news_sentiment(tickers=[symbol])
        else:
            logger.warning(f"Unsupported data type requested: {data_type}")
            return jsonify({
                'error': f'Unsupported data type: {data_type}'
            }), 400
        
        return jsonify({
            'symbol': symbol,
            'data_type': data_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        })
    except Exception as e:
        logger.error(f"Error fetching {data_type} data for {symbol}: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/screener', methods=['POST'])
def screen_stocks():
    """Screen stocks based on criteria"""
    data = request.get_json()
    criteria = data.get('criteria', {})
    
    try:
        logger.info("Running stock screener with criteria")
        # Apply screening criteria using agents
        technical_criteria = criteria.get('technical', {})
        fundamental_criteria = criteria.get('fundamental', {})
        
        logger.debug("Running technical screening")
        technical_matches = technical_agent.screen_stocks(technical_criteria)
        fundamental_matches = []  # Removed fundamentals screening as it's not implemented
        
        # Find intersection of matches
        matches = list(set(technical_matches) & set(fundamental_matches))
        logger.info(f"Screener found {len(matches)} matching stocks")
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'matches': matches,
            'total_matches': len(matches)
        })
    except Exception as e:
        logger.error(f"Error running stock screener: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7785))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting API server on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info("Server is ready to accept connections")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 