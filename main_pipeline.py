import sys
import os
import pandas as pd

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.ingestion.nse_downloader import NSEDownloader
from src.features.feature_engineer import FeatureEngineer
from src.models.trainer import ModelTrainer

def main():
    print("--- Prostock Market Prediction Pipeline ---")
    
    # 1. Download Data
    downloader = NSEDownloader()
    print("Fetching NIFTY 50 data...")
    # For speed and reliability in this demo, using yfinance
    df = downloader.download_index_data("NIFTY 50", start_date="2020-01-01")
    
    if df is None or df.empty:
        print("Failed to fetch data. Exiting.")
        return

    # 2. Feature Engineering
    print("Generating features...")
    fe = FeatureEngineer()
    df_features = fe.add_technical_indicators(df)
    
    # 3. Model Training
    print(f"Training XGBoost model on {df_features.shape[0]} samples...")
    trainer = ModelTrainer()
    
    # Define features to use (only numeric, non-price columns)
    # Using a list comprehension that works with multi-index columns too
    feature_cols = []
    for col in df_features.columns:
        col_name = col[0] if isinstance(col, tuple) else col
        if col_name not in ['Target', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']:
            feature_cols.append(col)
            
    print(f"Features used: {[c[0] if isinstance(c, tuple) else c for c in feature_cols]}")
    model = trainer.train_xgboost(df_features, feature_cols)
    
    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
