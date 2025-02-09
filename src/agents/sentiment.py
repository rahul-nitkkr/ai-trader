from typing import Dict, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from nltk.sentiment import SentimentIntensityAnalyzer
from .base_agent import BaseAgent
from src.tools.alpha_vantage.client import AlphaVantageClient

class SentimentAgent(BaseAgent):
    def __init__(self, show_reasoning: bool = False):
        super().__init__("Sentiment Analysis", show_reasoning)
        # Initialize Alpha Vantage client
        self.alpha_vantage = AlphaVantageClient()
        # Initialize NLTK sentiment analyzer for additional analysis
        self.sia = SentimentIntensityAnalyzer()
        
    def _get_news_sentiment(self, symbol: str, days: int = 7) -> Dict:
        """Get and analyze news sentiment for a symbol using Alpha Vantage."""
        try:
            # Get news from Alpha Vantage
            news_data = self.alpha_vantage.get_news_sentiment(tickers=[symbol])
            
            if not news_data or 'feed' not in news_data:
                return {
                    'compound_score': 0,
                    'article_count': 0,
                    'sentiment_scores': [],
                    'topics': []
                }
            
            # Process sentiment scores from articles
            sentiment_scores = []
            topics = set()
            
            for article in news_data.get('feed', []):
                # Use Alpha Vantage's sentiment score
                if 'overall_sentiment_score' in article:
                    # Convert Alpha Vantage score from [-1, 1] to compound score
                    sentiment_scores.append(float(article['overall_sentiment_score']))
                
                # Collect topics
                if 'topics' in article:
                    # Convert each topic to string to ensure hashability
                    article_topics = [str(topic) for topic in article['topics']]
                    topics.update(article_topics)
            
            return {
                'compound_score': np.mean(sentiment_scores) if sentiment_scores else 0,
                'article_count': len(sentiment_scores),
                'sentiment_scores': sentiment_scores,
                'topics': list(topics)
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching news sentiment: {str(e)}")
            return {
                'compound_score': 0,
                'article_count': 0,
                'sentiment_scores': [],
                'topics': []
            }
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Analyze market sentiment for a symbol."""
        # Get sentiment data
        news_sentiment = self._get_news_sentiment(symbol)
        
        # Initialize scoring
        score = 0
        max_score = 3  # Reduced from 5 since we removed social media
        reasons = []
        
        # 1. News Sentiment
        if news_sentiment['article_count'] > 0:
            if news_sentiment['compound_score'] > 0.2:
                score += 1
                reasons.append(f"Positive news sentiment ({news_sentiment['compound_score']:.2f})")
            elif news_sentiment['compound_score'] < -0.2:
                score -= 1
                reasons.append(f"Negative news sentiment ({news_sentiment['compound_score']:.2f})")
            else:
                reasons.append("Neutral news sentiment")
        else:
            reasons.append("No recent news coverage")
            
        # 2. News Volume
        if news_sentiment['article_count'] > 10:
            score += 1
            reasons.append(f"High news volume ({news_sentiment['article_count']} articles)")
        elif news_sentiment['article_count'] == 0:
            score -= 1
            reasons.append("No news coverage")
        else:
            reasons.append(f"Moderate news volume ({news_sentiment['article_count']} articles)")
            
        # 3. Topic Relevance
        relevant_topics = {'earnings', 'revenue', 'growth', 'merger', 'acquisition', 'product', 'technology'}
        found_topics = set(news_sentiment['topics'])
        topic_overlap = found_topics & relevant_topics
        
        if topic_overlap:
            score += 1
            reasons.append(f"Relevant topics found: {', '.join(topic_overlap)}")
        
        # Calculate confidence based on data availability
        confidence = news_sentiment['article_count'] / 10  # Scale confidence by article count
        confidence = min(max(confidence, 0.1), 1.0)  # Clamp between 0.1 and 1.0
        
        # Normalize score to [-1, 1] range
        normalized_score = score / max_score
        
        # Determine signal
        if normalized_score > 0.3:
            signal = 1
            action = "BUY"
        elif normalized_score < -0.3:
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
                'news_sentiment': news_sentiment
            }
        } 