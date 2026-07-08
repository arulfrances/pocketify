import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

from src.execution.brokers import KotakNeoGateway, PaytmMoneyGateway, IndstocksGateway, AngelOneGateway
from src.execution.live_strategy import LiveStrategyRunner

load_dotenv()

def start_trading(broker_name="kotak"):
    print(f"--- Starting Prostock with {broker_name} ---")

    # Initialize the chosen broker with credentials from .env
    if broker_name.lower() == "kotak":
        broker = KotakNeoGateway(
            api_key=os.getenv("KOTAK_API_KEY", "dummy"),
            access_token=os.getenv("KOTAK_ACCESS_TOKEN", "dummy"),
            consumer_secret=os.getenv("KOTAK_CONSUMER_SECRET", "dummy"),
            phone_number=os.getenv("KOTAK_PHONE", "9999999999"),
            mpin=os.getenv("KOTAK_MPIN", "1234")
        )
    elif broker_name.lower() == "paytm":
        broker = PaytmMoneyGateway(
            api_key=os.getenv("PAYTM_API_KEY", "dummy"),
            access_token=os.getenv("PAYTM_ACCESS_TOKEN", "dummy")
        )
    elif broker_name.lower() == "indstocks":
        broker = IndstocksGateway(
            api_key=os.getenv("IND_API_KEY", "dummy"),
            access_token=os.getenv("IND_ACCESS_TOKEN", "dummy")
        )
    elif broker_name.lower() == "angelone":
        broker = AngelOneGateway(
            api_key=os.getenv("ANGELONE_API_KEY", "dummy"),
            client_code=os.getenv("ANGELONE_CLIENT_CODE", "dummy"),
            password=os.getenv("ANGELONE_PASSWORD", "dummy"),
            totp_secret=os.getenv("ANGELONE_TOTP_SECRET", "")
        )
    else:
        print("Invalid broker selected.")
        return

    # Run the strategy (currently simulated stream)
    runner = LiveStrategyRunner(broker, symbol="NIFTY 50")
    
    # In a real scenario, you'd use the broker's WebSocket for real ticks
    # For now, we use our mock stream to verify the signal -> execution flow
    runner.run_mock_stream(duration_seconds=30)

if __name__ == "__main__":
    # Change this to 'paytm', 'indstocks', or 'angelone' to switch brokers
    selected_broker = "kotak"
    start_trading(selected_broker)
