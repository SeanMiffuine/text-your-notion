"""
Morning briefing handler for generating daily summaries.
"""
from services.calendar import GoogleCalendarClient
from services.notion import NotionClient
from utils.datetime_utils import get_current_time, get_date_range_today


async def generate_briefing(env):
    """
    Generate morning briefing with today's and this week's events/todos.
    
    Args:
        env: Cloudflare Worker environment (contains API keys and AI binding)
        
    Returns:
        str: Formatted briefing message
    """
    try:
        print("🌅 Starting briefing generation...")
        
        # Initialize clients
        calendar_client = GoogleCalendarClient(
            access_token=env.GOOGLE_CALENDAR_ACCESS_TOKEN,
            refresh_token=env.GOOGLE_CALENDAR_REFRESH_TOKEN,
            client_id=env.GOOGLE_CALENDAR_CLIENT_ID,
            client_secret=env.GOOGLE_CALENDAR_CLIENT_SECRET,
            env=env  # Pass env for calendar IDs
        )
        notion_client = NotionClient(env.NOTION_API_KEY, env.NOTION_DATABASE_ID)
        
        print("✅ Clients initialized")
        
        # Fetch data
        print("📅 Fetching today's events...")
        events_today = await calendar_client.get_events_today()
        print(f"✅ Found {len(events_today)} events today")
        
        print("📅 Fetching this week's events...")
        events_week_all = await calendar_client.get_events_this_week()
        print(f"✅ Found {len(events_week_all)} events this week (including today)")
        
        # Filter out today's events from this week's events to avoid duplicates
        from datetime import datetime
        today_start, today_end = get_date_range_today()
        
        events_week = []
        for event in events_week_all:
            # Get event start time
            start = event.get("start", {})
            start_datetime = start.get("dateTime", "")
            start_date = start.get("date", "")
            
            # Parse event datetime
            event_dt = None
            if start_datetime:
                try:
                    event_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                except:
                    pass
            elif start_date:
                try:
                    # For all-day events, parse as date and add timezone
                    event_dt = datetime.fromisoformat(start_date)
                    # Make it timezone-aware to match today_start/today_end
                    event_dt = event_dt.replace(tzinfo=today_start.tzinfo)
                except:
                    pass
            
            # Only include if not today
            if event_dt:
                # Ensure both are timezone-aware for comparison
                if event_dt.tzinfo is None:
                    event_dt = event_dt.replace(tzinfo=today_start.tzinfo)
                
                if event_dt < today_start or event_dt > today_end:
                    events_week.append(event)
            else:
                # If we can't parse, include it to be safe
                events_week.append(event)
        
        print(f"✅ Filtered to {len(events_week)} events this week (excluding today)")
        
        print("☑️ Fetching today's todos...")
        todos_today = await notion_client.get_todos_today()
        print(f"✅ Found {len(todos_today)} todos today")
        
        print("☑️ Fetching this week's todos...")
        todos_week_all = await notion_client.get_todos_this_week()
        print(f"✅ Found {len(todos_week_all)} todos this week (including today)")
        
        # Filter out today's todos from this week's todos
        todos_week = []
        for todo in todos_week_all:
            props = todo.get("properties", {})
            due_date = props.get("Due Date", {}).get("date", {}).get("start", "")
            
            # Parse due date
            if due_date:
                try:
                    todo_dt = datetime.fromisoformat(due_date)
                    # Only include if not today
                    if todo_dt.date() != today_start.date():
                        todos_week.append(todo)
                except:
                    todos_week.append(todo)  # Include if can't parse
            else:
                todos_week.append(todo)  # Include if no date
        
        print(f"✅ Filtered to {len(todos_week)} todos this week (excluding today)")
        
        # Get current time
        current_time = get_current_time()
        
        # Build context for LLM
        context = {
            "current_date": current_time.strftime("%A, %B %d, %Y"),
            "events_today": _format_events_for_llm(events_today),
            "events_week": _format_events_for_llm(events_week),
            "todos_today": _format_todos_for_llm(todos_today),
            "todos_week": _format_todos_for_llm(todos_week)
        }
        
        print("🤖 Formatting briefing with LLM...")
        # Generate briefing with LLM
        briefing = await _format_with_llm(env.AI, context)
        
        print("✅ Briefing generated successfully!")
        return briefing
        
    except Exception as e:
        error_msg = f"❌ Failed to generate briefing: {str(e)}"
        print(error_msg)
        print(f"Full error: {e}")
        import traceback
        traceback.print_exc()
        return error_msg


def _format_events_for_llm(events):
    """
    Format calendar events for LLM context.
    
    Args:
        events: List of Google Calendar event objects
        
    Returns:
        list: Simplified event data
    """
    formatted = []
    for event in events:
        # Extract start time
        start = event.get("start", {})
        start_datetime = start.get("dateTime", "")
        start_date = start.get("date", "")
        
        # Extract description
        description = event.get("description", "")
        
        item = {
            "title": event.get("summary", "Untitled"),
            "start_datetime": start_datetime,
            "start_date": start_date,
            "location": event.get("location", ""),
            "description": description
        }
        formatted.append(item)
    return formatted


def _format_todos_for_llm(todos):
    """
    Format Notion todos for LLM context.
    
    Args:
        todos: List of Notion page objects
        
    Returns:
        list: Simplified todo data
    """
    formatted = []
    for todo in todos:
        props = todo.get("properties", {})
        
        # Extract title
        title_prop = props.get("Name", {}).get("title", [])
        title = title_prop[0].get("text", {}).get("content", "Untitled") if title_prop else "Untitled"
        
        # Extract due date
        due_date = props.get("Due Date", {}).get("date", {}).get("start", "")
        
        # Extract status
        status = props.get("Status", {}).get("status", {}).get("name", "Not started")
        
        item = {
            "title": title,
            "due_date": due_date,
            "status": status
        }
        formatted.append(item)
    return formatted


async def _format_with_llm(ai_binding, context):
    """
    Use LLM to format briefing in a friendly, conversational style.
    
    Args:
        ai_binding: Cloudflare Workers AI binding
        context: Dictionary with events and todos data
        
    Returns:
        str: Formatted briefing message
    """
    try:
        # Build prompt with specific formatting instructions
        prompt = f"""Generate a friendly morning briefing message for {context['current_date']}.

TODAY'S EVENTS (show full details):
{_format_list(context['events_today'], 'event', detailed=True)}

THIS WEEK'S EVENTS (show name and day only):
{_format_list(context['events_week'], 'event', detailed=False)}

TODAY'S TODOS:
{_format_list(context['todos_today'], 'todo')}

THIS WEEK'S TODOS:
{_format_list(context['todos_week'], 'todo')}

FORMATTING RULES:
1. Start with a friendly greeting: "🌅 Good morning!"
2. For TODAY'S EVENTS section:
   - List each event with: name, time, and description (if available)
   - Format: "📅 [Event Name] at [Time]" followed by description on next line if present
   - Example: "📅 Team Meeting at 2:00 PM\n   Discuss Q2 roadmap"
3. For THIS WEEK'S EVENTS section:
   - Only show: event name and day of week
   - Format: "📅 [Event Name] - [Day]"
   - Example: "📅 Dentist Appointment - Friday"
4. For TODOS:
   - Show name and due date
   - Format: "☑️ [Todo Name] (due: [Date])"
5. Keep it concise and easy to scan
6. If a section is empty, skip it or say "Nothing scheduled"
7. Do NOT use markdown headers (no ##)
8. Use simple text formatting with emojis

Generate the briefing now:"""

        # Call AI with correct format
        response = await ai_binding.run(
            "@cf/meta/llama-3.1-8b-instruct-fast",
            {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful personal assistant. Generate friendly, concise morning briefings following the exact formatting rules provided."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        )
        
        # Extract response text
        result = None
        if hasattr(response, 'response'):
            result = response.response
        elif isinstance(response, dict):
            if 'response' in response:
                result = response['response']
            elif 'result' in response:
                result = response['result']
            else:
                result = str(response)
        else:
            result = str(response)
        
        # Handle JsProxy objects
        if hasattr(result, 'to_py'):
            result = result.to_py()
        
        return str(result)
            
    except Exception as e:
        print(f"Error formatting with LLM: {e}")
        # Fallback to simple formatting
        return _format_simple_briefing(context)


def _format_list(items, item_type, detailed=None):
    """
    Format list of items for prompt.
    
    Args:
        items: List of events or todos
        item_type: 'event' or 'todo'
        detailed: For events - True for detailed (today), False for summary (week), None for todos
    """
    if not items:
        return "None"
    
    lines = []
    for item in items:
        if item_type == 'event':
            if detailed is True:
                # Detailed format for today's events: name, time, description
                title = item['title']
                
                # Parse time from datetime
                start_datetime = item.get('start_datetime', '')
                if start_datetime:
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                        time_str = dt.strftime('%I:%M %p').lstrip('0')
                    except:
                        time_str = start_datetime
                else:
                    time_str = "All day"
                
                line = f"- {title} at {time_str}"
                
                # Add description if present
                if item.get('description'):
                    line += f"\n  Description: {item['description']}"
                
                # Add location if present
                if item.get('location'):
                    line += f"\n  Location: {item['location']}"
                
                lines.append(line)
                
            elif detailed is False:
                # Summary format for week's events: name and day only
                title = item['title']
                
                # Parse day from datetime
                start_datetime = item.get('start_datetime', '')
                start_date = item.get('start_date', '')
                
                if start_datetime:
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                        day_str = dt.strftime('%A')  # Day of week
                    except:
                        day_str = "Unknown day"
                elif start_date:
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(start_date)
                        day_str = dt.strftime('%A')
                    except:
                        day_str = "Unknown day"
                else:
                    day_str = "Unknown day"
                
                lines.append(f"- {title} - {day_str}")
        else:
            # Todo format
            title = item['title']
            due_date = item.get('due_date', 'No date')
            status = item.get('status', 'Not started')
            lines.append(f"- {title} (due: {due_date}, status: {status})")
    
    return "\n".join(lines)


def _format_simple_briefing(context):
    """Simple fallback briefing format with detailed today's events."""
    from datetime import datetime
    
    briefing = f"🌅 Good morning!\n\n"
    briefing += f"📅 {context['current_date']}\n\n"
    
    # Today's events - detailed
    if context['events_today']:
        briefing += "TODAY'S EVENTS:\n"
        for event in context['events_today']:
            title = event['title']
            
            # Parse time
            start_datetime = event.get('start_datetime', '')
            if start_datetime:
                try:
                    dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                    time_str = dt.strftime('%I:%M %p').lstrip('0')
                except:
                    time_str = "All day"
            else:
                time_str = "All day"
            
            briefing += f"📅 {title}\n"

            briefing += f"⏰ @{time_str}\n"
            
            # Add description if present
            if event.get('description'):
                briefing += f"   📃 {event['description']}\n"
            
            # Add location if present
            if event.get('location'):
                briefing += f"   📍 {event['location']}\n"
            
            briefing += "\n"
    
    # Today's todos
    if context['todos_today']:
        briefing += "TODAY'S TODOS:\n"
        for todo in context['todos_today']:
            briefing += f"☑️ {todo['title']}\n"
        briefing += "\n"
    
    if not context['events_today'] and not context['todos_today']:
        briefing += "Nothing scheduled for today!\n\n"
    
    # This week's events - summary
    if context['events_week']:
        briefing += "THIS WEEK:\n"
        for event in context['events_week']:
            title = event['title']
            
            # Parse day
            start_datetime = event.get('start_datetime', '')
            start_date = event.get('start_date', '')
            
            if start_datetime:
                try:
                    dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                    day_str = dt.strftime('%A')
                except:
                    day_str = "Unknown"
            elif start_date:
                try:
                    dt = datetime.fromisoformat(start_date)
                    day_str = dt.strftime('%A')
                except:
                    day_str = "Unknown"
            else:
                day_str = "Unknown"
            
            briefing += f"📅 {title} - {day_str}\n"
    
    # This week's todos
    if context['todos_week']:
        briefing += "\nTODOS THIS WEEK:\n"
        for todo in context['todos_week']:
            briefing += f"☑️ {todo['title']} (due: {todo['due_date']})\n"
    
    return briefing
