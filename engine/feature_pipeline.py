import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from ingestion.database import DatabaseManager
import config

logger = logging.getLogger(__name__)

class FeaturePipeline:
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()

    def compute_token_features(self, token_symbol: str) -> Dict[str, Any]:
        """
        Calculates time-window metrics for a specific meme coin.
        """
        token = token_symbol.upper()
        now = datetime.now(timezone.utc)
        h1_cutoff = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        prev_h1_cutoff = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        h24_cutoff = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # 1-hour posts
            cursor.execute("""
                SELECT sentiment_score, likes, retweets, author, platform
                FROM posts
                WHERE token_symbol = ? AND created_at >= ?
            """, (token, h1_cutoff))
            h1_posts = [dict(row) for row in cursor.fetchall()]

            # Previous 1-hour post count for velocity
            cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM posts
                WHERE token_symbol = ? AND created_at >= ? AND created_at < ?
            """, (token, prev_h1_cutoff, h1_cutoff))
            prev_h1_count = cursor.fetchone()["cnt"]

            # 24-hour post count
            cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM posts
                WHERE token_symbol = ? AND created_at >= ?
            """, (token, h24_cutoff))
            h24_count = cursor.fetchone()["cnt"]

        post_count_1h = len(h1_posts)
        
        # Calculate Volume Velocity
        if prev_h1_count == 0:
            volume_velocity = float(post_count_1h) # Spiked from 0
        else:
            volume_velocity = (post_count_1h - prev_h1_count) / float(prev_h1_count)

        # Sentiment statistics
        if post_count_1h > 0:
            sentiments = [p["sentiment_score"] for p in h1_posts]
            avg_sentiment = sum(sentiments) / float(post_count_1h)
            bullish_count = sum(1 for s in sentiments if s >= 0.15)
            bullish_ratio = bullish_count / float(post_count_1h)
            
            authors = set(p["author"] for p in h1_posts if p["author"])
            unique_authors_1h = len(authors)

            total_likes = sum(p["likes"] for p in h1_posts)
            total_retweets = sum(p["retweets"] for p in h1_posts)
            total_engagement_1h = total_likes + (total_retweets * 2)

            x_count = sum(1 for p in h1_posts if p["platform"].upper() in ["X", "TWITTER"])
            x_ratio = x_count / float(post_count_1h)
        else:
            avg_sentiment = 0.0
            bullish_ratio = 0.0
            unique_authors_1h = 0
            total_engagement_1h = 0
            x_ratio = 0.5

        # Social Reach Score: weighted combination of volume, author diversity, engagement
        social_reach_score = (post_count_1h * 1.5) + (unique_authors_1h * 2.0) + (total_engagement_1h * 0.1)

        features = {
            "token_symbol": token,
            "post_count_1h": post_count_1h,
            "post_count_24h": h24_count,
            "volume_velocity": round(volume_velocity, 4),
            "avg_sentiment": round(avg_sentiment, 4),
            "bullish_ratio": round(bullish_ratio, 4),
            "unique_authors_1h": unique_authors_1h,
            "total_engagement_1h": total_engagement_1h,
            "social_reach_score": round(social_reach_score, 2),
            "x_ratio": round(x_ratio, 4),
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Store metric record in DB
        self.db.insert_token_metric(features)

        return features

    def compute_all_tokens(self) -> Dict[str, Dict[str, Any]]:
        results = {}
        for token in config.TARGET_MEME_COINS:
            results[token] = self.compute_token_features(token)
        return results
