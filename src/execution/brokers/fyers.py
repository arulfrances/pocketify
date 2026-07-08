from .base import BrokerGateway


class FyersGateway(BrokerGateway):
    """
    Implementation for Fyers API v3.
    Official Docs: https://myapi.fyers.in/docsv3
    """
    BASE_URL = "https://api-t1.fyers.in/api/v3"

    def place_order(self, symbol, transaction_type, quantity, order_type="MARKET", product="INTRADAY", stop_loss=None, target=None):
        if not self.risk_manager.validate_order({"stop_loss": stop_loss, "target": target}):
            return {"status": "error", "message": "Order rejected by Risk Manager: Missing SL/Target"}

        url = f"{self.BASE_URL}/orders/sync"
        headers = {"Authorization": f"{self.api_key}:{self.access_token}"}
        payload = {
            "symbol": symbol,
            "qty": quantity,
            "type": 2 if order_type.upper() == "MARKET" else 1,  # 2=Market, 1=Limit
            "side": 1 if transaction_type.upper() == "BUY" else -1,
            "productType": product.upper(),  # INTRADAY, CNC, MARGIN
            "validity": "DAY",
        }

        self.logger.info(f"Fyers: Placing {transaction_type} {quantity} {symbol}")
        # In actual use:
        # response = requests.post(url, json=payload, headers=headers)
        # return response.json()

        return {"status": "success", "broker": "Fyers", "order_id": "FYERS_SIM_123"}

    def get_portfolio(self):
        url = f"{self.BASE_URL}/holdings"
        # In actual use:
        # response = requests.get(url, headers={"Authorization": f"{self.api_key}:{self.access_token}"})
        # return response.json()

        return {"status": "success", "data": []}

    def get_orders(self):
        url = f"{self.BASE_URL}/orders"
        # In actual use:
        # response = requests.get(url, headers={"Authorization": f"{self.api_key}:{self.access_token}"})
        # return response.json()

        return []
