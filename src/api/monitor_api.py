from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import os
import sys
import secrets

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.execution.brokers import IndstocksGateway, KotakNeoGateway, AngelOneGateway
from src.ingestion.nse_downloader import NSEDownloader
from src.features.feature_engineer import FeatureEngineer
from src.models.trainer import ModelTrainer
from src.backtest.engine import BacktestEngine
from src.execution.risk_manager import RiskManager
from src.utils.market_status import is_market_open
from src.services import prediction_service
from src.notifications.telegram_notifier import TelegramNotifier

app = FastAPI(title="Prostock Market API")

# Initialize components
downloader = NSEDownloader()
fe = FeatureEngineer()
trainer = ModelTrainer()
backtester = BacktestEngine()
risk_manager = RiskManager()
telegram = TelegramNotifier()

# Defaults & Caching
INDEX_CACHE = {
    "last_updated": None,
    "data": {},
    "market": {"open": False, "status": "FETCHING..."}
}

BROKER_CONTEXT = {
    "active": "indstocks",
    "brokers": {
        "indstocks": IndstocksGateway(os.getenv("IND_API_KEY", "key"), os.getenv("IND_ACCESS_TOKEN", "token")),
        "kotak": KotakNeoGateway(
            os.getenv("KOTAK_API_KEY", "key"),
            os.getenv("KOTAK_ACCESS_TOKEN", "token"),
            os.getenv("KOTAK_CONSUMER_SECRET", "secret"),
            os.getenv("KOTAK_PHONE", "999"),
            os.getenv("KOTAK_MPIN", "1234")
        ),
        "angelone": AngelOneGateway(
            os.getenv("ANGELONE_API_KEY", "key"),
            os.getenv("ANGELONE_CLIENT_CODE", "client"),
            os.getenv("ANGELONE_PASSWORD", "password"),
            os.getenv("ANGELONE_TOTP_SECRET", "")
        )
    }
}

@app.get("/api")
def read_root():
    return {"status": "Prostock Engine is Running"}

@app.get("/api/predictions")
def get_latest_predictions(symbol: str = "NIFTY 50"):
    try:
        return prediction_service.get_signal(symbol)
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/backtest")
def get_backtest_report():
    try:
        # Load the saved model and historical data
        df = downloader.download_index_data("NIFTY 50", start_date="2023-01-01")
        if df is None: return {"status": "error", "message": "No data"}
        
        df_features = fe.add_technical_indicators(df)
        model = trainer.load_model()
        if not model: return {"status": "error", "message": "Model not trained"}
        
        feature_cols = [col for col in df_features.columns if col not in ['Target', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
        predictions = model.predict(df_features[feature_cols])
        
        report = backtester.run_backtest(df_features, predictions)
        return report
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/indices")
def get_all_indices():
    try:
        now = pd.Timestamp.now()
        
        # Check cache (Refresh every 5 minutes)
        if INDEX_CACHE["last_updated"] and (now - INDEX_CACHE["last_updated"]).seconds < 300:
            return {**INDEX_CACHE["data"], "market": INDEX_CACHE["market"]}

        isOpen, status_text = is_market_open()
        indices = ["NIFTY 50", "BANKNIFTY", "SENSEX"]
        results = {}
        
        for idx in indices:
            # For live updates, only fetch last 5 days to be fast
            df = downloader.download_index_data(idx, start_date=(now - pd.Timedelta(days=5)).strftime('%Y-%m-%d'))
            if df is not None and not df.empty:
                current_price = float(df['Close'].iloc[-1])
                prev_price = float(df['Close'].iloc[-2]) if len(df) > 1 else current_price
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100
                results[idx] = {
                    "price": current_price,
                    "change": change,
                    "change_pct": change_pct
                }
        
        # Update Cache
        INDEX_CACHE["data"] = results
        INDEX_CACHE["market"] = {"open": isOpen, "status": status_text}
        INDEX_CACHE["last_updated"] = now
        
        return {**results, "market": INDEX_CACHE["market"]}
    except Exception as e:
        # Fallback to cache if error
        if INDEX_CACHE["data"]:
             return {**INDEX_CACHE["data"], "market": INDEX_CACHE["market"]}
        return {"status": "error", "message": str(e)}

@app.get("/api/config")
def get_config():
    return {"active_broker": BROKER_CONTEXT["active"]}

@app.post("/api/config/switch")
def switch_broker(broker: str):
    if broker.lower() in BROKER_CONTEXT["brokers"]:
        BROKER_CONTEXT["active"] = broker.lower()
        return {"status": "success", "active_broker": BROKER_CONTEXT["active"]}
    return {"status": "error", "message": "Broker not found"}

@app.get("/api/profile")
def get_user_profile():
    active_key = BROKER_CONTEXT["active"]
    active_broker = BROKER_CONTEXT["brokers"][active_key]
    
    try:
        # Mock retrieval based on active broker
        return {
            "status": "success",
            "broker": active_key,
            "data": {
                "first_name": active_key.capitalize(),
                "last_name": "User",
                "email": f"user@{active_key}.com",
                "user_id": f"{active_key.upper()}_123"
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/portfolio")
def get_portfolio():
    active_key = BROKER_CONTEXT["active"]
    return BROKER_CONTEXT["brokers"][active_key].get_portfolio()

@app.get("/api/orders")
def get_orders():
    active_key = BROKER_CONTEXT["active"]
    return BROKER_CONTEXT["brokers"][active_key].get_orders()

@app.get("/api/search")
def search_symbol(query: str):
    """
    Simple search simulation.
    In reality, this would search a ticker list or call a broker API.
    """
    valid_indices = ["NIFTY 50", "BANKNIFTY", "SENSEX"]
    results = [idx for idx in valid_indices if query.upper() in idx.upper()]
    return {"query": query, "results": results}

class WebhookSignal(BaseModel):
    secret: str
    symbol: str
    action: str  # BUY/SELL
    quantity: int = 1
    strategy: str = "external"
    stop_loss: float | None = None
    target: float | None = None

@app.post("/api/webhook/signal")
def webhook_signal(payload: WebhookSignal):
    """
    Accepts externally generated strategy signals (e.g. a TradingView alert),
    similar to openalgo's webhook-driven execution model.
    Routes the signal to the currently active broker and notifies Telegram.
    """
    expected_secret = os.getenv("WEBHOOK_SECRET", "")
    if not expected_secret or not secrets.compare_digest(payload.secret, expected_secret):
        raise HTTPException(status_code=401, detail="Invalid or missing webhook secret")

    active_key = BROKER_CONTEXT["active"]
    broker = BROKER_CONTEXT["brokers"][active_key]

    order_result = broker.place_order(
        symbol=payload.symbol,
        transaction_type=payload.action.upper(),
        quantity=payload.quantity,
        stop_loss=payload.stop_loss,
        target=payload.target,
    )

    telegram.send_message(
        f"\U0001F4E1 Webhook signal from *{payload.strategy}*: "
        f"{payload.action.upper()} {payload.quantity} {payload.symbol}\n"
        f"Broker: {active_key}\nResult: {order_result.get('status')}"
    )

    return {"status": "success", "broker": active_key, "order_result": order_result}

# Serve Static Files
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_path, "index.html"))

@app.get("/{file_path:path}")
async def serve_file(file_path: str):
    file = os.path.join(static_path, file_path)
    if os.path.exists(file):
        return FileResponse(file)
    return FileResponse(os.path.join(static_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    # Run: python src/api/monitor_api.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
