import requests
from .base import BrokerGateway

try:
    from src.utils.auth import generate_totp
except ImportError:
    from utils.auth import generate_totp


class AngelOneGateway(BrokerGateway):
    """
    Implementation for Angel One SmartAPI.
    Official Docs: https://smartapi.angelbroking.com/docs

    Auth flow: clientcode + password + TOTP -> jwtToken (Authorization), feedToken, refreshToken.
    """
    BASE_URL = "https://apiconnect.angelbroking.com"

    def __init__(self, api_key, client_code, password, totp_secret):
        super().__init__(api_key, access_token=None)
        self.client_code = client_code
        self.password = password
        self.totp_secret = totp_secret
        self.jwt_token = None
        self.feed_token = None

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-PrivateKey": self.api_key,
            "Authorization": f"Bearer {self.jwt_token}" if self.jwt_token else "",
        }

    def login(self):
        """
        Logs in using clientcode/password/TOTP and caches the session tokens.
        """
        url = f"{self.BASE_URL}/rest/auth/angelbroking/user/v1/loginByPassword"
        payload = {
            "clientcode": self.client_code,
            "password": self.password,
            "totp": generate_totp(self.totp_secret),
        }

        self.logger.info("Angel One: Logging in via SmartAPI")
        # In actual use:
        # response = requests.post(url, json=payload, headers=self._headers())
        # data = response.json()["data"]
        # self.jwt_token = data["jwtToken"]
        # self.feed_token = data["feedToken"]
        # self.access_token = data["refreshToken"]
        # return data

        # Simulate response for demo
        self.jwt_token = "SIM_JWT_TOKEN"
        self.feed_token = "SIM_FEED_TOKEN"
        return {"status": "success", "message": "logged in (simulated)"}

    def place_order(self, symbol, transaction_type, quantity, order_type="MARKET", product="INTRADAY", stop_loss=None, target=None, symbol_token=None, exchange="NSE"):
        if not self.risk_manager.validate_order({"stop_loss": stop_loss, "target": target}):
            return {"status": "error", "message": "Order rejected by Risk Manager: Missing SL/Target"}

        if not self.jwt_token:
            self.login()

        url = f"{self.BASE_URL}/rest/secure/angelbroking/order/v1/placeOrder"
        payload = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": symbol_token or "",
            "transactiontype": transaction_type.upper(),  # BUY/SELL
            "exchange": exchange,
            "ordertype": order_type.upper(),
            "producttype": product.upper(),  # INTRADAY, DELIVERY, MARGIN
            "duration": "DAY",
            "price": "0",
            "quantity": str(quantity),
        }

        self.logger.info(f"Angel One: Placing {transaction_type} {quantity} {symbol}")
        # In actual use:
        # response = requests.post(url, json=payload, headers=self._headers())
        # return response.json()

        return {"status": "success", "broker": "Angel One", "order_id": "ANGEL_SIM_123"}

    def get_portfolio(self):
        url = f"{self.BASE_URL}/rest/secure/angelbroking/portfolio/v1/getHolding"
        # In actual use:
        # response = requests.get(url, headers=self._headers())
        # return response.json()

        return {
            "status": "success",
            "data": [
                {"symbol": "RELIANCE", "qty": 10, "avg_price": 2400.0, "current_price": 2450.0, "pnl": 500.0},
            ]
        }

    def get_orders(self):
        url = f"{self.BASE_URL}/rest/secure/angelbroking/order/v1/getOrderBook"
        # In actual use:
        # response = requests.get(url, headers=self._headers())
        # return response.json()

        return [
            {"order_id": "ANGEL_ORD_1", "symbol": "RELIANCE", "status": "COMPLETE", "side": "BUY", "qty": 10},
        ]
