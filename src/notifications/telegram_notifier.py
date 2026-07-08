import os
import logging
import requests


class TelegramNotifier:
    """
    Sends trading signal alerts to a Telegram chat via the Bot API.
    Setup: message @BotFather to create a bot and get TELEGRAM_BOT_TOKEN,
    then message @userinfobot (or your bot) to find your TELEGRAM_CHAT_ID.
    """
    API_URL = "https://api.telegram.org"

    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.logger = logging.getLogger("TelegramNotifier")

    def is_configured(self):
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text):
        if not self.is_configured():
            self.logger.warning("Telegram not configured (missing TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID). Skipping alert.")
            return {"status": "error", "message": "Telegram not configured"}

        url = f"{self.API_URL}/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return {"status": "error", "message": str(e)}

    def send_signal_alert(self, signal_data):
        """
        signal_data: dict as returned by prediction_service.get_signal()
        """
        emoji = "🟢" if signal_data["signal"] == "BUY" else "🔴"
        text = (
            f"{emoji} *{signal_data['signal']} signal - {signal_data['symbol']}*\n"
            f"Price: {signal_data['price']:.2f}\n"
            f"Confidence: {signal_data['confidence']*100:.1f}%\n"
            f"Stop Loss: {signal_data['stop_loss']}\n"
            f"Target: {signal_data['target']}\n"
            f"Time: {signal_data['timestamp']}"
        )
        return self.send_message(text)
