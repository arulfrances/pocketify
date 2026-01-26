import pandas as pd
import numpy as np

class FeatureEngineer:
    def __init__(self):
        pass

    def add_technical_indicators(self, df):
        """
        Adds basic technical indicators to the dataframe.
        """
        df = df.copy()
        
        # Ensure we have a single Close column for calculations
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten or select the first level if possible
            # yfinance 1.x returns MultiIndex if only one ticker is requested sometimes
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

        print(f"Data size before indicators: {df.shape}")
        
        # Simple Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Relative Strength Index (RSI)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df['RSI'] = 100 - (100 / (1 + rs.fillna(0)))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        df['BB_Mid'] = df['Close'].rolling(window=20).mean()
        df['BB_Std'] = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * 2)
        df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * 2)

        # ATR (Average True Range) - Used for SL/Target
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Daily Returns and Volatility
        df['Returns'] = df['Close'].pct_change()
        df['Volatility'] = df['Returns'].rolling(window=21).std()
        
        # Target: Next day's direction
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(float)
        
        # Lagged features
        for lag in range(1, 6):
            df[f'Lag_Return_{lag}'] = df['Returns'].shift(lag)
            
        print(f"Data size before dropna: {df.shape}")
        result = df.dropna()
        print(f"Data size after dropna: {result.shape}")
        return result

if __name__ == "__main__":
    # Test with dummy data
    data = {
        'Close': np.random.randn(100).cumsum() + 100
    }
    df = pd.DataFrame(data)
    fe = FeatureEngineer()
    df_features = fe.add_technical_indicators(df)
    print(df_features.head())
