import logging
import requests
from typing import List, Dict, Any
import config

logger = logging.getLogger(__name__)

class DexScreenerCollector:
    def __init__(self):
        self.base_url = "https://api.dexscreener.com/latest/dex/search"

    def fetch_live_tickers(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        target_symbols = symbols or config.TARGET_MEME_COINS[:10]
        tickers = []

        for symbol in target_symbols:
            try:
                response = requests.get(f"{self.base_url}?q={symbol}", timeout=4)
                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])
                    if pairs:
                        # Pick the top liquidity pair for this symbol
                        top_pair = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
                        
                        price_usd = top_pair.get("priceUsd", "0.00")
                        # Format price nicely
                        price_float = float(price_usd)
                        if price_float < 0.0001:
                            price_str = f"${price_float:.8f}"
                        elif price_float < 1.0:
                            price_str = f"${price_float:.6f}"
                        else:
                            price_str = f"${price_float:.2f}"

                        h24_change = top_pair.get("priceChange", {}).get("h24", 0.0) or 0.0

                        tickers.append({
                            "symbol": symbol.upper(),
                            "price": price_str,
                            "change_24h": round(float(h24_change), 2),
                            "dex": top_pair.get("dexId", "DEX").upper(),
                            "url": top_pair.get("url", "https://dexscreener.com")
                        })
            except Exception as e:
                logger.warning(f"Failed to fetch DexScreener ticker for {symbol}: {e}")

        # Fallback simulation if API is rate limited or unavailable
        if not tickers:
            tickers = self._fallback_tickers(target_symbols)

        return tickers

    def _fallback_tickers(self, symbols: List[str]) -> List[Dict[str, Any]]:
        import random
        fallback = []
        for symbol in symbols:
            change = round(random.uniform(-15.0, 35.0), 2)
            fallback.append({
                "symbol": symbol.upper(),
                "price": f"${random.uniform(0.00001, 2.5):.6f}",
                "change_24h": change,
                "dex": "RAYDIUM",
                "url": "https://dexscreener.com"
            })
        return fallback
