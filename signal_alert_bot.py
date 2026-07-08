"""
Polls the ML model's predictions for Nifty 50, Bank Nifty and Sensex, and
sends a Telegram alert whenever a symbol's signal flips (BUY <-> SELL).

Usage (long-running, e.g. on a VM):
    python signal_alert_bot.py

Usage (single pass, e.g. from a scheduler like GitHub Actions or cron):
    RUN_ONCE=true python signal_alert_bot.py

Last-seen signals are persisted to STATE_FILE (default signal_state.json) so
the flip-detection survives process restarts between scheduled runs.

Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env (see .env.example).
Run main_pipeline.py first so a trained model exists.
"""
import os
import sys
import time
import json
import logging

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
from src.services.prediction_service import get_signal
from src.notifications.telegram_notifier import TelegramNotifier
from src.utils.market_status import is_market_open

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SignalAlertBot")

SYMBOLS = ["NIFTY 50", "BANKNIFTY", "SENSEX"]
POLL_INTERVAL_SECONDS = int(os.getenv("SIGNAL_POLL_INTERVAL", "300"))
STATE_FILE = os.getenv("STATE_FILE", "signal_state.json")


def load_state(path):
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not read state file {path}: {e}")
    return {}


def save_state(path, state):
    try:
        with open(path, "w") as f:
            json.dump(state, f)
    except OSError as e:
        logger.warning(f"Could not write state file {path}: {e}")


def run(poll_interval=POLL_INTERVAL_SECONDS, iterations=None, state_file=STATE_FILE):
    notifier = TelegramNotifier()
    if not notifier.is_configured():
        logger.warning("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set - alerts will be logged only, not sent.")

    last_signal = load_state(state_file)
    count = 0
    while iterations is None or count < iterations:
        is_open, status_text = is_market_open()
        if not is_open:
            logger.info(f"Market closed ({status_text}). Sleeping.")
        else:
            for symbol in SYMBOLS:
                result = get_signal(symbol)
                if result.get("status") != "success":
                    logger.error(f"{symbol}: {result.get('message')}")
                    continue

                signal = result["signal"]
                logger.info(f"{symbol}: {signal} @ {result['price']:.2f} (confidence {result['confidence']*100:.1f}%)")

                if last_signal.get(symbol) != signal:
                    notifier.send_signal_alert(result)
                    last_signal[symbol] = signal
                    save_state(state_file, last_signal)

        count += 1
        if iterations is None or count < iterations:
            time.sleep(poll_interval)


if __name__ == "__main__":
    run_once = os.getenv("RUN_ONCE", "false").lower() == "true"
    run(iterations=1 if run_once else None)
