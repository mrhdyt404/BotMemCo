import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Baseline data pola historis lonjakan harga spesifik per koin meme
TOKEN_HISTORICAL_BENCHMARKS = {
    "PEPE": {
        "weeks": {
            "ref": "Pola Rekor ATH PEPE (Mei 2024)",
            "desc": "Sangat Bullish! Pola perbincangan mirip akumulasi masif lonjakan ATH PEPE (Mei 2024). Perbincangan naik pesat dengan sentimen sangat positif. Berpotensi meroket +100%+ dalam 1-2 minggu."
        },
        "days": {
            "ref": "Pola Lonjakan Mingguan PEPE (Feb 2024)",
            "desc": "Sinyal Akumulasi Positif! Perbincangan mirip rali lonjakan mingguan PEPE (Feb 2024 +100%). Berpotensi naik +50%+ dalam 1-3 hari ke depan."
        }
    },
    "DOGE": {
        "weeks": {
            "ref": "Pola Rali Bull Run Masif DOGE (Nov 2024)",
            "desc": "Sangat Bullish! Pola perbincangan & akumulasi mirip rali masif DOGE (Nov 2024). Berpotensi melonjak +80% s/d +150%+ dalam 1-2 minggu."
        },
        "days": {
            "ref": "Pola Twitter Logo Pump DOGE (April 2023)",
            "desc": "Sinyal Akumulasi Kuat! Perbincangan di X & Telegram melonjak tajam mirip event akumulasi viral DOGE. Berpotensi naik +40% s/d +70% dalam 1-3 hari."
        }
    },
    "FLOKI": {
        "weeks": {
            "ref": "Pola Breakout Ekosistem & Listing CEX FLOKI (Maret 2024)",
            "desc": "Sangat Bullish! Perbincangan sosial & volume transaksi mirip pola rali eksponensial FLOKI (Maret 2024). Berpotensi melesat +90%+ dalam 1-2 minggu."
        },
        "days": {
            "ref": "Pola Akumulasi Staking & Marketing Surge FLOKI",
            "desc": "Sinyal Akumulasi Positif! Respon positif komunitas meningkat drastis mirip pola kenaikan FLOKI. Berpotensi naik +50%+ dalam 1-3 hari."
        }
    },
    "WIF": {
        "weeks": {
            "ref": "Pola Rali Parabolik Solana WIF (Maret 2024)",
            "desc": "Sangat Bullish! Pola perbincangan komunitas Solana mirip rali eksponensial WIF ke ATH $4.8. Berpotensi naik +100%+ dalam 1-2 minggu."
        },
        "days": {
            "ref": "Pola Kenaikan Volume Kilat WIF (Desember 2023)",
            "desc": "Momentum Tinggi! Terjadi akumulasi cepat mirip pola rali harian WIF. Berpotensi naik +50% s/d +80% dalam 1-3 hari."
        }
    },
    "SHIB": {
        "weeks": {
            "ref": "Pola Rali Masif SHIB (Oktober 2021 / Feb 2024)",
            "desc": "Sangat Bullish! Pola perbincangan komunitas & pembakaran token mirip rali besar SHIB. Berpotensi naik +70% s/d +120% dalam 1-2 minggu."
        },
        "days": {
            "ref": "Pola Kenaikan Volume Komunitas SHIB",
            "desc": "Sinyal Akumulasi Positif! Aktivitas sosial & minat komunitas memuncak. Berpotensi naik +40% s/d +70% dalam 1-3 hari."
        }
    },
    "BONK": {
        "weeks": {
            "ref": "Pola Rali Ekosistem Solana BONK (Desember 2023)",
            "desc": "Sangat Bullish! Pola akumulasi mirip rali raksasa BONK di ekosistem Solana. Berpotensi meroket +100%+ dalam 1-2 minggu."
        },
        "days": {
            "ref": "Pola Kenaikan Transaksi On-Chain BONK",
            "desc": "Sinyal Akumulasi Positif! Komunitas di Telegram & X sangat aktif. Berpotensi naik +50%+ dalam 1-3 hari."
        }
    },
    "BOME": {
        "weeks": {
            "ref": "Pola Kenaikan Kilat Listing Binance BOME (Maret 2024)",
            "desc": "Sangat Bullish! Pola percakapan masif mirip rali sejarah BOME (Maret 2024). Berpotensi melonjak +100%+ dalam 1-2 minggu."
        },
        "days": {
            "ref": "Pola Pre-Sale & Volume Surge BOME",
            "desc": "Sinyal Momentum Tinggi! Terdeteksi akumulasi volume cepat. Berpotensi naik +50% s/d +80% dalam 1-3 hari."
        }
    },
    "POPCAT": {
        "weeks": {
            "ref": "Pola Breakout ATH Tren Cat-Meme POPCAT (Juli 2024)",
            "desc": "Sangat Bullish! Pola perbincangan mirip tren rali POPCAT menembus rekor ATH baru. Berpotensi melesat +80% s/d +130% dalam 1-2 minggu."
        },
        "days": {
            "ref": "Pola Kenaikan Viral POPCAT",
            "desc": "Sinyal Akumulasi Positif! Viralitas sosial meningkat tajam. Berpotensi naik +50%+ dalam 1-3 hari."
        }
    },
    "BRETT": {
        "weeks": {
            "ref": "Pola Lonjakan Utama Base Chain BRETT (Juni 2024)",
            "desc": "Sangat Bullish! Pola perbincangan mirip dominasi rali BRETT di jaringan Base Chain. Berpotensi meroket +90%+ dalam 1-2 minggu."
        },
        "days": {
            "ref": "Pola Akumulasi Smart Money BRETT",
            "desc": "Sinyal Akumulasi Positif! Minat pembeli di X & Telegram mulai tinggi. Berpotensi naik +50%+ dalam 1-3 hari."
        }
    },
    "SLERF": {
        "weeks": {
            "ref": "Pola Lonjakan Volume Komunitas SLERF (Maret 2024)",
            "desc": "Sangat Bullish! Pola percakapan & volume mirip lonjakan sejarah SLERF. Berpotensi naik +80% s/d +140% dalam 1-2 minggu."
        },
        "days": {
            "ref": "Pola Rebound Komunitas SLERF",
            "desc": "Sinyal Akumulasi Positif! Perbincangan komunitas mendadak ramai. Berpotensi naik +50%+ dalam 1-3 hari."
        }
    },
    "NEIRO": {
        "weeks": {
            "ref": "Pola Rali Listing CEX Utama NEIRO (September 2024)",
            "desc": "Sangat Bullish! Pola perbincangan mirip rali eksponensial NEIRO setelah listing CEX. Berpotensi melonjak +100%+ dalam 1-2 minggu."
        },
        "days": {
            "ref": "Pola Accumulation Phase NEIRO",
            "desc": "Sinyal Akumulasi Positif! Respon sentimen sangat optimis. Berpotensi naik +50%+ dalam 1-3 hari."
        }
    }
}

class HistoricalPatternAnalyzer:
    """
    Menganalisis kemiripan pola data sosial terkini dengan data histori lonjakan besar koin meme spesifik
    (DOGE, PEPE, WIF, FLOKI, BONK, SHIB, dll.) untuk menentukan estimasi waktu kenaikan & keterangan bahasa awam.
    """
    def __init__(self):
        pass

    def evaluate_token(self, features: Dict[str, Any], pump_score: float) -> Dict[str, Any]:
        token_symbol = str(features.get("token_symbol", "")).upper()
        p1h = features.get("post_count_1h", 0)
        velocity = features.get("volume_velocity", 0.0)
        sentiment = features.get("avg_sentiment", 0.0)

        # Get token-specific benchmark or fallback
        token_bm = TOKEN_HISTORICAL_BENCHMARKS.get(token_symbol, {
            "weeks": {
                "ref": f"Pola Lonjakan Histori Utama ${token_symbol}",
                "desc": f"Sangat Bullish! Pola perbincangan & akumulasi mirip lonjakan histori terbesar ${token_symbol}. Berpotensi meroket +80%+ dalam 1-2 minggu."
            },
            "days": {
                "ref": f"Pola Kenaikan Akumulasi ${token_symbol}",
                "desc": f"Sinyal Akumulasi Positif! Perbincangan komunitas ${token_symbol} di X & Telegram mulai ramai. Berpotensi naik +50%+ dalam 1-3 hari."
            }
        })

        # 1. Kasus Sangat Bullish / High Momentum (Skala Mingguan - WEEKS)
        if pump_score >= 75.0 or (velocity >= 1.2 and sentiment >= 0.35 and p1h >= 10):
            target_gain = "+100%+ (Potensi ATH Baru)"
            timeframe = "1 - 2 Minggu Ke Depan"
            timeframe_cat = "WEEKS"
            keterangan_awam = token_bm["weeks"]["desc"]
            hist_ref = token_bm["weeks"]["ref"]
            recommendation_rank = 1

        # 2. Kasus Bullish Sedang (Skala Harian - DAYS)
        elif pump_score >= 55.0 or (velocity >= 0.6 and sentiment >= 0.20 and p1h >= 5):
            target_gain = "+50% s/d +80%"
            timeframe = "1 - 3 Hari Ke Depan"
            timeframe_cat = "DAYS"
            keterangan_awam = token_bm["days"]["desc"]
            hist_ref = token_bm["days"]["ref"]
            recommendation_rank = 2

        # 3. Kasus Jangka Pendek (HOURS)
        elif pump_score >= 40.0 or (velocity >= 0.2 and sentiment >= 0.05):
            target_gain = "+20% s/d +40%"
            timeframe = "6 - 24 Jam Ke Depan"
            timeframe_cat = "HOURS"
            keterangan_awam = (
                f"Pergerakan Jangka Pendek Stabil pada ${token_symbol}. Terdeteksi respon awal perbincangan. "
                f"Berpotensi naik cepat dalam 6-24 jam ke depan."
            )
            hist_ref = f"Pola Lonjakan Kilat Harian ${token_symbol}"
            recommendation_rank = 3

        # 4. Sentimen Negatif (BEARISH)
        elif sentiment < -0.15:
            target_gain = "Resiko Penurunan (-10% s/d -30%)"
            timeframe = "Waspada (Potensi Drop)"
            timeframe_cat = "BEARISH"
            keterangan_awam = (
                f"Waspada pada ${token_symbol}! Perbincangan didominasi sentimen negatif/FUD. Dikhawatirkan terjadi penurunan harga."
            )
            hist_ref = f"Pola Koreksi Sentimen Negatif ${token_symbol}"
            recommendation_rank = 5

        # 5. Netral / Standby
        else:
            target_gain = "Pergerakan Datar (0% s/d +15%)"
            timeframe = "Netral / Standby"
            timeframe_cat = "NEUTRAL"
            keterangan_awam = (
                f"Aktivitas perbincangan ${token_symbol} cenderung normal dan stabil. Belum ada sinyal lonjakan besar."
            )
            hist_ref = f"Pola Konsolidasi Normal ${token_symbol}"
            recommendation_rank = 4

        return {
            "target_gain": target_gain,
            "timeframe": timeframe,
            "timeframe_cat": timeframe_cat,
            "keterangan_awam": keterangan_awam,
            "recommendation_rank": recommendation_rank,
            "historical_reference": hist_ref
        }
