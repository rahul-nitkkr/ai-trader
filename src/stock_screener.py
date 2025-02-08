import pandas as pd
import yfinance as yf
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

class StockScreener:
    def __init__(self, agents: list):
        self.agents = agents
        # Define base lists of stocks for each segment
        self.stock_universe = {
            'Large Cap': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'BRK-B', 'LLY', 'V', 'TSM', 
                         'UNH', 'XOM', 'JPM', 'JNJ', 'WMT', 'MA', 'PG', 'HD', 'AVGO', 'MRK', 'CVX', 
                         'KO', 'PEP', 'ABBV', 'COST', 'BAC', 'ADBE', 'MCD', 'CRM', 'CSCO'],
            'Mid Cap': ['AMD', 'UBER', 'SNAP', 'DASH', 'RBLX', 'COIN', 'RIVN', 'LCID', 'ROKU', 'CRWD',
                       'FTNT', 'DDOG', 'ZS', 'PANW', 'SNOW', 'NET', 'AFRM', 'U', 'BILL', 'TTD',
                       'OKTA', 'DOCN', 'GTLB', 'CFLT', 'MDB', 'HUBS', 'TEAM', 'ZI', 'DKNG', 'PINS'],
            'Small Cap': ['PLTR', 'SOFI', 'HOOD', 'PLUG', 'CHPT', 'JOBY', 'ENVX', 'STEM', 'PTRA', 'EVGO',
                         'IONQ', 'DNA', 'MTTR', 'VLD', 'DM', 'MKFG', 'ORGN', 'LILM', 'VORB', 'SPCE',
                         'ASTS', 'RKLB', 'ACHR', 'GSAT', 'OUST', 'NNDM', 'GOEV', 'WKHS', 'BLNK', 'FSR']
        }
        
    def get_segment_stocks(self, segment: str, num_stocks: int) -> List[str]:
        """Get specified number of stocks from a segment."""
        if segment not in self.stock_universe:
            raise ValueError(f"Invalid segment: {segment}")
        
        return self.stock_universe[segment][:num_stocks]
            
    def analyze_stock(self, symbol: str, segment: str) -> Dict:
        """Analyze a single stock using all agents."""
        try:
            # Get historical data
            data = self.agents[0].get_historical_data(symbol, 
                                                    (pd.Timestamp.now() - pd.Timedelta(days=180)).strftime('%Y-%m-%d'),
                                                    pd.Timestamp.now().strftime('%Y-%m-%d'))
            
            if data.empty:
                return None
                
            # Get analysis from all agents
            agent_signals = {}
            for agent in self.agents:
                try:
                    signal = agent.analyze(symbol, data)
                    agent_signals[agent.name] = signal
                except Exception as e:
                    logger.error(f"Error in {agent.name} for {symbol}: {str(e)}")
                    continue
            
            # Get price targets
            price_target_agent = next(a for a in self.agents if a.name == "Price Target Analysis")
            price_analysis = price_target_agent.analyze(symbol, data)
            
            current_price = data['Close'].iloc[-1]
            potential_upside = (price_analysis['metadata']['exit_price'] / current_price - 1) * 100
            
            # Calculate aggregate score
            total_confidence = 0
            weighted_signal = 0
            valid_signals = 0
            
            for signal in agent_signals.values():
                if signal:
                    weighted_signal += signal['signal'] * signal['confidence']
                    total_confidence += signal['confidence']
                    valid_signals += 1
            
            if valid_signals > 0:
                aggregate_signal = weighted_signal / valid_signals
                average_confidence = total_confidence / valid_signals
            else:
                return None
            
            # Get company info
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Compile reasons
            reasons = []
            for agent_name, signal in agent_signals.items():
                if signal and signal['reasoning']:
                    reasons.append(f"{agent_name}: {signal['reasoning']}")
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'current_price': current_price,
                'target_price': price_analysis['metadata']['exit_price'],
                'potential_upside': potential_upside,
                'aggregate_signal': aggregate_signal,
                'confidence': average_confidence,
                'volume': data['Volume'].mean(),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('forwardPE', 0),
                'category': segment,
                'reasons': reasons
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            return None
            
    def screen_stocks(self, segment: str, num_stocks: int, max_workers: int = 5) -> pd.DataFrame:
        """Screen specified number of stocks from a segment in parallel."""
        try:
            # Get stocks for the specified segment
            stocks = self.get_segment_stocks(segment, num_stocks)
            results = []
            
            # Analyze stocks in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_stock = {
                    executor.submit(self.analyze_stock, symbol, segment): symbol
                    for symbol in stocks
                }
                
                for future in tqdm(as_completed(future_to_stock), total=len(stocks)):
                    symbol = future_to_stock[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {str(e)}")
                        continue
            
            # Convert to DataFrame and sort by potential upside
            df = pd.DataFrame(results)
            if not df.empty:
                df = df.sort_values('potential_upside', ascending=False)
            
            return df
            
        except Exception as e:
            logger.error(f"Error in stock screening: {str(e)}")
            return pd.DataFrame()