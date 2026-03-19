"""
Google Calendar API client for creating and querying events.
"""
import httpx
from src.utils.datetime_utils import (
    combine_datetime,
    add_minutes,
    format_datetime_for_google,
    get_date_range_today,
    get_date_range_this_week
)


class GoogleCalendarClient:
    """Client for Google Calendar API operations."""
    
    BASE_URL = "https://www.googleapis.com/calendar/v3"
    
    def __init__(self, oauth_token):
        """
        Initialize Google Calendar client.
        
        Args:
            oauth_token: Google OAuth 2.0 access token
        """
        self.oauth_token = oauth_token
        self.headers = {
            "Authorization": f"Bearer {oauth_token}",
            "Content-Type": "application/json"
        }
    
    async def create_event(self, title, date_str, time_str, duration_minutes=60, 
                          location=None, description=None):
        """
        Create a calendar event.
        
        Args:
            title: Event title/summary
            date_str: Date in YYYY-MM-DD format
            time_str: Time in HH:MM format
            duration_minutes: Event duration in minutes (default: 60)
            location: Event location (optional)
            description: Event description (optional)
            
        Returns:
            dict: Created event data from Google Calendar
            
        Raises:
            Exception: If event creation fails
        """
        try:
            # Combine date and time
            start_dt = combine_datetime(date_str, time_str)
            end_dt = add_minutes(start_dt, duration_minutes)
            
            # Build event object
            event = {
                "summary": title,
                "start": {
                    "dateTime": format_datetime_for_google(start_dt),
                    "timeZone": "America/Vancouver"
                },
                "end": {
                    "dateTime": format_datetime_for_google(end_dt),
                    "timeZone": "America/Vancouver"
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 30}
                    ]
                }
            }
            
            # Add optional fields
            if location:
                event["location"] = location
            
            if description:
                event["description"] = description
            
            # Create event via API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/calendars/primary/events",
                    headers=self.headers,
                    json=event,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Google Calendar API error: {response.status_code} - {response.text}")
                
                return response.json()
                
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            raise Exception(f"Failed to create calendar event: {str(e)}")
    
    async def get_events_today(self):
        """
        Get all events for today.
        
        Returns:
            list: List of event objects
        """
        start_dt, end_dt = get_date_range_today()
        return await self._get_events(start_dt, end_dt)
    
    async def get_events_this_week(self):
        """
        Get all events for this week (today through Sunday).
        
        Returns:
            list: List of event objects
        """
        start_dt, end_dt = get_date_range_this_week()
        return await self._get_events(start_dt, end_dt)
    
    async def _get_events(self, start_dt, end_dt):
        """
        Get events within a date range.
        
        Args:
            start_dt: Start datetime
            end_dt: End datetime
            
        Returns:
            list: List of event objects
        """
        try:
            params = {
                "timeMin": format_datetime_for_google(start_dt),
                "timeMax": format_datetime_for_google(end_dt),
                "singleEvents": True,
                "orderBy": "startTime"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/calendars/primary/events",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Google Calendar API error: {response.status_code}")
                
                data = response.json()
                return data.get("items", [])
                
        except Exception as e:
            print(f"Error fetching calendar events: {e}")
            return []
