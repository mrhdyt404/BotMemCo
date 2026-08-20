import time
import logging
import threading
import uvicorn
from datetime import datetime
import config
from ingestion.database import DatabaseManager
from ingestion.data_collector import DataCollector
from engine.feature_pipeline import FeaturePipeline
from ml.model_manager import MemeCoinMLManager
from ml.continuous_learner import ContinuousLearner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("MemeBotMain")

class MemeCoinBot:
    def __init__(self):
        self.db = DatabaseManager()
        self.collector = DataCollector(self.db)
        self.features = FeaturePipeline(self.db)
        self.ml = MemeCoinMLManager()
        self.learner = ContinuousLearner(self.db, self.ml)
        self.is_running = False

    def run_ingestion_cycle(self):
        logger.info("--- Starting Social Data Ingestion Cycle ---")
        posts = self.collector.collect_and_store()
        logger.info(f"Collected {len(posts)} posts from X & Telegram.")

        # Compute & store updated features for all monitored meme coins
        logger.info("Computing time-series features & generating ML predictions...")
        for token in config.TARGET_MEME_COINS:
            feat = self.features.compute_token_features(token)
            score, conf, rec = self.ml.predict(feat)
            self.db.insert_prediction(
                token_symbol=token,
                pump_score=score,
                confidence=conf,
                recommendation=rec,
                features=feat
            )

    def run_learning_cycle(self):
        logger.info("--- Starting Continuous ML Self-Learning Loop ---")
        self.learner.evaluate_and_learn()

    def start_background_loop(self):
        self.is_running = True
        logger.info(f"Background Loop Started. Scraping X & Telegram every {config.FETCH_INTERVAL_SECONDS} seconds.")
        
        cycle_count = 0
        while self.is_running:
            try:
                self.run_ingestion_cycle()
                cycle_count += 1
                
                # Every 2 cycles, run continuous self-learning evaluation
                if cycle_count % 2 == 0:
                    self.run_learning_cycle()

            except Exception as e:
                logger.error(f"Error in background bot loop: {e}", exc_info=True)

            time.sleep(config.FETCH_INTERVAL_SECONDS)

def find_available_port(start_port: int = 3000, max_attempts: int = 20) -> int:
    import socket
    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', p))
                return p
            except OSError:
                continue
    return start_port

def start_dashboard():
    port = find_available_port(config.PORT)
    logger.info(f"Starting Web Dashboard on http://127.0.0.1:{port}")
    uvicorn.run("dashboard.app:app", host="127.0.0.1", port=port, log_level="warning")

if __name__ == "__main__":
    bot = MemeCoinBot()

    # Initial seed ingestion so DB has data immediately upon launch
    bot.run_ingestion_cycle()

    # Start background loop in worker thread
    bg_thread = threading.Thread(target=bot.start_background_loop, daemon=True)
    bg_thread.start()

    # Run FastAPI web dashboard on main thread
    start_dashboard()
