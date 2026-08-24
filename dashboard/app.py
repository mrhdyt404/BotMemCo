import os
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import config
from ingestion.database import DatabaseManager
from ingestion.dexscreener_collector import DexScreenerCollector
from engine.feature_pipeline import FeaturePipeline
from ml.model_manager import MemeCoinMLManager
from engine.historical_analyzer import HistoricalPatternAnalyzer

logger = logging.getLogger(__name__)

app = FastAPI(title="MemeCoin ML Trend & Prediction Bot")

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

db = DatabaseManager()
dex_collector = DexScreenerCollector()
feature_pipeline = FeaturePipeline(db)
ml_manager = MemeCoinMLManager()
historical_analyzer = HistoricalPatternAnalyzer()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/trending")
async def get_trending_predictions():
    # Compute latest features for all target meme coins
    features_dict = feature_pipeline.compute_all_tokens()
    predictions = []

    for token, feat in features_dict.items():
        pump_score, confidence, recommendation = ml_manager.predict(feat)
        pump_score_pct = round(pump_score * 100, 1)
        
        hist_eval = historical_analyzer.evaluate_token(feat, pump_score_pct)

        # Save prediction into DB
        pred_id = db.insert_prediction(
            token_symbol=token,
            pump_score=pump_score,
            confidence=confidence,
            recommendation=recommendation,
            features=feat
        )

        predictions.append({
            "id": pred_id,
            "token_symbol": token,
            "pump_score": pump_score_pct,
            "confidence": round(confidence * 100, 1),
            "recommendation": recommendation,
            "post_count_1h": feat["post_count_1h"],
            "post_count_24h": feat["post_count_24h"],
            "volume_velocity": feat["volume_velocity"],
            "avg_sentiment": feat["avg_sentiment"],
            "bullish_ratio": round(feat["bullish_ratio"] * 100, 1),
            "social_reach_score": feat["social_reach_score"],
            "x_ratio": round(feat["x_ratio"] * 100, 1),
            "target_gain": hist_eval["target_gain"],
            "timeframe": hist_eval["timeframe"],
            "timeframe_cat": hist_eval["timeframe_cat"],
            "keterangan_awam": hist_eval["keterangan_awam"]
        })

    # Sort by pump score descending
    predictions.sort(key=lambda x: x["pump_score"], reverse=True)
    top_recommendations = predictions[:3]

    return {
        "status": "ok",
        "predictions": predictions,
        "top_recommendations": top_recommendations
    }

@app.get("/api/feed")
async def get_live_feed(limit: int = 30):
    posts = db.get_recent_posts(limit=limit)
    return {"status": "ok", "posts": posts}

@app.get("/api/ml/status")
async def get_ml_status():
    logs = db.get_model_logs(limit=10)
    return {
        "status": "ok",
        "samples_trained": ml_manager.samples_seen,
        "is_online_fitted": ml_manager.is_online_fitted,
        "is_batch_fitted": ml_manager.is_batch_fitted,
        "logs": logs
    }

@app.get("/api/predict/{token_symbol}")
async def predict_token(token_symbol: str):
    token = token_symbol.upper()
    feat = feature_pipeline.compute_token_features(token)
    pump_score, confidence, recommendation = ml_manager.predict(feat)
    pump_score_pct = round(pump_score * 100, 1)
    hist_eval = historical_analyzer.evaluate_token(feat, pump_score_pct)

    return {
        "token_symbol": token,
        "pump_score": pump_score_pct,
        "confidence": round(confidence * 100, 1),
        "recommendation": recommendation,
        "target_gain": hist_eval["target_gain"],
        "timeframe": hist_eval["timeframe"],
        "keterangan_awam": hist_eval["keterangan_awam"],
        "features": feat
    }

@app.get("/api/dexscreener")
async def get_dexscreener_tickers():
    tickers = dex_collector.fetch_live_tickers()
    return {"status": "ok", "tickers": tickers}
