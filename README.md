# Prostock: Indian Market Prediction & Trading Engine

> **⚠️ Study Note & Disclaimer:** This project has been built as a **hobby project** for educational purposes. Trading in financial markets involves significant risk. Use this software with extreme care. Always perform your own research and study before executing trades. The authors are not responsible for any financial losses.

![Prostock Dashboard](https://github.com/arulfrances/ProStock/blob/main/prostock-dashboard.png)

Prostock is an AI-powered trading application designed for the Indian market (Nifty 50, Bank Nifty, Sensex). It integrates data ingestion from NSE, feature engineering using technical indicators, ML-based prediction, and a broker-agnostic execution gateway.

## Project Structure

- `data/`: Raw and processed market data.
- `src/ingestion/`: Modules to fetch data from NSE/BSE and other APIs.
- `src/features/`: Feature engineering and technical indicators.
- `src/models/`: AI/ML model training and saved models.
- `src/services/prediction_service.py`: Shared signal-generation logic used by both the API and the Telegram bot.
- `src/execution/brokers/`: One adapter per broker, all implementing the same `BrokerGateway` interface (`place_order`, `get_portfolio`, `get_orders`) - Zerodha, Upstox, Kotak Neo, Paytm Money, Indstocks (INDmoney), Angel One, Fyers, Dhan.
- `src/execution/live_strategy.py`: Sample live trading loop with strategy logic.
- `src/notifications/telegram_notifier.py`: Sends signal alerts to a Telegram chat.
- `signal_alert_bot.py`: Polls Nifty/Bank Nifty/Sensex signals and pushes a Telegram alert whenever a signal flips.
- `main_pipeline.py`: End-to-end ML pipeline (Fetch -> Feature -> Train).

## Broker Connectivity

Only brokers with a public, documented trading API can place automated orders. Of the brokers commonly used by retail traders in India:

| Broker | Status |
|---|---|
| Angel One (SmartAPI) | Supported (`AngelOneGateway`) |
| Zerodha Kite Connect | Supported (`ZerodhaKiteGateway`) |
| Upstox | Supported (`UpstoxGateway`) |
| Fyers | Supported (`FyersGateway`) |
| Dhan | Supported (`DhanGateway`) |
| Kotak Neo | Supported (`KotakNeoGateway`) |
| Paytm Money | Supported (`PaytmMoneyGateway`) |
| Indstocks (INDmoney) | Supported (`IndstocksGateway`) |
| Groww | **Not available** - Groww has no public API for automated order placement. |

All broker adapters currently return simulated responses for the live HTTP calls (the real request is written and commented above the simulated return) so the codebase is safe to run without live credentials. Fill in `.env` and uncomment the real `requests` call to go live - **test with a paper/sandbox account first.**

## Telegram Signal Alerts

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the bot token into `TELEGRAM_BOT_TOKEN`.
2. Message your bot once, then get your chat id (e.g. via [@userinfobot](https://t.me/userinfobot)) and set `TELEGRAM_CHAT_ID`.
3. Run `python main_pipeline.py` once to train the model.
4. Run `python signal_alert_bot.py` - it polls Nifty 50, Bank Nifty and Sensex on an interval (`SIGNAL_POLL_INTERVAL`, default 300s) during market hours and sends a Telegram message whenever a symbol's signal flips between BUY and SELL.

## Webhook-Triggered Strategies

`POST /api/webhook/signal` accepts external strategy signals (e.g. a TradingView alert) and routes them to the currently active broker, similar to openalgo's webhook execution model:

```json
{
  "secret": "<WEBHOOK_SECRET from .env>",
  "symbol": "NIFTY 50",
  "action": "BUY",
  "quantity": 1,
  "strategy": "my-strategy",
  "stop_loss": 21000,
  "target": 21500
}
```

Every call is validated against `WEBHOOK_SECRET` and posts a Telegram notification with the result.

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

# Step 4: Get Telegram Alerts for every signal:

powershell
python signal_alert_bot.py


## Features Implemented

- [x] **Data Ingestion**: Support for `yfinance` and NSE Bhavcopy downloading.
- [x] **Feature Store**: RSI, SMA, Volatility, and Lagged returns.
- [x] **Modeling**: XGBoost Classifier for price direction prediction.
- [x] **Execution**: Broker adapters for Angel One, Zerodha, Upstox, Fyers, Dhan, Kotak Neo, Paytm Money and Indstocks (INDmoney), all behind one interface.
- [x] **Strategy**: Real-time ticker processing and signal generation.
- [x] **Alerts**: Telegram bot that pushes BUY/SELL signal changes with stop-loss/target.
- [x] **Webhooks**: `/api/webhook/signal` for externally triggered strategies (openalgo-style).

![ProStock dashboard](https://github.com/arulfrances/ProStock/blob/main/prostock-dashboard.png)

## Future Roadmap

- [ ] Add deep learning models (LSTM/Transformers).
- [ ] Implement a full-fledged Backtest engine with slippage and costs.
- [ ] Create a monitoring dashboard using FastAPI & React/HTML.
- [ ] Integrate real-time WebSocket from Kite Connect/Upstox.
