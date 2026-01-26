import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, classification_report
import os

class ModelTrainer:
    def __init__(self, model_dir="src/models/saved_models"):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)

    def train_xgboost(self, df, features, target='Target'):
        """
        Trains an XGBoost model with a simple time-series split.
        """
        # Ensure target is integer and clean data
        df = df.dropna().copy()
        df[target] = df[target].astype(int)
        
        # Time-series split: use last 20% for testing
        split_idx = int(len(df) * 0.8)
        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]
        
        X_train = train_df[features]
        y_train = train_df[target]
        X_test = test_df[features]
        y_test = test_df[target]
        
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.05,
            random_state=42,
            eval_metric='logloss',
            objective='binary:logistic',
            base_score=0.5
        )
        
        model.fit(X_train, y_train)
        
        # Predictions
        y_pred = model.predict(X_test)
        
        print("XGBoost Model Performance:")
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Accuracy: {accuracy:.4f}")
        print(classification_report(y_test, y_pred))
        
        # Save model
        model_path = os.path.join(self.model_dir, "xgboost_baseline.json")
        model.save_model(model_path)
        print(f"Model saved to {model_path}")
        
        return model

    def load_model(self):
        """
        Loads the saved XGBoost model.
        """
        model_path = os.path.join(self.model_dir, "xgboost_baseline.json")
        if not os.path.exists(model_path):
            return None
            
        model = xgb.XGBClassifier()
        model.load_model(model_path)
        return model

    def predict_latest(self, df, features):
        """
        Predicts using the last row of the provided dataframe.
        """
        model = self.load_model()
        if model is None:
            return None
            
        latest_data = df[features].iloc[-1:].values
        prediction = model.predict(latest_data)[0]
        # Get probability
        prob = model.predict_proba(latest_data)[0]
        confidence = prob[1] if prediction == 1 else prob[0]
        
        return {
            "signal": "BUY" if prediction == 1 else "SELL",
            "confidence": float(confidence)
        }

if __name__ == "__main__":
    # This would be called from a main pipeline script
    pass
