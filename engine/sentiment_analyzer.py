import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import config

logger = logging.getLogger(__name__)

class CryptoSentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        # Add custom crypto slang terms to VADER lexicon
        self.analyzer.lexicon.update(config.CRYPTO_LEXICON)

    def analyze(self, text: str) -> float:
        """
        Analyzes post text and returns a compound sentiment score from -1.0 (extremely bearish) to +1.0 (extremely bullish).
        """
        if not text:
            return 0.0
        
        try:
            scores = self.analyzer.polarity_scores(text)
            return scores.get("compound", 0.0)
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 0.0

    def is_bullish(self, text: str, threshold: float = 0.15) -> bool:
        return self.analyze(text) >= threshold
