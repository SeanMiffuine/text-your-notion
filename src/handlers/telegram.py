"""
Telegram message handler for processing user messages.
"""
from services.ai_parser import parse_message
from services.calendar import GoogleCalendarClient
from services.notion import NotionClient
from utils.datetime_utils import (
    get_current_time,
    format_date_friendly,
    format_time_friendly
)


async def handle_message(env, chat_id, message_text):
    """
    Process incoming Telegram message and create event/todo.
    
    Args:
        env: Cloudflare Worker environment (contains API keys and AI binding)
        chat_id: Telegram chat ID to send response to
        message_text: User's message text
        
    Returns:
        str: Response message to send back to user
    """
    try:
        # Get current time in Vancouver timezone
        current_time = get_current_time()
        
        # Parse message with AI
        parsed_data = await parse_message(
            env.AI,
            message_text,
            current_time
        )
        
        # Determine if event or todo
        item_type = parsed_data['item_type']
        title = parsed_data['title']
        date_str = parsed_data['date']
        
        if item_type == 'event':
            # Create calendar event
            time_str = parsed_data.get('time')
            duration = parsed_data.get('duration_minutes', 60)
            location = parsed_data.get('location')
            description = parsed_data.get('description')
            
            if not time_str:
                return "⚠️ I need a specific time to create a calendar event. Try: 'Meeting tomorrow at 2pm'"
            
            # Initialize Google Calendar client
            calendar_client = GoogleCalendarClient(
                access_token=env.GOOGLE_CALENDAR_ACCESS_TOKEN,
                refresh_token=env.GOOGLE_CALENDAR_REFRESH_TOKEN,
                client_id=env.GOOGLE_CALENDAR_CLIENT_ID,
                client_secret=env.GOOGLE_CALENDAR_CLIENT_SECRET
            )
            
            # Create event
            event = await calendar_client.create_event(
                title=title,
                date_str=date_str,
                time_str=time_str,
                duration_minutes=duration,
                location=location,
                description=description
            )
            
            # Format confirmation message
            date_friendly = format_date_friendly(date_str)
            time_friendly = format_time_friendly(time_str)
            
            response = f"✅ **Event created!**\n\n"
            response += f"📅 {title}\n"
            response += f"🕐 {date_friendly} at {time_friendly}\n"
            response += f"⏱️ Duration: {duration} minutes\n"
            
            if location:
                response += f"📍 {location}\n"
            
            if description:
                response += f"📝 {description}\n"
            
            return response
            
        else:  # todo
            # Create Notion todo
            description = parsed_data.get('description')
            
            # Initialize Notion client
            notion_client = NotionClient(
                env.NOTION_API_KEY,
                env.NOTION_DATABASE_ID
            )
            
            # Create todo
            page = await notion_client.create_todo(
                title=title,
                date_str=date_str,
                description=description
            )
            
            # Format confirmation message
            date_friendly = format_date_friendly(date_str)
            
            response = f"✅ **Todo created!**\n\n"
            response += f"☑️ {title}\n"
            response += f"📅 Due: {date_friendly}\n"
            
            if description:
                response += f"📝 {description}\n"
            
            return response
            
    except Exception as e:
        # Return error message
        error_msg = str(e)
        print(f"Error handling message: {error_msg}")
        return f"❌ {error_msg}"
