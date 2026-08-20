import logging
import json
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from ingestion.database import DatabaseManager
from ml.model_manager import MemeCoinMLManager, FEATURE_KEYS

logger = logging.getLogger(__name__)

class ContinuousLearner:
    def __init__(self, db_manager: DatabaseManager = None, ml_manager: MemeCoinMLManager = None):
        self.db = db_manager or DatabaseManager()
        self.ml = ml_manager or MemeCoinMLManager()

    def evaluate_and_learn(self):
        """
        Scans recent predictions that haven't been feedback-labeled yet,
        evaluates actual post volume outcome over time, and updates ML model.
        """
        logger.info("Executing continuous learning feedback loop...")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Fetch predictions older than 1 minute that don't have feedback labels yet
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                SELECT p.* 
                FROM predictions p
                LEFT JOIN feedback_labels fl ON p.id = fl.prediction_id
                WHERE fl.id IS NULL AND p.timestamp <= ?
                ORDER BY p.timestamp ASC
                LIMIT 30
            """, (cutoff,))
            unlabeled = [dict(row) for row in cursor.fetchall()]

        if not unlabeled:
            logger.info("No new predictions pending feedback label evaluation.")
            return

        updated_count = 0
        correct_count = 0

        for pred in unlabeled:
            token = pred["token_symbol"]
            pred_score = pred["pump_score"]
            pred_id = pred["id"]
            
            try:
                features = json.loads(pred["features_json"])
            except Exception:
                continue

            # Evaluate outcome: check if token volume velocity and sentiment stayed strong or grew
            h1_cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as post_cnt, AVG(sentiment_score) as avg_sent
                    FROM posts
                    WHERE token_symbol = ? AND created_at >= ?
                """, (token, h1_cutoff))
                res = cursor.fetchone()
                recent_cnt = res["post_cnt"] or 0
                recent_sent = res["avg_sent"] or 0.0

            # Outcome criterion: Volume > 10 and positive sentiment -> Pump (1), else (0)
            actual_pump = 1 if (recent_cnt >= 8 and recent_sent > 0.1) else 0
            actual_vol_change = float(recent_cnt - features.get("post_count_1h", 0))

            # Store label in DB
            self.db.insert_feedback_label(
                token_symbol=token,
                prediction_id=pred_id,
                predicted_score=pred_score,
                actual_pump_outcome=actual_pump,
                actual_volume_change=actual_vol_change
            )

            # Online continuous learning update
            self.ml.update_online(features, actual_pump)
            updated_count += 1

            # Metric evaluation
            predicted_binary = 1 if pred_score >= 0.55 else 0
            if predicted_binary == actual_pump:
                correct_count += 1

        if updated_count > 0:
            accuracy = round((correct_count / updated_count) * 100, 2)
            version = f"v1.{self.ml.samples_seen}"
            notes = f"Continuous online update on {updated_count} predictions. Batch accuracy: {accuracy}%"
            self.db.log_model_update(version=version, accuracy=accuracy, samples_trained=self.ml.samples_seen, notes=notes)
            self.ml.save_model()
            logger.info(f"Continuous Learning Cycle Complete: {notes}")

    def trigger_batch_retrain(self):
        """
        Retrains full ensemble model using historical dataset stored in DB.
        """
        training_records = self.db.get_training_data()
        if len(training_records) < 10:
            return

        X_list = []
        y_list = []

        for rec in training_records:
            features = rec.get("features", {})
            vec = [float(features.get(k, 0.0)) for k in FEATURE_KEYS]
            X_list.append(vec)
            y_list.append(rec["actual_pump_outcome"])

        X_arr = np.array(X_list)
        y_arr = np.array(y_list)

        self.ml.retrain_full(X_arr, y_arr)
