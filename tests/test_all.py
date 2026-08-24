import unittest
import os
import sys
import shutil
import tempfile

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from ingestion.database import DatabaseManager
from engine.token_extractor import TokenExtractor
from engine.sentiment_analyzer import CryptoSentimentAnalyzer
from engine.feature_pipeline import FeaturePipeline
from ml.model_manager import MemeCoinMLManager
from ml.continuous_learner import ContinuousLearner

from engine.historical_analyzer import HistoricalPatternAnalyzer

class TestMemeCoinBot(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_bot.db")
        self.db = DatabaseManager(self.db_path)
        self.token_extractor = TokenExtractor(target_coins=["DOGE", "PEPE", "WIF"])
        self.sentiment = CryptoSentimentAnalyzer()
        self.feature_pipeline = FeaturePipeline(self.db)
        self.ml = MemeCoinMLManager(model_dir=os.path.join(self.test_dir, "models"))
        self.hist_analyzer = HistoricalPatternAnalyzer()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_token_extraction(self):
        text = "Check out $DOGE and #PEPE to the moon! Is WIF pump incoming?"
        tokens = self.token_extractor.extract_tokens(text)
        self.assertIn("DOGE", tokens)
        self.assertIn("PEPE", tokens)
        self.assertIn("WIF", tokens)

    def test_sentiment_analysis(self):
        bullish_text = "BULLISH on $DOGE, 100x gem to the moon LFG!"
        bearish_text = "Scam dump incoming, sell immediately!"
        
        score_bull = self.sentiment.analyze(bullish_text)
        score_bear = self.sentiment.analyze(bearish_text)

        self.assertGreater(score_bull, 0.3)
        self.assertLess(score_bear, -0.3)

    def test_db_and_feature_pipeline(self):
        # Insert test posts
        self.db.insert_post("X", "1", "trader1", "DOGE to the moon 🚀", "DOGE", sentiment_score=0.8, likes=50, retweets=10)
        self.db.insert_post("Telegram", "2", "trader2", "$DOGE massive volume pump!", "DOGE", sentiment_score=0.7, likes=20, retweets=5)

        features = self.feature_pipeline.compute_token_features("DOGE")
        
        self.assertEqual(features["post_count_1h"], 2)
        self.assertGreater(features["avg_sentiment"], 0.5)
        self.assertEqual(features["unique_authors_1h"], 2)

    def test_ml_prediction_and_online_learning(self):
        features = {
            "post_count_1h": 25,
            "post_count_24h": 100,
            "volume_velocity": 1.5,
            "avg_sentiment": 0.65,
            "bullish_ratio": 0.8,
            "unique_authors_1h": 18,
            "total_engagement_1h": 400,
            "social_reach_score": 115.0,
            "x_ratio": 0.6
        }

        pump_score, confidence, rec = self.ml.predict(features)
        self.assertTrue(0.0 <= pump_score <= 1.0)
        self.assertTrue(0.0 <= confidence <= 1.0)
        self.assertIn(rec, ["STRONG BUY 🚀", "BULLISH 📈", "NEUTRAL ⚡", "BEARISH 📉"])

        # Test continuous online learning update
        initial_samples = self.ml.samples_seen
        self.ml.update_online(features, actual_label=1)
        self.assertEqual(self.ml.samples_seen, initial_samples + 1)

    def test_historical_pattern_analysis(self):
        features_bullish = {
            "post_count_1h": 20,
            "post_count_24h": 150,
            "volume_velocity": 1.8,
            "avg_sentiment": 0.55,
            "bullish_ratio": 0.85
        }
        res = self.hist_analyzer.evaluate_token(features_bullish, pump_score=85.0)
        self.assertIn("+100%+", res["target_gain"])
        self.assertEqual(res["timeframe"], "1 - 2 Minggu Ke Depan")
        self.assertIn("Sangat Bullish", res["keterangan_awam"])

if __name__ == "__main__":
    unittest.main()
