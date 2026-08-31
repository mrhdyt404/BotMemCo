import time
import logging
import threading

import config
from ingestion.database import DatabaseManager
from ingestion.data_collector import DataCollector
from engine.feature_pipeline import FeaturePipeline
from ml.model_manager import MemeCoinMLManager
from ml.continuous_learner import ContinuousLearner


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MemeBotMain")


# ============================================================
# MEMECOIN BOT
# ============================================================

class MemeCoinBot:

    def __init__(self):

        logger.info("Initializing MemeCoinBot...")

        self.db = DatabaseManager()

        self.collector = DataCollector(
            self.db
        )

        self.features = FeaturePipeline(
            self.db
        )

        self.ml = MemeCoinMLManager()

        self.learner = ContinuousLearner(
            self.db,
            self.ml
        )

        self.is_running = False

        logger.info(
            "MemeCoinBot initialized successfully."
        )

    # ========================================================
    # INGESTION
    # ========================================================

    def run_ingestion_cycle(self):

        logger.info(
            "--- Starting Social Data Ingestion Cycle ---"
        )

        try:

            posts = self.collector.collect_and_store()

            logger.info(
                f"Collected {len(posts)} posts "
                f"from X & Telegram."
            )

        except Exception as e:

            # ------------------------------------------------
            # IMPORTANT:
            # Failure in external API must NOT stop bot.
            # ------------------------------------------------

            logger.error(
                f"Social ingestion failed: {e}",
                exc_info=True
            )

            return

        # ----------------------------------------------------
        # FEATURES + ML
        # ----------------------------------------------------

        logger.info(
            "Computing time-series features "
            "& generating ML predictions..."
        )

        for token in config.TARGET_MEME_COINS:

            try:

                feat = (
                    self.features
                    .compute_token_features(token)
                )

                score, conf, rec = (
                    self.ml.predict(feat)
                )

                self.db.insert_prediction(
                    token_symbol=token,
                    pump_score=score,
                    confidence=conf,
                    recommendation=rec,
                    features=feat
                )

                logger.info(
                    f"{token}: "
                    f"score={score:.2f}, "
                    f"confidence={conf:.2f}, "
                    f"recommendation={rec}"
                )

            except Exception as e:

                logger.error(
                    f"Failed processing "
                    f"{token}: {e}",
                    exc_info=True
                )

                # Continue with next token
                continue

    # ========================================================
    # CONTINUOUS LEARNING
    # ========================================================

    def run_learning_cycle(self):

        logger.info(
            "--- Starting Continuous ML "
            "Self-Learning Loop ---"
        )

        try:

            self.learner.evaluate_and_learn()

        except Exception as e:

            logger.error(
                f"Continuous learning failed: {e}",
                exc_info=True
            )

    # ========================================================
    # BACKGROUND LOOP
    # ========================================================

    def start_background_loop(self):

        self.is_running = True

        logger.info(
            "Background Loop Started. "
            f"Fetching data every "
            f"{config.FETCH_INTERVAL_SECONDS} seconds."
        )

        cycle_count = 0

        while self.is_running:

            try:

                # ------------------------------------------------
                # INGESTION
                # ------------------------------------------------

                self.run_ingestion_cycle()

                cycle_count += 1

                # ------------------------------------------------
                # ML LEARNING EVERY 2 CYCLES
                # ------------------------------------------------

                if cycle_count % 2 == 0:

                    self.run_learning_cycle()

            except Exception as e:

                logger.error(
                    f"Error in background bot loop: {e}",
                    exc_info=True
                )

            # ----------------------------------------------------
            # WAIT
            # ----------------------------------------------------

            time.sleep(
                config.FETCH_INTERVAL_SECONDS
            )

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        logger.info(
            "Stopping MemeCoinBot..."
        )

        self.is_running = False


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    logger.info(
        "========================================"
    )

    logger.info(
        "      MemeCoin Bot Starting"
    )

    logger.info(
        "========================================"
    )

    bot = MemeCoinBot()

    # --------------------------------------------------------
    # Initial ingestion
    # --------------------------------------------------------

    try:

        logger.info(
            "Running initial ingestion cycle..."
        )

        bot.run_ingestion_cycle()

    except Exception as e:

        logger.error(
            f"Initial ingestion failed: {e}",
            exc_info=True
        )

    # --------------------------------------------------------
    # Background worker
    # --------------------------------------------------------

    bg_thread = threading.Thread(
        target=bot.start_background_loop,
        name="MemeCoinBackgroundWorker",
        daemon=True
    )

    bg_thread.start()

    logger.info(
        "Background worker started."
    )

    def start_web_server():
        import uvicorn
        host = getattr(config, "HOST", "127.0.0.1")
        port = getattr(config, "PORT", 3000)
        uvicorn.run("dashboard.app:app", host=host, port=port, log_level="warning")

    web_thread = threading.Thread(target=start_web_server, name="MemeCoinWebServer", daemon=True)
    web_thread.start()
    logger.info(f"Web Dashboard started on http://{getattr(config, 'HOST', '127.0.0.1')}:{getattr(config, 'PORT', 3000)}")

    try:
        while True:
            time.sleep(60)

    except KeyboardInterrupt:

        logger.info(
            "KeyboardInterrupt received."
        )

        bot.stop()

        logger.info(
            "MemeCoin Bot stopped."
        )