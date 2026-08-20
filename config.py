import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Twitter Credentials
TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY", "")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# Telegram Credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Database Config
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "crypto_meme_bot.db"))

# Execution Parameters
PORT = int(os.getenv("PORT", "3000"))
FETCH_INTERVAL_SECONDS = int(os.getenv("FETCH_INTERVAL_SECONDS", "60"))
ENABLE_SIMULATION_FALLBACK = os.getenv("ENABLE_SIMULATION_FALLBACK", "true").lower() == "true"
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "true").lower() == "true"

# Monitored Meme Coins Target Keywords & Tickers
TARGET_MEME_COINS = [
    "DOGE", "PEPE", "WIF", "SHIB", "BONK", 
    "FLOKI", "POPCAT", "BRETT", "MEW", "BOME",
    "MOG", "NEIRO", "MYRO", "SLERF", "TURBO"
]

# Sentiment Lexicon Additions for Crypto Meme Slang
CRYPTO_LEXICON = {
    "moon": 3.0,
    "bullish": 2.5,
    "100x": 3.5,
    "1000x": 4.0,
    "gem": 2.5,
    "lfg": 2.8,
    "pump": 2.0,
    "breakout": 2.2,
    "buy": 1.5,
    "hold": 1.5,
    "hodl": 2.0,
    "wagmi": 2.5,
    "ath": 2.0,
    "dump": -3.0,
    "rug": -4.0,
    "scam": -3.5,
    "bearish": -2.5,
    "ngmi": -2.5,
    "sell": -1.5,
    "drop": -2.0
}
