import logging
import random
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
import tweepy
import config
from engine.sentiment_analyzer import CryptoSentimentAnalyzer
from engine.token_extractor import TokenExtractor

logger = logging.getLogger(__name__)

class XCollector:
    def __init__(self):
        self.sentiment_analyzer = CryptoSentimentAnalyzer()
        self.token_extractor = TokenExtractor()
        self.client = None
        
        if config.TWITTER_BEARER_TOKEN:
            try:
                self.client = tweepy.Client(bearer_token=config.TWITTER_BEARER_TOKEN)
                logger.info("X (Twitter) API Client initialized successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize Tweepy Client: {e}")

    def fetch_recent_tweets(self, query: str = None) -> List[Dict[str, Any]]:
        tweets_data = []
        if self.client and not config.SIMULATION_MODE:
            try:
                search_query = query or " OR ".join([f"${coin}" for coin in config.TARGET_MEME_COINS[:5]])
                search_query += " -is:retweet lang:en"
                
                response = self.client.search_recent_tweets(
                    query=search_query,
                    max_results=20,
                    tweet_fields=["created_at", "public_metrics", "author_id"]
                )
                
                if response.data:
                    for tweet in response.data:
                        text = tweet.text
                        tokens = self.token_extractor.extract_tokens(text)
                        metrics = tweet.public_metrics or {}
                        
                        for token in tokens:
                            tweets_data.append({
                                "platform": "X",
                                "post_id": str(tweet.id),
                                "author": f"user_{tweet.author_id or 'anon'}",
                                "content": text,
                                "token_symbol": token,
                                "sentiment_score": self.sentiment_analyzer.analyze(text),
                                "likes": metrics.get("like_count", 0),
                                "retweets": metrics.get("retweet_count", 0),
                                "created_at": str(tweet.created_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
                            })
                return tweets_data
            except Exception as e:
                logger.warning(f"Error fetching live tweets: {e}. Falling back to simulation if enabled.")

        # Simulation fallback generator
        return self._generate_simulated_tweets()

    def _generate_simulated_tweets(self) -> List[Dict[str, Any]]:
        simulated = []
        templates = [
            "BULLISH on ${coin}! 🚀 Just bought more, to the moon! #100x #crypto",
            "Huge momentum coming for ${coin}! Volume spiking hard 💎🙌",
            "Is ${coin} the next big meme coin pump? Chart looks insane LFG!",
            "Caution on ${coin}, looks like a dump incoming 📉 #scam",
            "${coin} breaking out past key resistance! WAGMI 🚀🚀",
            "Whales accumulation detected on ${coin} 🐋 Don't sleep on this gem!"
        ]
        
        for _ in range(random.randint(3, 8)):
            coin = random.choice(config.TARGET_MEME_COINS)
            template = random.choice(templates)
            text = template.replace("${coin}", coin)
            
            simulated.append({
                "platform": "X",
                "post_id": f"sim_x_{int(time.time()*1000)}_{random.randint(100,999)}",
                "author": f"crypto_trader_{random.randint(1,100)}",
                "content": text,
                "token_symbol": coin,
                "sentiment_score": self.sentiment_analyzer.analyze(text),
                "likes": random.randint(5, 450),
                "retweets": random.randint(1, 120),
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
        return simulated
