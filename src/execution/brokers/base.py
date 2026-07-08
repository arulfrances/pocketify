import logging

try:
    from src.execution.risk_manager import RiskManager
except ImportError:
    from execution.risk_manager import RiskManager


class BrokerGateway:
    """
    Base class / interface for all broker integrations.
    """
    def __init__(self, api_key, access_token):
        self.api_key = api_key
        self.access_token = access_token
        self.logger = logging.getLogger(self.__class__.__name__)
        self.risk_manager = RiskManager()

    def place_order(self, symbol, transaction_type, quantity, order_type="MARKET", product="MIS", stop_loss=None, target=None):
        raise NotImplementedError

    def get_portfolio(self):
        raise NotImplementedError

    def get_orders(self):
        raise NotImplementedError
