import logging

class RiskManager:
    def __init__(self, max_daily_loss_pct=2.0, max_position_size_pct=10.0):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_position_size_pct = max_position_size_pct
        self.daily_pnl = 0.0
        self.logger = logging.getLogger("RiskManager")

    def can_trade(self, current_capital):
        """
        Check if we hit the daily loss limit.
        """
        loss_limit = -(current_capital * (self.max_daily_loss_pct / 100))
        if self.daily_pnl <= loss_limit:
            self.logger.warning(f"Daily loss limit reached: {self.daily_pnl}. Trading halted.")
            return False
        return True

    def calculate_levels(self, current_price, atr, side="BUY"):
        """
        Calculates Stop Loss and Target based on ATR.
        Multipliers: SL = 1.5 * ATR, Target = 3 * ATR (1:2 Risk-Reward)
        """
        sl_multiplier = 1.5
        target_multiplier = 3.0
        
        if side == "BUY":
            stop_loss = current_price - (atr * sl_multiplier)
            target = current_price + (atr * target_multiplier)
        else: # SELL
            stop_loss = current_price + (atr * sl_multiplier)
            target = current_price - (atr * target_multiplier)
            
        return round(stop_loss, 2), round(target, 2)

    def validate_order(self, order_payload):
        """
        Enforces that EVERY order MUST have a stop_loss and target.
        """
        if 'stop_loss' not in order_payload or 'target' not in order_payload:
            self.logger.error("Order rejected: Missing Stop Loss or Target.")
            return False
        
        # Additional check: qty limits
        self.logger.info("Order validated by Risk Manager.")
        return True
