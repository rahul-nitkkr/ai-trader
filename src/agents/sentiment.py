from typing import Dict, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import finnhub
import os
from nltk.sentiment import SentimentIntensityAnalyzer
from .base_agent import BaseAgent

class SentimentAgent(BaseAgent):
    def __init__(self, show_reasoning: bool = False):
        super().__init__("Sentiment Analysis", show_reasoning)
        # Initialize Finnhub client
        self.finnhub_client = finnhub.Client(api_key=os.getenv('FINNHUB_API_KEY'))
        # Initialize NLTK sentiment analyzer
        self.sia = SentimentIntensityAnalyzer()
        
    def _get_news_sentiment(self, symbol: str, days: int = 7) -> Dict:
        """Get and analyze news sentiment for a symbol."""
        try:
            # Get news from Finnhub
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            news = self.finnhub_client.company_news(
                symbol,
                _from=start_date.strftime('%Y-%m-%d'),
                to=end_date.strftime('%Y-%m-%d')
            )
            
            if not news:
                return {
                    'compound_score': 0,
                    'article_count': 0,
                    'sentiment_scores': []
                }
            
            # Analyze sentiment for each article
            sentiment_scores = []
            for article in news:
                if article.get('headline') and article.get('summary'):
                    text = f"{article['headline']} {article['summary']}"
                    sentiment = self.sia.polarity_scores(text)
                    sentiment_scores.append(sentiment['compound'])
            
            return {
                'compound_score': np.mean(sentiment_scores) if sentiment_scores else 0,
                'article_count': len(sentiment_scores),
                'sentiment_scores': sentiment_scores
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching news sentiment: {str(e)}")
            return {
                'compound_score': 0,
                'article_count': 0,
                'sentiment_scores': []
            }
    
    def _get_social_sentiment(self, symbol: str) -> Dict:
        """Get social media sentiment from Finnhub."""
        try:
            sentiment = self.finnhub_client.stock_social_sentiment(symbol)
            
            # Process Reddit sentiment
            reddit = sentiment.get('reddit', [])
            reddit_score = np.mean([post['score'] for post in reddit]) if reddit else 0
            reddit_mentions = sum(post['mention'] for post in reddit) if reddit else 0
            
            # Process Twitter sentiment
            twitter = sentiment.get('twitter', [])
            twitter_score = np.mean([post['score'] for post in twitter]) if twitter else 0
            twitter_mentions = sum(post['mention'] for post in twitter) if twitter else 0
            
            return {
                'reddit_score': reddit_score,
                'reddit_mentions': reddit_mentions,
                'twitter_score': twitter_score,
                'twitter_mentions': twitter_mentions
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching social sentiment: {str(e)}")
            return {
                'reddit_score': 0,
                'reddit_mentions': 0,
                'twitter_score': 0,
                'twitter_mentions': 0
            }
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Analyze market sentiment for a symbol."""
        # Get sentiment data
        news_sentiment = self._get_news_sentiment(symbol)
        social_sentiment = self._get_social_sentiment(symbol)
        
        # Initialize scoring
        score = 0
        max_score = 5
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
            
        # 3. Reddit Sentiment
        if social_sentiment['reddit_mentions'] > 0:
            if social_sentiment['reddit_score'] > 0.2:
                score += 1
                reasons.append(f"Positive Reddit sentiment ({social_sentiment['reddit_score']:.2f})")
            elif social_sentiment['reddit_score'] < -0.2:
                score -= 1
                reasons.append(f"Negative Reddit sentiment ({social_sentiment['reddit_score']:.2f})")
            else:
                reasons.append("Neutral Reddit sentiment")
        else:
            reasons.append("No Reddit mentions")
            
        # 4. Twitter Sentiment
        if social_sentiment['twitter_mentions'] > 0:
            if social_sentiment['twitter_score'] > 0.2:
                score += 1
                reasons.append(f"Positive Twitter sentiment ({social_sentiment['twitter_score']:.2f})")
            elif social_sentiment['twitter_score'] < -0.2:
                score -= 1
                reasons.append(f"Negative Twitter sentiment ({social_sentiment['twitter_score']:.2f})")
            else:
                reasons.append("Neutral Twitter sentiment")
        else:
            reasons.append("No Twitter mentions")
            
        # 5. Social Media Volume
        total_mentions = social_sentiment['reddit_mentions'] + social_sentiment['twitter_mentions']
        if total_mentions > 100:
            score += 1
            reasons.append(f"High social media activity ({total_mentions} mentions)")
        elif total_mentions == 0:
            score -= 1
            reasons.append("No social media activity")
        else:
            reasons.append(f"Moderate social media activity ({total_mentions} mentions)")
            
        # Calculate confidence based on data availability and consistency
        data_points = sum(1 for s in [
            news_sentiment['compound_score'],
            social_sentiment['reddit_score'],
            social_sentiment['twitter_score']
        ] if s != 0)
        
        confidence = (data_points / 3) * (abs(score) / max_score)
        
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
                'news_sentiment': news_sentiment,
                'social_sentiment': social_sentiment
            }
        } 