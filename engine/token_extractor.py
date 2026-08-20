import re
from typing import List, Set
import config

class TokenExtractor:
    def __init__(self, target_coins: List[str] = None):
        self.target_coins = [coin.upper() for coin in (target_coins or config.TARGET_MEME_COINS)]
        # Regex for $CASHTAG (e.g. $DOGE) or #HASHTAG (e.g. #PEPE) or standalone ticker symbols
        self.cashtag_pattern = re.compile(r'\$([A-Za-z0-9_]{2,10})')
        self.hashtag_pattern = re.compile(r'#([A-Za-z0-9_]{2,10})')

    def extract_tokens(self, text: str) -> List[str]:
        if not text:
            return []
        
        found_tokens: Set[str] = set()
        text_upper = text.upper()

        # Extract cashtags
        for match in self.cashtag_pattern.findall(text):
            symbol = match.upper()
            if symbol in self.target_coins:
                found_tokens.add(symbol)

        # Extract hashtags
        for match in self.hashtag_pattern.findall(text):
            symbol = match.upper()
            if symbol in self.target_coins:
                found_tokens.add(symbol)

        # Extract direct word matches
        words = set(re.findall(r'\b[A-Z0-9]{2,10}\b', text_upper))
        for token in self.target_coins:
            if token in words or f"${token}" in text_upper or f"#{token}" in text_upper:
                found_tokens.add(token)

        return list(found_tokens)
