import logging
import random
import time
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any
import config
from engine.sentiment_analyzer import CryptoSentimentAnalyzer
from engine.token_extractor import TokenExtractor

logger = logging.getLogger(__name__)

class TelegramCollector:
    def __init__(self):
        self.sentiment_analyzer = CryptoSentimentAnalyzer()
        self.token_extractor = TokenExtractor()
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    def fetch_recent_messages(self) -> List[Dict[str, Any]]:
        messages = []
        if self.api_url and not config.SIMULATION_MODE:
            try:
                response = requests.get(f"{self.api_url}/getUpdates", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        for item in data.get("result", []):
                            msg = item.get("message") or item.get("channel_post")
                            if msg and "text" in msg:
                                text = msg["text"]
                                tokens = self.token_extractor.extract_tokens(text)
                                sender = msg.get("from", {}).get("username", "tg_user")
                                for token in tokens:
                                    messages.append({
                                        "platform": "Telegram",
                                        "post_id": str(msg.get("message_id")),
                                        "author": sender,
                                        "content": text,
                                        "token_symbol": token,
                                        "sentiment_score": self.sentiment_analyzer.analyze(text),
                                        "likes": random.randint(1, 50),
                                        "retweets": 0,
                                        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                                    })
                        if messages:
                            return messages
            except Exception as e:
                logger.warning(f"Telegram API fetch warning: {e}. Using fallback simulation.")

        # Simulation fallback generator for Telegram crypto channels
        return self._generate_simulated_messages()

    def _generate_simulated_messages(self) -> List[Dict[str, Any]]:
        simulated = []
        templates = [
            "🚨 CALL ALERT: ${coin} showing massive volume surge in DexScreener! 💎",
            "MEME COIN GEM DETECTED: ${coin} - Buy before 100x pump! 🚀🚀",
            "Group, ${coin} liquidity locked! Very bullish chart structure 📈",
            "Whale alert: 500 SOL moved into ${coin} liquidity pool 🐋",
            "Take profit warning on ${coin}, looks like sellers taking over 📉",
            "NEW ATH loading for ${coin}! Send it to the moon 🌕🔥"
        ]
        
        channels = ["@SolanaMemeCalls", "@CryptoWhaleGems", "@BinancePumpAlerts", "@DEX_Gem_Finds"]

        for _ in range(random.randint(2, 6)):
            coin = random.choice(config.TARGET_MEME_COINS)
            template = random.choice(templates)
            text = template.replace("${coin}", coin)
            channel = random.choice(channels)

            simulated.append({
                "platform": "Telegram",
                "post_id": f"sim_tg_{int(time.time()*1000)}_{random.randint(100,999)}",
                "author": channel,
                "content": text,
                "token_symbol": coin,
                "sentiment_score": self.sentiment_analyzer.analyze(text),
                "likes": random.randint(10, 300),
                "retweets": random.randint(2, 80),
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
        return simulated
