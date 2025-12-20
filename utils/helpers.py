import datetime
import pytz

def is_time_in_range(start_time_str, end_time_str, current_time):
    """
    Checks if current_time is between start_time and end_time (hh:mm).
    """
    start_time = datetime.datetime.strptime(start_time_str, "%H:%M").time()
    end_time = datetime.datetime.strptime(end_time_str, "%H:%M").time()
    current_time_time = current_time.time()

    if start_time <= end_time:
        return start_time <= current_time_time <= end_time
    else: # Over midnight
        return start_time <= current_time_time or current_time_time <= end_time

def check_trading_session(config):
    """
    Verifies if the current time is within allowed trading sessions.
    """
    # Assuming Broker Time is UTC for this generic implementation
    # In production, fetch symbol time from MT5
    current_time = datetime.datetime.now(datetime.timezone.utc)
    
    # 1. Day Check (Avoid Weekly First Trading Day - usually Monday early hours)
    # Weekday: 0=Mon, 6=Sun. 
    # Logic: if Monday, maybe strict filter. 
    # User said: "Avoid weekly first trading day". 
    # Interpreted as: Avoid Monday Asian Session or just Monday entirety?
    # Let's be safe: If Monday, return False? Or just first few hours?
    # Common practice: Skip first 2-4 hours of market open.
    # For now, let's keep it simple: Trade Tue-Fri for safety if requested "Avoid first day" often means Monday.
    if current_time.weekday() == 0: # Monday
        return False
    if current_time.weekday() >= 5: # Sat/Sun
        return False

    # 2. Session Check
    is_asian = is_time_in_range(config['sessions']['asian_start'], config['sessions']['asian_end'], current_time)
    is_london = is_time_in_range(config['sessions']['london_mid_start'], config['sessions']['london_mid_end'], current_time)

    return is_asian or is_london

def check_news_impact():
    """
    Placeholder for news filter.
    Returns True if safe to trade (no news), False if high impact news.
    """
    # TODO: Integrate valid news API (ForexFactory, etc.)
    return True
