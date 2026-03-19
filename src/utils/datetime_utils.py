"""
Datetime utilities for Vancouver timezone (America/Vancouver).
Handles PST/PDT conversions and date/time formatting.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


VANCOUVER_TZ = ZoneInfo("America/Vancouver")


def get_current_time():
    """
    Get current datetime in Vancouver timezone.
    
    Returns:
        datetime: Current time in America/Vancouver timezone
    """
    return datetime.now(VANCOUVER_TZ)


def parse_date_string(date_str):
    """
    Parse date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string (e.g., "2026-03-21")
        
    Returns:
        datetime.date: Parsed date object
    """
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def parse_time_string(time_str):
    """
    Parse time string in HH:MM format.
    
    Args:
        time_str: Time string (e.g., "14:00")
        
    Returns:
        datetime.time: Parsed time object
    """
    return datetime.strptime(time_str, "%H:%M").time()


def combine_datetime(date_str, time_str):
    """
    Combine date and time strings into Vancouver timezone datetime.
    
    Args:
        date_str: Date string (YYYY-MM-DD)
        time_str: Time string (HH:MM)
        
    Returns:
        datetime: Combined datetime in Vancouver timezone
    """
    date_obj = parse_date_string(date_str)
    time_obj = parse_time_string(time_str)
    
    # Combine and localize to Vancouver timezone
    dt = datetime.combine(date_obj, time_obj)
    return dt.replace(tzinfo=VANCOUVER_TZ)


def format_datetime_for_google(dt):
    """
    Format datetime for Google Calendar API (RFC3339).
    
    Args:
        dt: datetime object with timezone
        
    Returns:
        str: RFC3339 formatted datetime string
    """
    return dt.isoformat()


def add_minutes(dt, minutes):
    """
    Add minutes to a datetime.
    
    Args:
        dt: datetime object
        minutes: Number of minutes to add
        
    Returns:
        datetime: New datetime with minutes added
    """
    return dt + timedelta(minutes=minutes)


def get_date_range_today():
    """
    Get start and end datetime for today in Vancouver timezone.
    
    Returns:
        tuple: (start_datetime, end_datetime) for today
    """
    now = get_current_time()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def get_date_range_this_week():
    """
    Get start and end datetime for this week (today through Sunday).
    
    Returns:
        tuple: (start_datetime, end_datetime) for this week
    """
    now = get_current_time()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate days until Sunday (6 = Sunday in weekday())
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7  # If today is Sunday, go to next Sunday
    
    end = start + timedelta(days=days_until_sunday)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return start, end


def format_date_friendly(date_str):
    """
    Format date string to friendly format (e.g., "Friday, March 21").
    
    Args:
        date_str: Date string (YYYY-MM-DD)
        
    Returns:
        str: Friendly formatted date
    """
    date_obj = parse_date_string(date_str)
    return date_obj.strftime("%A, %B %d")


def format_time_friendly(time_str):
    """
    Format time string to friendly format (e.g., "2:00 PM").
    
    Args:
        time_str: Time string (HH:MM)
        
    Returns:
        str: Friendly formatted time
    """
    time_obj = parse_time_string(time_str)
    return time_obj.strftime("%I:%M %p").lstrip("0")
