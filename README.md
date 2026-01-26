# Prostock: Indian Market Prediction & Trading Engine

> **⚠️ Study Note & Disclaimer:** This project has been built as a **hobby project** for educational purposes. Trading in financial markets involves significant risk. Use this software with extreme care. Always perform your own research and study before executing trades. The authors are not responsible for any financial losses.

![Prostock Dashboard](https://github.com/arulfrances/ProStock/blob/main/prostock-dashboard.png)

Prostock is an AI-powered trading application designed for the Indian market (Nifty 50, Bank Nifty, Sensex). It integrates data ingestion from NSE, feature engineering using technical indicators, ML-based prediction, and a broker-agnostic execution gateway.

## Project Structure

- `data/`: Raw and processed market data.
- `src/ingestion/`: Modules to fetch data from NSE/BSE and other APIs.
- `src/features/`: Feature engineering and technical indicators.
- `src/models/`: AI/ML model training and saved models.
- `src/execution/`: Broker API integrations (Zerodha, Upstox) and live strategy logic.
- `main_pipeline.py`: End-to-end ML pipeline (Fetch -> Feature -> Train).
- `src/execution/live_strategy.py`: Sample live trading loop with strategy logic.

## Getting Started

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run ML Pipeline**:
    This will download historical Nifty 50 data, calculate indicators, and train an XGBoost model.
    ```bash
    python main_pipeline.py
    ```

3.  **Run Live Simulation**:
    This simulates a live price stream and executes a simple SMA crossover strategy.
    ```bash
    python src/execution/live_strategy.py
    ```

   ## 🚦 How to Start Your Engine:
# Step 1: Train the "Brain" (Takes ~10 seconds):

powershell
python main_pipeline.py
# Step 2: Start the Monitoring Station:

powershell
python src/api/monitor_api.py
Access your command center at http://localhost:8000.

# Step 3: Activate the Trading Bot:

powershell
python run_trading.py




## Features Implemented

- [x] **Data Ingestion**: Support for `yfinance` and NSE Bhavcopy downloading.
- [x] **Feature Store**: RSI, SMA, Volatility, and Lagged returns.
- [x] **Modeling**: XGBoost Classifier for price direction prediction.
- [x] **Execution**: Interface for Zerodha Kite and Upstox with order placement logic.
- [x] **Strategy**: Real-time ticker processing and signal generation.

![ProStock dashboard](https://github.com/arulfrances/ProStock/blob/main/prostock-dashboard.png)

## Future Roadmap

- [ ] Add deep learning models (LSTM/Transformers).
- [ ] Implement a full-fledged Backtest engine with slippage and costs.
- [ ] Create a monitoring dashboard using FastAPI & React/HTML.
- [ ] Integrate real-time WebSocket from Kite Connect/Upstox.
