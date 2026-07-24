import requests
from .base import BrokerGateway


class IndstocksGateway(BrokerGateway):
    """
    Implementation for Indstocks (INDmoney).
    Official Docs: https://api-docs.indstocks.com/
    """
    def __init__(self, api_key, access_token):
        super().__init__(api_key, access_token)
        self.base_url = "https://api.indstocks.com"
        self.instruments_cache = {}  # Map symbol -> security_id

    def fetch_instruments(self, segment="equity"):
        """
        Fetches instrument master CSV and caches it.
        Segments: equity, fno, index
        """
        url = f"{self.base_url}/market/instruments?source={segment}"
        headers = {"Authorization": self.access_token}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                # Parse CSV response
                import csv
                from io import StringIO
                f = StringIO(response.text)
                reader = csv.DictReader(f)
                for row in reader:
                    # Map TRADING_SYMBOL to SECURITY_ID
                    symbol = row.get('TRADING_SYMBOL')
                    sec_id = row.get('SECURITY_ID')
                    if symbol and sec_id:
                        self.instruments_cache[symbol] = sec_id
                self.logger.info(f"Loaded {len(self.instruments_cache)} instruments for {segment}")
            else:
                self.logger.error(f"Failed to fetch {segment} instruments: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Error fetching instruments: {e}")

    def _resolve_security_id(self, symbol, segment):
        security_id = self.instruments_cache.get(symbol)
        if not security_id:
            self.fetch_instruments(segment.lower())
            security_id = self.instruments_cache.get(symbol)
        return security_id

    def place_order(self, symbol, transaction_type, quantity, order_type="MARKET", product="CNC", segment="EQUITY", stop_loss=None, target=None):
        # Risk Management Check
        if not self.risk_manager.validate_order({"stop_loss": stop_loss, "target": target}):
            return {"status": "error", "message": "Order rejected by Risk Manager: Missing SL/Target"}

        security_id = self._resolve_security_id(symbol, segment)
        if not security_id:
            self.logger.error(f"Security ID not found for symbol: {symbol}")
            return {"status": "error", "message": f"Symbol {symbol} not found in instrument master"}

        # If both legs are present, place a real broker-enforced OCO (GTT) order
        # instead of a plain order, so SL/target survive even if this app goes down.
        if stop_loss is not None and target is not None:
            return self._place_smart_order(symbol, transaction_type, quantity, order_type, product, segment, security_id, stop_loss, target)

        url = f"{self.base_url}/order"
        headers = {
            "Authorization": self.access_token,
            "Content-Type": "application/json"
        }

        payload = {
            "txn_type": transaction_type.upper(),  # BUY or SELL
            "exchange": "NSE",
            "segment": segment.upper(),
            "security_id": str(security_id),
            "qty": int(quantity),
            "order_type": order_type.upper(),
            "product": product.upper(),  # CNC, INTRADAY, MARGIN
            "validity": "DAY",
            "is_amo": False,
            "algo_id": "99999"  # Regular order
        }

        self.logger.info(f"Indstocks: Placing {transaction_type} for {symbol} (ID: {security_id})")
        # In actual use:
        # response = requests.post(url, headers=headers, json=payload)
        # return response.json()

        return {"status": "success", "broker": "Indstocks", "order_id": "IND_SIM_123"}

    def _place_smart_order(self, symbol, transaction_type, quantity, order_type, product, segment, security_id, stop_loss, target):
        """
        Places a parent order with linked SL + target child legs via the
        Smart Orders (GTT) API, so the exit is enforced broker-side (OCO:
        whichever leg triggers first cancels the other) rather than only
        being tracked in this app's RiskManager.
        """
        url = f"{self.base_url}/smart/order"
        headers = {
            "Authorization": self.access_token,
            "Content-Type": "application/json"
        }

        payload = {
            "txn_type": transaction_type.upper(),
            "exchange": "NSE",
            "segment": segment.upper(),
            "product": product.upper(),
            "order_type": order_type.upper(),
            "security_id": str(security_id),
            "qty": int(quantity),
            "algo_id": "99999",
            "sl_trigger_price": stop_loss,
            "sl_limit_price": stop_loss,
            "tgt_trigger_price": target,
            "tgt_limit_price": target,
        }

        self.logger.info(f"Indstocks: Placing {transaction_type} {quantity} {symbol} with SL={stop_loss} target={target} (smart order)")
        # In actual use:
        # response = requests.post(url, headers=headers, json=payload)
        # return response.json()

        return {
            "status": "success",
            "broker": "Indstocks",
            "order_id": "IND_SMART_SIM_123",
            "child_order_details": {"order_id": "IND_GTT_SIM_456", "order_status": "CREATED"}
        }

    def modify_order(self, order_id, segment, qty=None, limit_price=None):
        """
        Modifies a pending order's quantity and/or limit price.
        """
        url = f"{self.base_url}/order/modify"
        headers = {"Authorization": self.access_token, "Content-Type": "application/json"}
        payload = {"order_id": order_id, "segment": segment.upper()}
        if qty is not None:
            payload["qty"] = int(qty)
        if limit_price is not None:
            payload["limit_price"] = limit_price

        self.logger.info(f"Indstocks: Modifying order {order_id}")
        # In actual use:
        # response = requests.post(url, headers=headers, json=payload)
        # return response.json()

        return {"status": "success", "order_id": order_id, "order_status": "MODIFIED"}

    def cancel_order(self, order_id, segment):
        """
        Cancels a pending order.
        """
        url = f"{self.base_url}/order/cancel"
        headers = {"Authorization": self.access_token, "Content-Type": "application/json"}
        payload = {"order_id": order_id, "segment": segment.upper()}

        self.logger.info(f"Indstocks: Cancelling order {order_id}")
        # In actual use:
        # response = requests.post(url, headers=headers, json=payload)
        # return response.json()

        return {"status": "success", "order_id": order_id, "order_status": "CANCELLED"}

    def get_order_status(self, order_id):
        """
        Fetches the status of a specific order.
        """
        url = f"{self.base_url}/order/{order_id}"
        headers = {"Authorization": self.access_token}

        # In actual use:
        # response = requests.get(url, headers=headers)
        # return response.json()

        return {
            "status": "success",
            "data": {
                "order_id": order_id,
                "order_status": "COMPLETED",
                "average_price": 2450.50,
                "filled_qty": 1
            }
        }

    def get_orders(self):
        """
        Fetches all recent orders (order book).
        """
        url = f"{self.base_url}/order-book"
        headers = {"Authorization": self.access_token}

        # In actual use:
        # response = requests.get(url, headers=headers)
        # return response.json()

        return [
            {"order_id": "IND_ORD_1", "symbol": "RELIANCE", "status": "COMPLETED", "side": "BUY", "qty": 10},
            {"order_id": "IND_ORD_2", "symbol": "TCS", "status": "COMPLETED", "side": "BUY", "qty": 5},
        ]

    def get_portfolio(self):
        """
        Fetches current holdings.
        """
        url = f"{self.base_url}/portfolio/holdings"
        headers = {"Authorization": self.access_token}

        # In actual use:
        # response = requests.get(url, headers=headers)
        # return response.json()

        return {
            "status": "success",
            "data": [
                {"symbol": "RELIANCE", "qty": 10, "avg_price": 2400.0, "current_price": 2450.0, "pnl": 500.0},
                {"symbol": "TCS", "qty": 5, "avg_price": 3200.0, "current_price": 3150.0, "pnl": -250.0}
            ]
        }

    def get_positions(self, segment=None, product=None):
        """
        Fetches open derivative/equity positions (distinct from holdings).
        """
        url = f"{self.base_url}/portfolio/positions"
        headers = {"Authorization": self.access_token}
        params = {}
        if segment:
            params["segment"] = segment.lower()
        if product:
            params["product"] = product.lower()

        # In actual use:
        # response = requests.get(url, headers=headers, params=params)
        # return response.json()

        return {"status": "success", "data": {"net_positions": [], "day_positions": []}}

    def get_quote(self, symbols, mode="ltp"):
        """
        Fetches market quotes. mode: 'ltp', 'full', or 'mkt' (depth).
        symbols: list of 'SEGMENT_TOKEN' strings, e.g. ['NSE_3045'], up to 1000 per call.
        """
        endpoint = {"ltp": "ltp", "full": "full", "mkt": "mkt"}.get(mode, "ltp")
        url = f"{self.base_url}/market/quotes/{endpoint}"
        headers = {"Authorization": self.access_token}
        params = {"scrip-codes": ",".join(symbols)}

        # In actual use:
        # response = requests.get(url, headers=headers, params=params)
        # return response.json()

        return {"status": "success", "data": {s: {"live_price": 0.0} for s in symbols}}
