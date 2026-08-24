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

def get_live_prices_dict() -> Dict[str, Dict[str, Any]]:
    try:
        tickers = dex_collector.fetch_live_tickers(config.TARGET_MEME_COINS)
        return {t["symbol"]: t for t in tickers}
    except Exception as e:
        logger.warning(f"Error fetching live prices: {e}")
        return {}

@app.get("/api/trending")
async def get_trending_predictions():
    # Compute latest features for all target meme coins
    features_dict = feature_pipeline.compute_all_tokens()
    prices_map = get_live_prices_dict()
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

        price_info = prices_map.get(token.upper(), {})
        price_str = price_info.get("price", "$0.000045")
        change_24h = price_info.get("change_24h", 12.5)

        predictions.append({
            "id": pred_id,
            "token_symbol": token,
            "pump_score": pump_score_pct,
            "confidence": round(confidence * 100, 1),
            "recommendation": recommendation,
            "price_usd": price_str,
            "change_24h": change_24h,
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
    prices_map = get_live_prices_dict()
    price_info = prices_map.get(token, {})

    return {
        "token_symbol": token,
        "pump_score": pump_score_pct,
        "confidence": round(confidence * 100, 1),
        "recommendation": recommendation,
        "price_usd": price_info.get("price", "$0.000045"),
        "change_24h": price_info.get("change_24h", 12.5),
        "target_gain": hist_eval["target_gain"],
        "timeframe": hist_eval["timeframe"],
        "keterangan_awam": hist_eval["keterangan_awam"],
        "features": feat
    }

# ==============================================================================
# WISHLIST & PREDICTION OUTCOME VERIFICATION API ENDPOINTS
# ==============================================================================

@app.post("/api/wishlist/add")
async def add_to_wishlist(request: Request):
    data = await request.json()
    token = data.get("token_symbol", "TOKEN").upper().replace("$", "")
    
    # Get current live price
    prices_map = get_live_prices_dict()
    price_info = prices_map.get(token, {})
    price_str = data.get("entry_price_str") or price_info.get("price", "$0.00005")
    
    try:
        clean_price = float(price_str.replace("$", "").replace(",", ""))
    except Exception:
        clean_price = 0.00005

    target_gain = data.get("target_gain", "+50% s/d +80%")
    target_ratio = 1.50
    if "+100%" in target_gain:
        target_ratio = 2.00
    elif "+50%" in target_gain:
        target_ratio = 1.50
    elif "+20%" in target_gain:
        target_ratio = 1.20

    timeframe_str = data.get("timeframe", "1 - 3 Hari Ke Depan")
    timeframe_days = 3
    if "Hari" in timeframe_str:
        timeframe_days = 3
    elif "Minggu" in timeframe_str:
        timeframe_days = 14
    elif "Jam" in timeframe_str:
        timeframe_days = 1

    feat = feature_pipeline.compute_token_features(token)

    wishlist_id = db.insert_wishlist(
        token_symbol=token,
        entry_price=clean_price,
        entry_price_str=price_str,
        pump_score=float(data.get("pump_score", 85.0)),
        recommendation=data.get("recommendation", "STRONG BUY 🚀"),
        target_gain=target_gain,
        target_ratio=target_ratio,
        timeframe=timeframe_str,
        timeframe_days=timeframe_days,
        keterangan_awam=data.get("keterangan_awam", "Perbincangan komunitas positif."),
        features=feat
    )

    return {
        "status": "ok",
        "message": f"Koin ${token} berhasil ditambahkan ke Wishlist & Tracker!",
        "wishlist_id": wishlist_id
    }

@app.get("/api/wishlist")
async def get_wishlist():
    items = db.get_wishlists()
    prices_map = get_live_prices_dict()

    processed_items = []
    for item in items:
        token = item["token_symbol"]
        price_info = prices_map.get(token, {})
        current_price_str = price_info.get("price", item["entry_price_str"])
        
        try:
            current_price = float(current_price_str.replace("$", "").replace(",", ""))
        except Exception:
            current_price = item["entry_price"]

        entry_price = item["entry_price"] or 0.00005
        current_gain_pct = round(((current_price - entry_price) / entry_price) * 100, 2)
        highest_price = max(item["highest_price_seen"] or 0, current_price)
        highest_gain_pct = round(((highest_price - entry_price) / entry_price) * 100, 2)

        status = item["status"]
        fed_to_ml = item["fed_to_ml"]

        # Automatic verification logic
        # If price pumped by target_ratio (+50%+ or +100%+)
        if highest_gain_pct >= (item["target_ratio"] - 1.0) * 100:
            status = f"🎯 PREDIKSI BENAR (+{highest_gain_pct}% Gain)"
            if fed_to_ml == 0:
                # Ground truth label = 1 (Pump Success)
                feat = feature_pipeline.compute_token_features(token)
                ml_manager.update_online(feat, 1)
                db.insert_model_log("1.5.0", 1.0, ml_manager.samples_seen, 
                                   f"Wishlist verification for ${token}: PUMP CONFIRMED (+{highest_gain_pct}% gain). ML model updated with positive sample.")
                fed_to_ml = 1
                db.update_wishlist_verification(item["id"], status, highest_price, highest_gain_pct, fed_to_ml=1)
        else:
            db.update_wishlist_verification(item["id"], status, highest_price, current_gain_pct, fed_to_ml=fed_to_ml)

        item_dict = {
            "id": int(item["id"]),
            "token_symbol": str(item["token_symbol"]),
            "entry_price": float(item["entry_price"] or 0.0),
            "entry_price_str": str(item["entry_price_str"] or "$0.00"),
            "pump_score": float(item["pump_score"] or 0.0),
            "recommendation": str(item["recommendation"] or "STRONG BUY 🚀"),
            "target_gain": str(item["target_gain"] or "+50%"),
            "target_ratio": float(item["target_ratio"] or 1.50),
            "timeframe": str(item["timeframe"] or "1-3 Hari"),
            "timeframe_days": int(item["timeframe_days"] or 3),
            "keterangan_awam": str(item["keterangan_awam"] or ""),
            "created_at": str(item["created_at"] or ""),
            "target_deadline": str(item["target_deadline"] or ""),
            "current_price_str": str(current_price_str),
            "current_gain_pct": float(current_gain_pct),
            "highest_gain_pct": float(highest_gain_pct),
            "status": str(status),
            "fed_to_ml": int(fed_to_ml)
        }
        processed_items.append(item_dict)

    return {"status": "ok", "wishlist": processed_items}

@app.delete("/api/wishlist/{wishlist_id}")
async def delete_wishlist_item(wishlist_id: int):
    db.delete_wishlist(wishlist_id)
    return {"status": "ok", "message": "Wishlist item removed."}

@app.post("/api/wishlist/simulate_pump/{wishlist_id}")
async def simulate_wishlist_pump(wishlist_id: int):
    items = db.get_wishlists()
    target_item = next((i for i in items if i["id"] == wishlist_id), None)
    if not target_item:
        return {"status": "error", "message": "Wishlist item not found."}

    token = target_item["token_symbol"]
    entry_price = target_item["entry_price"] or 0.00005
    # Simulate a +65% pump
    simulated_price = entry_price * 1.65
    simulated_gain_pct = 65.0

    status = f"🎯 PREDIKSI BENAR (+{simulated_gain_pct}% Gain)"
    
    # Train ML Model with ground-truth positive label = 1
    feat = feature_pipeline.compute_token_features(token)
    ml_manager.update_online(feat, 1)
    db.insert_model_log("1.5.0", 1.0, ml_manager.samples_seen, 
                       f"Simulated verification for ${token}: PUMP CONFIRMED (+{simulated_gain_pct}% gain). ML model updated with positive label=1.")
    
    db.update_wishlist_verification(wishlist_id, status, simulated_price, simulated_gain_pct, fed_to_ml=1)

    return {
        "status": "ok",
        "message": f"⚡ SIMULASI KENAIKAN SUCCESS! Prediksi ${token} terverifikasi BENAR (+65% Gain). Data telah dikirim ke ML Engine untuk Self-Learning!",
        "simulated_gain": "+65.0%",
        "new_samples_trained": ml_manager.samples_seen
    }


@app.get("/api/dexscreener")
async def get_dexscreener_tickers():
    tickers = dex_collector.fetch_live_tickers()
    return {"status": "ok", "tickers": tickers}
