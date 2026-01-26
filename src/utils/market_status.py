from datetime import datetime, time
import pytz

def is_market_open():
    """
    Checks if the Indian Stock Market (NSE/BSE) is currently open.
    Hours: 9:15 AM - 3:30 PM IST, Monday to Friday.
    """
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Check if it's a weekend
    if now.weekday() >= 5:
        return False, "Market Closed (Weekend)"
    
    # Indian Market Holidays (Simplified list - Can be expanded)
    holidays = [
        "2026-01-26", # Republic Day
        "2026-03-06", # Holi
        "2026-04-02", # Ram Navami
        "2026-05-01", # Maharashtra Day
        "2026-08-15", # Independence Day
        "2026-10-02", # Gandhi Jayanti
        "2026-12-25", # Christmas
    ]
    
    if now.strftime("%Y-%m-%d") in holidays:
        return False, "Market Closed (Holiday)"
    
    # Check time
    market_start = time(9, 15)
    market_end = time(15, 30)
    current_time = now.time()
    
    if market_start <= current_time <= market_end:
        return True, "Market Open"
    elif current_time < market_start:
        return False, "Market Opening Soon"
    else:
        return False, "Market Closed"
