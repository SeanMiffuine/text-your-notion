"""
Datetime utilities for Vancouver timezone (America/Vancouver).
Handles PST/PDT conversions and date/time formatting.
"""
from datetime import datetime, timedelta, timezone


# Vancouver timezone offset (PST is UTC-8, PDT is UTC-7)
# We'll use a simple approach since zoneinfo isn't available in Workers
PST_OFFSET = timezone(timedelta(hours=-8))
PDT_OFFSET = timezone(timedelta(hours=-7))


def _get_vancouver_offset():
    """
    Determine if we're in PST or PDT based on daylight saving rules.
    DST in North America: Second Sunday in March to First Sunday in November
    """
    now_utc = datetime.now(timezone.utc)
    year = now_utc.year
    
    # Calculate DST start (second Sunday in March)
    march_first = datetime(year, 3, 1, 2, 0, 0, tzinfo=timezone.utc)
    days_to_sunday = (6 - march_first.weekday()) % 7
    dst_start = march_first + timedelta(days=days_to_sunday + 7)
    
    # Calculate DST end (first Sunday in November)
    nov_first = datetime(year, 11, 1, 2, 0, 0, tzinfo=timezone.utc)
    days_to_sunday = (6 - nov_first.weekday()) % 7
    dst_end = nov_first + timedelta(days=days_to_sunday)
    
    # Check if we're in DST period
    if dst_start <= now_utc < dst_end:
        return PDT_OFFSET  # UTC-7
    else:
        return PST_OFFSET  # UTC-8


def get_current_time():
    """
    Get current datetime in Vancouver timezone.
    
    Returns:
        datetime: Current time in America/Vancouver timezone
    """
    utc_now = datetime.now(timezone.utc)
    vancouver_offset = _get_vancouver_offset()
    return utc_now.astimezone(vancouver_offset)


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
    vancouver_offset = _get_vancouver_offset()
    return dt.replace(tzinfo=vancouver_offset)


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
