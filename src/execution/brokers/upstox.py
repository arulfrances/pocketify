from .base import BrokerGateway


class UpstoxGateway(BrokerGateway):
    """
    Implementation for Upstox API v2.
    Official Docs: https://upstox.com/developer/api-documentation
    """
    BASE_URL = "https://api.upstox.com/v2"

    def place_order(self, symbol, transaction_type, quantity, order_type="MARKET", product="I", stop_loss=None, target=None):
        if not self.risk_manager.validate_order({"stop_loss": stop_loss, "target": target}):
            return {"status": "error", "message": "Order rejected by Risk Manager: Missing SL/Target"}

        url = f"{self.BASE_URL}/order/place"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "instrument_token": symbol,
            "transaction_type": transaction_type.upper(),  # BUY/SELL
            "order_type": order_type.upper(),
            "product": product,  # I (intraday), D (delivery)
            "quantity": quantity,
            "validity": "DAY",
        }

        self.logger.info(f"Upstox: Placing {transaction_type} {quantity} {symbol}")
        # In actual use:
        # response = requests.post(url, json=payload, headers=headers)
        # return response.json()

        return {"status": "success", "broker": "Upstox", "order_id": "UPSTOX_SIM_123"}

    def get_portfolio(self):
        url = f"{self.BASE_URL}/portfolio/long-term-holdings"
        # In actual use:
        # response = requests.get(url, headers={"Authorization": f"Bearer {self.access_token}"})
        # return response.json()

        return {"status": "success", "data": []}

    def get_orders(self):
        url = f"{self.BASE_URL}/order/retrieve-all"
        # In actual use:
        # response = requests.get(url, headers={"Authorization": f"Bearer {self.access_token}"})
        # return response.json()

        return []
