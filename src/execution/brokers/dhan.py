from .base import BrokerGateway


class DhanGateway(BrokerGateway):
    """
    Implementation for Dhan API.
    Official Docs: https://dhanhq.co/docs/v2/
    """
    BASE_URL = "https://api.dhan.co/v2"

    def __init__(self, client_id, access_token):
        super().__init__(api_key=client_id, access_token=access_token)
        self.client_id = client_id

    def place_order(self, symbol, transaction_type, quantity, order_type="MARKET", product="INTRADAY", stop_loss=None, target=None, security_id=None, exchange_segment="NSE_EQ"):
        if not self.risk_manager.validate_order({"stop_loss": stop_loss, "target": target}):
            return {"status": "error", "message": "Order rejected by Risk Manager: Missing SL/Target"}

        url = f"{self.BASE_URL}/orders"
        headers = {"access-token": self.access_token, "Content-Type": "application/json"}
        payload = {
            "dhanClientId": self.client_id,
            "transactionType": transaction_type.upper(),  # BUY/SELL
            "exchangeSegment": exchange_segment,
            "productType": product.upper(),  # INTRADAY, CNC, MARGIN
            "orderType": order_type.upper(),
            "securityId": security_id or symbol,
            "quantity": quantity,
            "validity": "DAY",
        }

        self.logger.info(f"Dhan: Placing {transaction_type} {quantity} {symbol}")
        # In actual use:
        # response = requests.post(url, json=payload, headers=headers)
        # return response.json()

        return {"status": "success", "broker": "Dhan", "order_id": "DHAN_SIM_123"}

    def get_portfolio(self):
        url = f"{self.BASE_URL}/holdings"
        # In actual use:
        # response = requests.get(url, headers={"access-token": self.access_token})
        # return response.json()

        return {"status": "success", "data": []}

    def get_orders(self):
        url = f"{self.BASE_URL}/orders"
        # In actual use:
        # response = requests.get(url, headers={"access-token": self.access_token})
        # return response.json()

        return []
