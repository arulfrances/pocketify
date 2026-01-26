import sys
import os
import time
import random
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.features.feature_engineer import FeatureEngineer
from src.execution.broker_gateway import ZerodhaKiteGateway

class LiveStrategyRunner:
    def __init__(self, broker_gateway, symbol="NIFTY 50"):
        self.broker = broker_gateway
        self.symbol = symbol
        # Use dtype to avoid FutureWarning with concat
        self.data_buffer = pd.DataFrame(columns=['Close']).astype('float32')
        self.fe = FeatureEngineer()
        self.position = 0 # 0 for none, 1 for long, -1 for short

    def on_tick(self, tick_data):
        """
        Simulated websocket callback.
        """
        # Append new tick to buffer
        new_row = pd.DataFrame({'Close': [tick_data['price']]}, index=[pd.Timestamp.now()]).astype('float32')
        if self.data_buffer.empty:
            self.data_buffer = new_row
        else:
            self.data_buffer = pd.concat([self.data_buffer, new_row])
        
        # Keep only last 100 ticks
        if len(self.data_buffer) > 100:
            self.data_buffer = self.data_buffer.iloc[-100:]
            
        # Run strategy logic if we have enough data
        if len(self.data_buffer) >= 50:
            self.execute_crossover_strategy()

    def execute_crossover_strategy(self):
        # Calculate SMAs
        sma_short = self.data_buffer['Close'].rolling(window=20).mean().iloc[-1]
        sma_long = self.data_buffer['Close'].rolling(window=50).mean().iloc[-1]
        
        current_price = self.data_buffer['Close'].iloc[-1]
        
        print(f"[{pd.Timestamp.now()}] Price: {current_price:.2f} | SMA20: {sma_short:.2f} | SMA50: {sma_long:.2f}")

        # Signal Logic: Simple Crossover
        if sma_short > sma_long and self.position <= 0:
            print(">>> BUY SIGNAL <<<")
            self.broker.place_order(self.symbol, "BUY", 1)
            self.position = 1
        elif sma_short < sma_long and self.position >= 0:
            print(">>> SELL SIGNAL <<<")
            self.broker.place_order(self.symbol, "SELL", 1)
            self.position = -1

    def run_mock_stream(self, duration_seconds=60):
        """
        Simulates a live price stream for testing.
        """
        print(f"Starting mock stream for {self.symbol}...")
        start_price = 21000.0
        for _ in range(duration_seconds):
            price = start_price + random.uniform(-10, 10)
            start_price = price
            self.on_tick({'price': price})
            time.sleep(1)

if __name__ == "__main__":
    # Setup dummy broker
    kite = ZerodhaKiteGateway("dummy_api_key", "dummy_access_token")
    
    # Run strategy
    runner = LiveStrategyRunner(kite, symbol="NIFTY50")
    runner.run_mock_stream(duration_seconds=120)
