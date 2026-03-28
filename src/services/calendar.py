"""
Google Calendar API client for creating and querying events.
Handles OAuth token refresh automatically.
"""
import httpx
import json
from datetime import datetime, timedelta
from utils.datetime_utils import (
    combine_datetime,
    add_minutes,
    format_datetime_for_google,
    get_date_range_today,
    get_date_range_next_7_days
)


class GoogleCalendarClient:
    """Client for Google Calendar API operations with automatic token refresh."""
    
    BASE_URL = "https://www.googleapis.com/calendar/v3"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    
    # Calendar category to calendar ID mapping
    # Note: These calendar IDs need to be configured in your environment variables
    CATEGORY_CALENDARS = {
        "Academic": "GOOGLE_CALENDAR_ID_ACADEMIC",
        "Birthdays": "GOOGLE_CALENDAR_ID_BIRTHDAYS",
        "Errands": "GOOGLE_CALENDAR_ID_ERRANDS",
        "Events": "GOOGLE_CALENDAR_ID_EVENTS",
        "Finance": "GOOGLE_CALENDAR_ID_FINANCE",
        "Holidays": "GOOGLE_CALENDAR_ID_HOLIDAYS",
        "Occupation": "GOOGLE_CALENDAR_ID_OCCUPATION",
        "Passion": "GOOGLE_CALENDAR_ID_PASSION"
    }
    
    def __init__(self, access_token, refresh_token=None, client_id=None, client_secret=None, env=None):
        """
        Initialize Google Calendar client.
        
        Args:
            access_token: Google OAuth 2.0 access token
            refresh_token: Refresh token for automatic token renewal (optional)
            client_id: OAuth client ID (required if using refresh token)
            client_secret: OAuth client secret (required if using refresh token)
            env: Environment object containing calendar IDs (optional)
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_expiry = None
        self.env = env
    
    async def _get_headers(self):
        """Get authorization headers, refreshing token if needed."""
        # If we have refresh capability and token might be expired, refresh it
        if self.refresh_token and self.client_id and self.client_secret:
            # Try to refresh if we don't have an expiry or if it's close to expiring
            if self.token_expiry is None or datetime.now() >= self.token_expiry - timedelta(minutes=5):
                await self._refresh_access_token()
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def _refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        try:
            print("Refreshing Google Calendar access token...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": self.refresh_token,
                        "grant_type": "refresh_token"
                    },
                    headers={"Accept-Encoding": "identity"},  # Disable compression
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Token refresh failed: {response.status_code} - {response.text}")
                
                data = response.json()
                self.access_token = data["access_token"]
                
                # Set expiry time (tokens typically last 1 hour)
                expires_in = data.get("expires_in", 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                print(f"✅ Token refreshed successfully. Expires in {expires_in} seconds.")
                
        except Exception as e:
            print(f"Error refreshing token: {e}")
            # Continue with existing token and hope it works
    
    async def create_event(self, title, date_str, time_str, duration_minutes=60, 
                          location=None, description=None, category=None):
        """
        Create a calendar event.
        
        Args:
            title: Event title/summary
            date_str: Date in YYYY-MM-DD format
            time_str: Time in HH:MM format
            duration_minutes: Event duration in minutes (default: 60)
            location: Event location (optional)
            description: Event description (optional)
            category: Calendar category (Academic/Birthdays/Errands/Events/Finance/Occupation/Passion)
            
        Returns:
            dict: Created event data from Google Calendar
            
        Raises:
            Exception: If event creation fails
        """
        try:
            # Combine date and time
            start_dt = combine_datetime(date_str, time_str)
            end_dt = add_minutes(start_dt, duration_minutes)
            
            # Determine which calendar to use
            calendar_id = "primary"
            if category and self.env:
                env_var_name = self.CATEGORY_CALENDARS.get(category)
                if env_var_name and hasattr(self.env, env_var_name):
                    calendar_id = getattr(self.env, env_var_name)
            
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
            
            # Get headers (with token refresh if needed)
            headers = await self._get_headers()
            headers["Accept-Encoding"] = "identity"  # Disable compression
            
            # Create event via API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/calendars/{calendar_id}/events",
                    headers=headers,
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
        Get all events for today from all calendars.
        
        Returns:
            list: List of event objects
        """
        start_dt, end_dt = get_date_range_today()
        return await self._get_events_all_calendars(start_dt, end_dt)
    
    async def get_events_next_7_days(self):
        """
        Get all events for the next 7 days from all calendars.
        
        Returns:
            list: List of event objects
        """
        start_dt, end_dt = get_date_range_next_7_days()
        return await self._get_events_all_calendars(start_dt, end_dt)
    async def delete_event(self, event_id, calendar_id="primary"):
        """
        Delete a calendar event.

        Args:
            event_id: Google Calendar event ID
            calendar_id: Calendar ID (default: "primary")

        Returns:
            bool: True if deletion successful

        Raises:
            Exception: If event deletion fails
        """
        try:
            # Get headers (with token refresh if needed)
            headers = await self._get_headers()

            # Use JS fetch API directly to avoid httpx issues with empty responses
            from js import fetch
            from pyodide.ffi import to_js
            from js import Object

            url = f"{self.BASE_URL}/calendars/{calendar_id}/events/{event_id}"

            # Build fetch options
            options = to_js({
                "method": "DELETE",
                "headers": headers
            }, dict_converter=Object.fromEntries)

            print(f"Deleting event {event_id} from calendar {calendar_id}")

            # Make the request
            response = await fetch(url, options)
            status = response.status

            print(f"Delete event response status: {status}")

            # Check status code (DELETE returns 204 No Content on success)
            if status not in [200, 204]:
                raise Exception(f"Google Calendar API error: {status}")

            print(f"✅ Successfully deleted event {event_id}")
            return True

        except Exception as e:
            print(f"Error deleting calendar event: {e}")
            raise Exception(f"Failed to delete calendar event: {str(e)}")
    
    async def _get_events_all_calendars(self, start_dt, end_dt):
        """
        Get events from all calendars within a date range.
        
        Args:
            start_dt: Start datetime
            end_dt: End datetime
            
        Returns:
            list: Combined list of event objects from all calendars
        """
        all_events = []
        
        # Get calendar IDs to query
        calendar_ids = ["primary"]
        
        # Add category calendars if configured
        if self.env:
            for category, env_var_name in self.CATEGORY_CALENDARS.items():
                if hasattr(self.env, env_var_name):
                    calendar_id = getattr(self.env, env_var_name)
                    if calendar_id:
                        calendar_ids.append(calendar_id)
                        print(f"Including calendar: {category} ({calendar_id})")
        
        # Query each calendar
        for calendar_id in calendar_ids:
            try:
                events = await self._get_events(calendar_id, start_dt, end_dt)
                all_events.extend(events)
                print(f"✅ Fetched {len(events)} events from calendar: {calendar_id}")
            except Exception as e:
                print(f"⚠️ Error fetching from calendar {calendar_id}: {e}")
                continue
        
        # Sort all events by start time
        all_events.sort(key=lambda e: e.get("start", {}).get("dateTime", ""))
        
        print(f"📅 Total events fetched: {len(all_events)}")
        return all_events
    
    async def _get_events(self, calendar_id, start_dt, end_dt):
        """
        Get events from a specific calendar within a date range.
        
        Args:
            calendar_id: Calendar ID to query
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
            
            # Get headers (with token refresh if needed)
            headers = await self._get_headers()
            headers["Accept-Encoding"] = "identity"  # Disable compression
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/calendars/{calendar_id}/events",
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"❌ Google Calendar API error for {calendar_id}: {response.status_code} - {error_text}")
                    raise Exception(f"Google Calendar API error: {response.status_code}")
                
                data = response.json()
                return data.get("items", [])
                
        except Exception as e:
            print(f"Error fetching calendar events from {calendar_id}: {e}")
            raise

