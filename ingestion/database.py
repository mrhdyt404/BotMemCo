import sqlite3
import json
import logging
import time

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

import config


logger = logging.getLogger(__name__)


class DatabaseManager:

    # ============================================================
    # CONFIGURATION
    # ============================================================

    SQLITE_TIMEOUT = 30
    SQLITE_BUSY_TIMEOUT_MS = 30000

    MAX_RETRIES = 5
    RETRY_DELAY = 0.5

    # ============================================================
    # INIT
    # ============================================================

    def __init__(self, db_path: str = None):

        self.db_path = db_path or config.DB_PATH

        logger.info(
            f"Initializing SQLite database: {self.db_path}"
        )

        self._init_db()

    # ============================================================
    # CONNECTION
    # ============================================================

    def get_connection(self):

        conn = sqlite3.connect(
            self.db_path,
            timeout=self.SQLITE_TIMEOUT
        )

        conn.row_factory = sqlite3.Row

        # --------------------------------------------------------
        # Enable foreign key constraints
        # --------------------------------------------------------

        conn.execute(
            "PRAGMA foreign_keys = ON"
        )

        # --------------------------------------------------------
        # Wait when database is temporarily locked
        # --------------------------------------------------------

        conn.execute(
            f"PRAGMA busy_timeout = "
            f"{self.SQLITE_BUSY_TIMEOUT_MS}"
        )

        # --------------------------------------------------------
        # WAL mode
        #
        # WAL allows readers and writers to work concurrently
        # much better than the default rollback journal.
        # --------------------------------------------------------

        try:

            conn.execute(
                "PRAGMA journal_mode = WAL"
            )

        except sqlite3.DatabaseError as e:

            logger.warning(
                f"Could not enable SQLite WAL mode: {e}"
            )

        return conn

    # ============================================================
    # SQLITE RETRY HELPER
    # ============================================================

    def _execute_with_retry(
        self,
        operation,
        operation_name: str = "database operation"
    ):

        last_error = None

        for attempt in range(
            1,
            self.MAX_RETRIES + 1
        ):

            try:

                return operation()

            except sqlite3.OperationalError as e:

                last_error = e

                if "locked" not in str(e).lower():
                    raise

                logger.warning(
                    f"SQLite database locked during "
                    f"{operation_name}. "
                    f"Retry {attempt}/"
                    f"{self.MAX_RETRIES}..."
                )

                if attempt < self.MAX_RETRIES:

                    time.sleep(
                        self.RETRY_DELAY * attempt
                    )

        logger.error(
            f"SQLite operation failed after "
            f"{self.MAX_RETRIES} retries: "
            f"{operation_name}"
        )

        raise last_error

    # ============================================================
    # INITIALIZE DATABASE
    # ============================================================

    def _init_db(self):

        def initialize():

            with self.get_connection() as conn:

                cursor = conn.cursor()

                # ------------------------------------------------
                # POSTS
                # ------------------------------------------------

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        platform TEXT NOT NULL,
                        post_id TEXT,
                        author TEXT,
                        content TEXT NOT NULL,
                        token_symbol TEXT NOT NULL,
                        sentiment_score REAL DEFAULT 0.0,
                        likes INTEGER DEFAULT 0,
                        retweets INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # ------------------------------------------------
                # TOKEN METRICS
                # ------------------------------------------------

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS token_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_symbol TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        post_count_1h INTEGER DEFAULT 0,
                        post_count_24h INTEGER DEFAULT 0,
                        volume_velocity REAL DEFAULT 0.0,
                        avg_sentiment REAL DEFAULT 0.0,
                        bullish_ratio REAL DEFAULT 0.0,
                        social_reach_score REAL DEFAULT 0.0
                    )
                """)

                # ------------------------------------------------
                # PREDICTIONS
                # ------------------------------------------------

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_symbol TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        pump_score REAL NOT NULL,
                        confidence REAL DEFAULT 0.0,
                        recommendation TEXT,
                        features_json TEXT
                    )
                """)

                # ------------------------------------------------
                # FEEDBACK LABELS
                # ------------------------------------------------

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS feedback_labels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_symbol TEXT NOT NULL,
                        prediction_id INTEGER,
                        predicted_score REAL,
                        actual_pump_outcome INTEGER NOT NULL,
                        actual_volume_change REAL DEFAULT 0.0,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(prediction_id)
                            REFERENCES predictions(id)
                    )
                """)

                # ------------------------------------------------
                # MODEL LOGS
                # ------------------------------------------------

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS model_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        version TEXT NOT NULL,
                        accuracy REAL,
                        samples_trained INTEGER,
                        notes TEXT
                    )
                """)

                # ------------------------------------------------
                # WISHLIST
                # ------------------------------------------------

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS wishlist (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_symbol TEXT NOT NULL,
                        entry_price REAL DEFAULT 0.0,
                        entry_price_str TEXT DEFAULT '$0.00',
                        pump_score REAL DEFAULT 0.0,
                        recommendation TEXT DEFAULT 'BUY',
                        target_gain TEXT DEFAULT '+50%',
                        target_ratio REAL DEFAULT 1.50,
                        timeframe TEXT DEFAULT '1-3 Hari',
                        timeframe_days INTEGER DEFAULT 3,
                        keterangan_awam TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        target_deadline TIMESTAMP,
                        status TEXT DEFAULT 'PENDING TRACKING ⏱️',
                        highest_price_seen REAL DEFAULT 0.0,
                        actual_gain_percent REAL DEFAULT 0.0,
                        verified_at TIMESTAMP,
                        fed_to_ml INTEGER DEFAULT 0,
                        features_json TEXT
                    )
                """)

                conn.commit()

        self._execute_with_retry(
            initialize,
            "database initialization"
        )

        logger.info(
            "SQLite database initialized successfully."
        )

    # ============================================================
    # INSERT POST
    # ============================================================

    def insert_post(
        self,
        platform: str,
        post_id: str,
        author: str,
        content: str,
        token_symbol: str,
        sentiment_score: float = 0.0,
        likes: int = 0,
        retweets: int = 0,
        created_at: str = None
    ) -> int:

        def operation():

            with self.get_connection() as conn:

                cursor = conn.cursor()

                created_at_value = (
                    created_at
                    or datetime.now(timezone.utc)
                    .strftime("%Y-%m-%d %H:%M:%S")
                )

                cursor.execute("""
                    INSERT INTO posts (
                        platform,
                        post_id,
                        author,
                        content,
                        token_symbol,
                        sentiment_score,
                        likes,
                        retweets,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    platform,
                    post_id,
                    author,
                    content,
                    token_symbol,
                    sentiment_score,
                    likes,
                    retweets,
                    created_at_value
                ))

                conn.commit()

                return cursor.lastrowid

        return self._execute_with_retry(
            operation,
            "insert_post"
        )

    # ============================================================
    # INSERT TOKEN METRIC
    # ============================================================

    def insert_token_metric(
        self,
        metric: Dict[str, Any]
    ) -> int:

        def operation():

            with self.get_connection() as conn:

                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO token_metrics (
                        token_symbol,
                        timestamp,
                        post_count_1h,
                        post_count_24h,
                        volume_velocity,
                        avg_sentiment,
                        bullish_ratio,
                        social_reach_score
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric["token_symbol"],
                    metric.get(
                        "timestamp",
                        datetime.now(timezone.utc)
                        .strftime("%Y-%m-%d %H:%M:%S")
                    ),
                    metric.get("post_count_1h", 0),
                    metric.get("post_count_24h", 0),
                    metric.get("volume_velocity", 0.0),
                    metric.get("avg_sentiment", 0.0),
                    metric.get("bullish_ratio", 0.0),
                    metric.get("social_reach_score", 0.0)
                ))

                conn.commit()

                return cursor.lastrowid

        return self._execute_with_retry(
            operation,
            "insert_token_metric"
        )

    # ============================================================
    # INSERT PREDICTION
    # ============================================================

    def insert_prediction(
        self,
        token_symbol: str,
        pump_score: float,
        confidence: float,
        recommendation: str,
        features: Dict[str, Any]
    ) -> int:

        def operation():

            with self.get_connection() as conn:

                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO predictions (
                        token_symbol,
                        timestamp,
                        pump_score,
                        confidence,
                        recommendation,
                        features_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    token_symbol,
                    datetime.now(timezone.utc)
                    .strftime("%Y-%m-%d %H:%M:%S"),
                    pump_score,
                    confidence,
                    recommendation,
                    json.dumps(
                        features,
                        default=str
                    )
                ))

                conn.commit()

                return cursor.lastrowid

        return self._execute_with_retry(
            operation,
            "insert_prediction"
        )

    # ============================================================
    # INSERT FEEDBACK LABEL
    # ============================================================

    def insert_feedback_label(
        self,
        token_symbol: str,
        prediction_id: Optional[int],
        predicted_score: float,
        actual_pump_outcome: int,
        actual_volume_change: float = 0.0
    ):

        def operation():

            with self.get_connection() as conn:

                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO feedback_labels (
                        token_symbol,
                        prediction_id,
                        predicted_score,
                        actual_pump_outcome,
                        actual_volume_change
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    token_symbol,
                    prediction_id,
                    predicted_score,
                    actual_pump_outcome,
                    actual_volume_change
                ))

                conn.commit()

        return self._execute_with_retry(
            operation,
            "insert_feedback_label"
        )

    # ============================================================
    # MODEL LOG
    # ============================================================

    def log_model_update(
        self,
        version: str,
        accuracy: float,
        samples_trained: int,
        notes: str = ""
    ):

        def operation():

            with self.get_connection() as conn:

                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO model_logs (
                        version,
                        accuracy,
                        samples_trained,
                        notes
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    version,
                    accuracy,
                    samples_trained,
                    notes
                ))

                conn.commit()

        return self._execute_with_retry(
            operation,
            "log_model_update"
        )

    # ============================================================
    # GET RECENT POSTS
    # ============================================================

    def get_recent_posts(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:

        with self.get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT *
                FROM posts
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            return [
                dict(row)
                for row in cursor.fetchall()
            ]

    # ============================================================
    # GET LATEST PREDICTIONS
    # ============================================================

    def get_latest_predictions(
        self
    ) -> List[Dict[str, Any]]:

        with self.get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT p1.*
                FROM predictions p1
                INNER JOIN (
                    SELECT
                        token_symbol,
                        MAX(timestamp) AS max_ts
                    FROM predictions
                    GROUP BY token_symbol
                ) p2
                ON p1.token_symbol = p2.token_symbol
                AND p1.timestamp = p2.max_ts
                ORDER BY p1.pump_score DESC
            """)

            return [
                dict(row)
                for row in cursor.fetchall()
            ]

    # ============================================================
    # GET TRAINING DATA
    # ============================================================

    def get_training_data(
        self
    ) -> List[Dict[str, Any]]:

        with self.get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    fl.actual_pump_outcome,
                    fl.predicted_score,
                    p.features_json
                FROM feedback_labels fl
                JOIN predictions p
                    ON fl.prediction_id = p.id
                WHERE p.features_json IS NOT NULL
            """)

            rows = cursor.fetchall()

            results = []

            for row in rows:

                item = dict(row)

                try:

                    item["features"] = json.loads(
                        item["features_json"]
                    )

                    results.append(item)

                except Exception:

                    continue

            return results

    # ============================================================
    # GET MODEL LOGS
    # ============================================================

    def get_model_logs(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:

        with self.get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT *
                FROM model_logs
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            return [
                dict(row)
                for row in cursor.fetchall()
            ]

    # ============================================================
    # INSERT MODEL LOG
    # ============================================================

    def insert_model_log(
        self,
        version: str,
        accuracy: float,
        samples_trained: int,
        notes: str
    ):

        def operation():

            with self.get_connection() as conn:

                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO model_logs (
                        version,
                        accuracy,
                        samples_trained,
                        notes
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    version,
                    accuracy,
                    samples_trained,
                    notes
                ))

                conn.commit()

        return self._execute_with_retry(
            operation,
            "insert_model_log"
        )

    # ============================================================
    # INSERT WISHLIST
    # ============================================================

    def insert_wishlist(
        self,
        token_symbol: str,
        entry_price: float,
        entry_price_str: str,
        pump_score: float,
        recommendation: str,
        target_gain: str,
        target_ratio: float,
        timeframe: str,
        timeframe_days: int,
        keterangan_awam: str,
        features: dict = None
    ) -> int:

        def operation():

            with self.get_connection() as conn:

                cursor = conn.cursor()

                now = datetime.now(timezone.utc)

                deadline = (
                    now +
                    timedelta(days=timeframe_days)
                )

                features_json = (
                    json.dumps(features, default=str)
                    if features
                    else None
                )

                cursor.execute("""
                    INSERT INTO wishlist (
                        token_symbol,
                        entry_price,
                        entry_price_str,
                        pump_score,
                        recommendation,
                        target_gain,
                        target_ratio,
                        timeframe,
                        timeframe_days,
                        keterangan_awam,
                        created_at,
                        target_deadline,
                        highest_price_seen,
                        status,
                        features_json
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    token_symbol.upper(),
                    entry_price,
                    entry_price_str,
                    pump_score,
                    recommendation,
                    target_gain,
                    target_ratio,
                    timeframe,
                    timeframe_days,
                    keterangan_awam,
                    now.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    deadline.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    entry_price,
                    "TRACKING ⏱️",
                    features_json
                ))

                conn.commit()

                return cursor.lastrowid

        return self._execute_with_retry(
            operation,
            "insert_wishlist"
        )

    # ============================================================
    # GET WISHLISTS
    # ============================================================

    def get_wishlists(
        self
    ) -> List[Dict[str, Any]]:

        with self.get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT *
                FROM wishlist
                ORDER BY created_at DESC
            """)

            return [
                dict(row)
                for row in cursor.fetchall()
            ]

    # ============================================================
    # UPDATE WISHLIST VERIFICATION
    # ============================================================

    def update_wishlist_verification(
        self,
        wishlist_id: int,
        status: str,
        highest_price: float,
        actual_gain_pct: float,
        fed_to_ml: int = 0
    ):

        def operation():

            with self.get_connection() as conn:

                cursor = conn.cursor()

                now_str = (
                    datetime.now(timezone.utc)
                    .strftime("%Y-%m-%d %H:%M:%S")
                )

                cursor.execute("""
                    UPDATE wishlist
                    SET
                        status = ?,
                        highest_price_seen = ?,
                        actual_gain_percent = ?,
                        verified_at = ?,
                        fed_to_ml = ?
                    WHERE id = ?
                """, (
                    status,
                    highest_price,
                    actual_gain_pct,
                    now_str,
                    fed_to_ml,
                    wishlist_id
                ))

                conn.commit()

        return self._execute_with_retry(
            operation,
            "update_wishlist_verification"
        )

    # ============================================================
    # DELETE WISHLIST
    # ============================================================

    def delete_wishlist(
        self,
        wishlist_id: int
    ):

        def operation():

            with self.get_connection() as conn:

                cursor = conn.cursor()

                cursor.execute(
                    "DELETE FROM wishlist WHERE id = ?",
                    (wishlist_id,)
                )

                conn.commit()

        return self._execute_with_retry(
            operation,
            "delete_wishlist"
        )