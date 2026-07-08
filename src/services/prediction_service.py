import pandas as pd

from src.ingestion.nse_downloader import NSEDownloader
from src.features.feature_engineer import FeatureEngineer
from src.models.trainer import ModelTrainer
from src.execution.risk_manager import RiskManager

downloader = NSEDownloader()
fe = FeatureEngineer()
trainer = ModelTrainer()
risk_manager = RiskManager()


def get_signal(symbol="NIFTY 50"):
    """
    Fetches recent data, engineers features and returns the latest
    BUY/SELL signal with confidence and risk levels for a given index.
    """
    df = downloader.download_index_data(symbol, start_date=(pd.Timestamp.now() - pd.Timedelta(days=100)).strftime('%Y-%m-%d'))

    if df is None or df.empty:
        return {"status": "error", "message": f"Failed to fetch market data for {symbol}"}

    df_features = fe.add_technical_indicators(df)

    feature_cols = [col for col in df_features.columns if col not in ['Target', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
    prediction = trainer.predict_latest(df_features, feature_cols)

    if not prediction:
        return {"status": "error", "message": "Model not trained yet. Run main_pipeline.py first."}

    current_price = float(df['Close'].iloc[-1])
    atr = float(df_features['ATR'].iloc[-1])
    sl, target = risk_manager.calculate_levels(current_price, atr, side=prediction["signal"])

    return {
        "status": "success",
        "symbol": symbol,
        "price": current_price,
        "signal": prediction["signal"],
        "confidence": prediction["confidence"],
        "stop_loss": sl,
        "target": target,
        "timestamp": pd.Timestamp.now().isoformat()
    }
