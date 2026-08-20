import logging
from typing import List, Dict, Any
from ingestion.database import DatabaseManager
from ingestion.x_collector import XCollector
from ingestion.telegram_collector import TelegramCollector

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        self.x_collector = XCollector()
        self.tg_collector = TelegramCollector()

    def collect_and_store(self) -> List[Dict[str, Any]]:
        """
        Fetches posts from X and Telegram and persists them to SQLite.
        """
        all_posts = []
        
        # 1. Fetch from X
        try:
            x_posts = self.x_collector.fetch_recent_tweets()
            all_posts.extend(x_posts)
        except Exception as e:
            logger.error(f"Error collecting X posts: {e}")

        # 2. Fetch from Telegram
        try:
            tg_posts = self.tg_collector.fetch_recent_messages()
            all_posts.extend(tg_posts)
        except Exception as e:
            logger.error(f"Error collecting Telegram posts: {e}")

        # Store to DB
        stored_count = 0
        for post in all_posts:
            self.db.insert_post(
                platform=post["platform"],
                post_id=post.get("post_id"),
                author=post.get("author"),
                content=post["content"],
                token_symbol=post["token_symbol"],
                sentiment_score=post.get("sentiment_score", 0.0),
                likes=post.get("likes", 0),
                retweets=post.get("retweets", 0),
                created_at=post.get("created_at")
            )
            stored_count += 1

        logger.info(f"Ingested {stored_count} new posts from X & Telegram.")
        return all_posts
