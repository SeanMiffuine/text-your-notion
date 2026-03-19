"""
Morning briefing handler for generating daily summaries.
"""
from src.services.calendar import GoogleCalendarClient
from src.services.notion import NotionClient
from src.utils.datetime_utils import get_current_time


async def generate_briefing(env):
    """
    Generate morning briefing with today's and this week's events/todos.
    
    Args:
        env: Cloudflare Worker environment (contains API keys and AI binding)
        
    Returns:
        str: Formatted briefing message
    """
    try:
        # Initialize clients
        calendar_client = GoogleCalendarClient(env.GOOGLE_CALENDAR_OAUTH_TOKEN)
        notion_client = NotionClient(env.NOTION_API_KEY, env.NOTION_DATABASE_ID)
        
        # Fetch data
        events_today = await calendar_client.get_events_today()
        events_week = await calendar_client.get_events_this_week()
        todos_today = await notion_client.get_todos_today()
        todos_week = await notion_client.get_todos_this_week()
        
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
        
        # Generate briefing with LLM
        briefing = await _format_with_llm(env.AI, context)
        
        return briefing
        
    except Exception as e:
        print(f"Error generating briefing: {e}")
        return f"❌ Failed to generate briefing: {str(e)}"


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
        item = {
            "title": event.get("summary", "Untitled"),
            "start": event.get("start", {}).get("dateTime", ""),
            "location": event.get("location", "")
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
        # Build prompt
        prompt = f"""Generate a friendly morning briefing message for {context['current_date']}.

Today's Events:
{_format_list(context['events_today'], 'event')}

This Week's Events:
{_format_list(context['events_week'], 'event')}

Today's Todos:
{_format_list(context['todos_today'], 'todo')}

This Week's Todos:
{_format_list(context['todos_week'], 'todo')}

Format the briefing in a warm, conversational style with:
- A friendly greeting (🌅 Good morning!)
- Clear sections for Today and This Week
- Use emojis appropriately (📅 for events, ☑️ for todos)
- Keep it concise but informative
- If nothing is scheduled, say something encouraging

Do not use markdown headers. Use simple text formatting."""

        # Call AI
        response = await ai_binding.run(
            "@cf/meta/llama-3.1-8b-instruct-fast",
            {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful personal assistant. Generate friendly, concise morning briefings."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        )
        
        # Extract response
        if hasattr(response, 'response'):
            return response.response
        elif isinstance(response, dict) and 'response' in response:
            return response['response']
        else:
            return str(response)
            
    except Exception as e:
        print(f"Error formatting with LLM: {e}")
        # Fallback to simple formatting
        return _format_simple_briefing(context)


def _format_list(items, item_type):
    """Format list of items for prompt."""
    if not items:
        return "None"
    
    lines = []
    for item in items:
        if item_type == 'event':
            lines.append(f"- {item['title']} at {item['start']}")
        else:
            lines.append(f"- {item['title']} (due: {item['due_date']}, status: {item['status']})")
    
    return "\n".join(lines)


def _format_simple_briefing(context):
    """Simple fallback briefing format."""
    briefing = f"🌅 Good morning!\n\n"
    briefing += f"📅 {context['current_date']}\n\n"
    
    # Today
    briefing += "**Today:**\n"
    if context['events_today']:
        briefing += f"📅 {len(context['events_today'])} event(s)\n"
    if context['todos_today']:
        briefing += f"☑️ {len(context['todos_today'])} todo(s)\n"
    if not context['events_today'] and not context['todos_today']:
        briefing += "Nothing scheduled!\n"
    
    briefing += "\n"
    
    # This week
    briefing += "**This Week:**\n"
    if context['events_week']:
        briefing += f"📅 {len(context['events_week'])} event(s)\n"
    if context['todos_week']:
        briefing += f"☑️ {len(context['todos_week'])} todo(s)\n"
    
    return briefing
