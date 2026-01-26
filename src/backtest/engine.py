import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self, initial_capital=100000.0):
        self.initial_capital = initial_capital

    def run_backtest(self, df, predictions):
        """
        Runs a simple backtest based on model predictions.
        Assumes predictions are aligned with the test set of the dataframe.
        """
        results = df.copy()
        results['Signal'] = predictions
        
        # Calculate daily returns
        results['Daily_Return'] = results['Close'].pct_change()
        
        # Strategy Return: If Signal is 1 (BUY), we get the next day's return
        # Signal is for 'tomorrow', so we multiply signal by the 'tomorrow' return
        results['Strategy_Return'] = results['Signal'].shift(1) * results['Daily_Return']
        results['Strategy_Return'] = results['Strategy_Return'].fillna(0)

        # Cumulative Returns
        results['Cum_Market_Return'] = (1 + results['Daily_Return']).cumprod()
        results['Cum_Strategy_Return'] = (1 + results['Strategy_Return']).cumprod()

        # Metrics
        total_return = (results['Cum_Strategy_Return'].iloc[-1] - 1) * 100
        market_return = (results['Cum_Market_Return'].iloc[-1] - 1) * 100
        
        # Sharpe Ratio (annualized, assuming 252 trading days)
        sharpe = (results['Strategy_Return'].mean() / results['Strategy_Return'].std()) * np.sqrt(252) if results['Strategy_Return'].std() != 0 else 0
        
        # Max Drawdown
        cum_ret = results['Cum_Strategy_Return']
        rolling_max = cum_ret.cummax()
        drawdown = (cum_ret - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100

        return {
            "total_return": float(total_return),
            "market_return": float(market_return),
            "sharpe_ratio": float(sharpe),
            "max_drawdown": float(max_drawdown),
            "equity_curve": results[['Cum_Strategy_Return', 'Cum_Market_Return']].tail(100).to_dict(orient='list')
        }

if __name__ == "__main__":
    # Test with dummy data
    pass
