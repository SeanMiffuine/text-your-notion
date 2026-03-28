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

# Track last created item for quick cancellation
# Format: {"type": "event"|"todo", "id": "...", "title": "...", "calendar_id": "..."}
last_created_item = None


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
    global last_created_item
    
    try:
        # Check for cancellation keywords
        cancel_keywords = ["cancel", "delete", "undo", "nevermind", "never mind"]
        message_lower = message_text.lower().strip()
        
        if any(keyword in message_lower for keyword in cancel_keywords):
            return await handle_cancellation(env)
        
        # Continue with normal event/todo creation
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
            category = parsed_data.get('category')
            
            if not time_str:
                return "I need a specific time to create a calendar event.'"
            
            # Initialize Google Calendar client
            calendar_client = GoogleCalendarClient(
                access_token=env.GOOGLE_CALENDAR_ACCESS_TOKEN,
                refresh_token=env.GOOGLE_CALENDAR_REFRESH_TOKEN,
                client_id=env.GOOGLE_CALENDAR_CLIENT_ID,
                client_secret=env.GOOGLE_CALENDAR_CLIENT_SECRET,
                env=env
            )
            
            # Determine which calendar to use
            calendar_id = "primary"
            if category and env:
                env_var_name = GoogleCalendarClient.CATEGORY_CALENDARS.get(category)
                if env_var_name and hasattr(env, env_var_name):
                    calendar_id = getattr(env, env_var_name)
            
            # Create event
            event = await calendar_client.create_event(
                title=title,
                date_str=date_str,
                time_str=time_str,
                duration_minutes=duration,
                location=location,
                description=description,
                category=category
            )
            
            # Store for quick cancellation
            last_created_item = {
                "type": "event",
                "id": event["id"],
                "title": title,
                "calendar_id": calendar_id
            }
            
            # Format confirmation message
            date_friendly = format_date_friendly(date_str)
            
            # Calculate end time for time range display
            from datetime import datetime, timedelta
            start_time = datetime.strptime(time_str, "%H:%M")
            end_time = start_time + timedelta(minutes=duration)
            time_range = f"{start_time.strftime('%I:%M %p').lstrip('0')}-{end_time.strftime('%I:%M %p').lstrip('0')}"
            
            response = f"✅ Event created!\n\n"
            response += f"📅 {title}\n"
            response += f"🕐 {date_friendly} at {time_range}\n"
            
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
            
            # Store for quick cancellation
            last_created_item = {
                "type": "todo",
                "id": page["id"],
                "title": title
            }
            
            # Format confirmation message
            date_friendly = format_date_friendly(date_str)
            
            response = f"✅ Todo created!\n\n"
            response += f"☑️ {title}\n"
            response += f"📅 Due: {date_friendly}\n"
            
            if description:
                response += f"📝 {description}\n"
            
            return response
            
    except Exception as e:
        # Return error message
        error_msg = str(e)
        print(f"Error handling message: {error_msg}")
        return "❌ Couldn't parse that. Please rephrase."



async def handle_cancellation(env):
    """
    Handle cancellation of the last created item.
    
    Args:
        env: Cloudflare Worker environment
        
    Returns:
        str: Response message confirming cancellation or error
    """
    global last_created_item
    
    if not last_created_item:
        return "Nothing to cancel. Create an event or todo first."
    
    try:
        item_type = last_created_item["type"]
        item_id = last_created_item["id"]
        item_title = last_created_item["title"]
        
        if item_type == "event":
            # Delete calendar event
            calendar_id = last_created_item.get("calendar_id", "primary")
            print(f"Attempting to delete event {item_id} from calendar {calendar_id}")
            
            calendar_client = GoogleCalendarClient(
                access_token=env.GOOGLE_CALENDAR_ACCESS_TOKEN,
                refresh_token=env.GOOGLE_CALENDAR_REFRESH_TOKEN,
                client_id=env.GOOGLE_CALENDAR_CLIENT_ID,
                client_secret=env.GOOGLE_CALENDAR_CLIENT_SECRET,
                env=env
            )
            
            result = await calendar_client.delete_event(item_id, calendar_id)
            print(f"Delete event result: {result}")
            
            # Clear stored item
            last_created_item = None
            
            return f"🗑️ Cancelled event: {item_title}"
            
        else:  # todo
            # Delete Notion todo
            notion_client = NotionClient(
                env.NOTION_API_KEY,
                env.NOTION_DATABASE_ID
            )
            await notion_client.delete_todo(item_id)
            
            # Clear stored item
            last_created_item = None
            
            return f"🗑️ Cancelled todo: {item_title}"
            
    except Exception as e:
        print(f"Error cancelling item: {e}")
        # Clear the item anyway since it might be invalid
        last_created_item = None
        return f"❌ Couldn't cancel: {str(e)}"
