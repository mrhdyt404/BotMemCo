import os
import pickle
import logging
from typing import Dict, Any, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
import config

logger = logging.getLogger(__name__)

FEATURE_KEYS = [
    "post_count_1h",
    "post_count_24h",
    "volume_velocity",
    "avg_sentiment",
    "bullish_ratio",
    "unique_authors_1h",
    "total_engagement_1h",
    "social_reach_score",
    "x_ratio"
]

class MemeCoinMLManager:
    def __init__(self, model_dir: str = None):
        self.model_dir = model_dir or os.path.join(config.BASE_DIR, "models")
        os.makedirs(self.model_dir, exist_ok=True)
        self.model_file = os.path.join(self.model_dir, "meme_predictor.pkl")
        
        self.scaler = StandardScaler()
        # Online incremental model (SGD with log_loss supports probability estimates)
        self.online_model = SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, random_state=42)
        # Ensemble batch model
        self.batch_model = RandomForestClassifier(n_estimators=50, random_state=42)
        
        self.is_scaler_fitted = False
        self.is_online_fitted = False
        self.is_batch_fitted = False
        self.samples_seen = 0

        self._load_or_init_models()

    def _extract_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        vector = []
        for key in FEATURE_KEYS:
            vector.append(float(features.get(key, 0.0)))
        return np.array(vector).reshape(1, -1)

    def _load_or_init_models(self):
        if os.path.exists(self.model_file):
            try:
                with open(self.model_file, "rb") as f:
                    state = pickle.load(f)
                    self.scaler = state["scaler"]
                    self.online_model = state["online_model"]
                    self.batch_model = state["batch_model"]
                    self.is_scaler_fitted = state.get("is_scaler_fitted", False)
                    self.is_online_fitted = state.get("is_online_fitted", False)
                    self.is_batch_fitted = state.get("is_batch_fitted", False)
                    self.samples_seen = state.get("samples_seen", 0)
                logger.info(f"Loaded existing ML model trained on {self.samples_seen} samples.")
                return
            except Exception as e:
                logger.warning(f"Failed to load model file: {e}. Reinitializing.")

        # Initialize with synthetic bootstrap dataset so model works out-of-the-box
        self._bootstrap_initial_model()

    def _bootstrap_initial_model(self):
        """
        Creates an initial synthetic training baseline so the model can predict immediately.
        """
        logger.info("Bootstrapping baseline ML model with crypto meme heuristics...")
        X_dummy = []
        y_dummy = []

        for _ in range(300):
            p1h = np.random.randint(0, 100)
            p24h = p1h * np.random.randint(1, 20)
            velocity = np.random.uniform(-0.5, 3.0)
            sentiment = np.random.uniform(-0.8, 0.9)
            bullish_ratio = np.random.uniform(0.0, 1.0)
            authors = max(1, int(p1h * np.random.uniform(0.3, 0.9)))
            engagement = int(p1h * np.random.uniform(2, 20))
            reach = (p1h * 1.5) + (authors * 2.0) + (engagement * 0.1)
            x_ratio = np.random.uniform(0.2, 0.8)

            vec = [p1h, p24h, velocity, sentiment, bullish_ratio, authors, engagement, reach, x_ratio]
            X_dummy.append(vec)

            # Heuristic pump condition: High velocity + high bullish sentiment + high post count
            is_pump = 1 if (velocity > 0.8 and sentiment > 0.3 and p1h > 15 and bullish_ratio > 0.6) else 0
            y_dummy.append(is_pump)

        X_arr = np.array(X_dummy)
        y_arr = np.array(y_dummy)

        self.scaler.fit(X_arr)
        self.is_scaler_fitted = True

        X_scaled = self.scaler.transform(X_arr)
        self.online_model.partial_fit(X_scaled, y_arr, classes=np.array([0, 1]))
        self.is_online_fitted = True

        self.batch_model.fit(X_scaled, y_arr)
        self.is_batch_fitted = True

        self.samples_seen = len(y_dummy)
        self.save_model()

    def predict(self, features: Dict[str, Any]) -> Tuple[float, float, str]:
        """
        Returns (pump_score, confidence, recommendation)
        pump_score is between 0.0 (0%) and 1.0 (100%).
        """
        vector = self._extract_feature_vector(features)
        
        if not self.is_scaler_fitted:
            self.scaler.fit(vector)
            self.is_scaler_fitted = True

        scaled_vec = self.scaler.transform(vector)

        # Get probabilities from ensemble batch model and online model
        probs_batch = self.batch_model.predict_proba(scaled_vec)[0] if self.is_batch_fitted else [0.5, 0.5]
        probs_online = self.online_model.predict_proba(scaled_vec)[0] if self.is_online_fitted else [0.5, 0.5]

        # Combine ensemble (70% weight batch, 30% weight online)
        pump_prob = float((probs_batch[1] * 0.7) + (probs_online[1] * 0.3))
        pump_prob = max(0.01, min(0.99, pump_prob))

        # Confidence metric based on model agreement
        agreement = 1.0 - abs(probs_batch[1] - probs_online[1])
        confidence = float(round(0.70 + (agreement * 0.25), 2))

        if pump_prob >= 0.75:
            recommendation = "STRONG BUY 🚀"
        elif pump_prob >= 0.55:
            recommendation = "BULLISH 📈"
        elif pump_prob >= 0.40:
            recommendation = "NEUTRAL ⚡"
        else:
            recommendation = "BEARISH 📉"

        return round(pump_prob, 4), confidence, recommendation

    def update_online(self, features: Dict[str, Any], actual_label: int):
        """
        Incremental learning method (partial_fit). Called when new ground-truth arrives.
        """
        vector = self._extract_feature_vector(features)
        if not self.is_scaler_fitted:
            self.scaler.fit(vector)
            self.is_scaler_fitted = True
            
        scaled_vec = self.scaler.transform(vector)
        self.online_model.partial_fit(scaled_vec, [actual_label], classes=np.array([0, 1]))
        self.is_online_fitted = True
        self.samples_seen += 1
        
        logger.info(f"ML Model online updated with sample label={actual_label}. Total samples: {self.samples_seen}")

    def retrain_full(self, X_data: np.ndarray, y_data: np.ndarray):
        """
        Full batch retraining on collected historical database records.
        """
        if len(y_data) < 10:
            logger.info("Not enough data points for full retrain yet.")
            return

        self.scaler.fit(X_data)
        X_scaled = self.scaler.transform(X_data)
        
        self.batch_model.fit(X_scaled, y_data)
        self.is_batch_fitted = True

        self.online_model.partial_fit(X_scaled, y_data, classes=np.array([0, 1]))
        self.samples_seen += len(y_data)
        
        self.save_model()
        logger.info(f"Full retraining finished on {len(y_data)} samples.")

    def save_model(self):
        state = {
            "scaler": self.scaler,
            "online_model": self.online_model,
            "batch_model": self.batch_model,
            "is_scaler_fitted": self.is_scaler_fitted,
            "is_online_fitted": self.is_online_fitted,
            "is_batch_fitted": self.is_batch_fitted,
            "samples_seen": self.samples_seen
        }
        with open(self.model_file, "wb") as f:
            pickle.dump(state, f)
