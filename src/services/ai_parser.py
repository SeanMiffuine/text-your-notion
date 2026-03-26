"""
AI Parser using Workers AI with JSON Schema for structured output.
Extracts event/todo details from natural language messages.
"""
from datetime import datetime
import json
from js import Object
from pyodide.ffi import to_js as _to_js


# Helper to convert Python dicts to JavaScript objects
def to_js(obj):
    return _to_js(obj, dict_converter=Object.fromEntries)


# JSON Schema for event/todo extraction
# Simplified to avoid nullable type arrays which can confuse the model
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "item_type": {
            "type": "string",
            "enum": ["event", "todo"],
            "description": "event if specific time mentioned, todo otherwise"
        },
        "title": {
            "type": "string",
            "description": "Short title/summary of the event or todo"
        },
        "date": {
            "type": "string",
            "description": "Date in YYYY-MM-DD format"
        },
        "time": {
            "type": "string",
            "description": "Time in HH:MM format (24-hour), empty string if not specified"
        },
        "duration_minutes": {
            "type": "number",
            "description": "Duration in minutes, default 60 for events"
        },
        "location": {
            "type": "string",
            "description": "Location if mentioned, empty string otherwise"
        },
        "description": {
            "type": "string",
            "description": "Additional context or notes, empty string if none"
        },
        "category": {
            "type": "string",
            "enum": ["Academic", "Birthdays", "Errands", "Events", "Finance", "Occupation", "Passion"],
            "description": "Calendar category based on event type, defaults to Events"
        }
    },
    "required": ["item_type", "title", "date", "time", "duration_minutes", "location", "description", "category"]
}


def get_system_prompt(current_datetime):
    """
    Generate system prompt for AI parser.
    
    Args:
        current_datetime: Current datetime in Vancouver timezone
        
    Returns:
        System prompt string
    """
    return f"""You are a calendar assistant. Extract event/todo details from user messages.

Current date and time (America/Vancouver timezone): {current_datetime.strftime('%Y-%m-%d %H:%M %Z')}
Current day of week: {current_datetime.strftime('%A')}

Rules:
- Timezone: America/Vancouver (PST/PDT)
- If specific time mentioned (e.g., "2pm", "at 3:30") → item_type: "event"
- If no time or vague time (e.g., "tomorrow", "later") → item_type: "todo"
- Convert relative dates to absolute YYYY-MM-DD format:
  - "today" → {current_datetime.strftime('%Y-%m-%d')}
  - "tomorrow" → calculate next day
  - "Friday", "next Monday" → calculate actual date
- Time format: 24-hour HH:MM (e.g., "14:00" for 2pm), use empty string if no time
- Default duration: 60 minutes for events
- Extract location if mentioned, use empty string if not mentioned
- Keep title concise and clear
- Description field: ONLY use for explicit notes, reminders, or special instructions the user mentions. If the user just describes what the event is, put that in the title. Use empty string if no description.
- Category: Choose the most appropriate calendar category:
  - Academic: Classes, lectures, study sessions, exams, school-related
  - Birthdays: Birthday celebrations and anniversaries
  - Errands: Shopping, chores, appointments (dentist, haircut, etc.)
  - Events: Social events, dinners, parties, meetups, entertainment
  - Finance: Bill payments, financial meetings, budget reviews
  - Occupation: Work meetings, deadlines, work tasks, professional activities
  - Passion: Hobbies, personal projects, art, music, sports, creative activities
  - Default to "Events" if unclear or doesn't fit other categories

Examples:
- "Meeting with Sarah Friday 2pm" → event, date: next Friday, time: "14:00", description: "", category: "Events"
- "Buy groceries tomorrow" → todo, date: tomorrow, time: "", description: "", category: "Errands"
- "Dentist appointment next Tuesday 10am for 30 minutes" → event, duration: 30, description: "", category: "Errands"
- "Dinner with John at 7pm, remind me to bring the documents" → event, time: "19:00", description: "Bring the documents", category: "Events"
- "Block off 6pm till end of day for dinner and drinks with Rikochan" → event, title: "Dinner and drinks with Rikochan", description: "", category: "Events"
- "Art practice tomorrow at 3pm" → event, time: "15:00", category: "Passion"
- "Team standup Monday 9am" → event, time: "09:00", category: "Occupation"
- "Pay rent on the 1st" → todo, category: "Finance"
"""


async def parse_message(ai_binding, message_text, current_datetime):
    """
    Parse natural language message using Workers AI.
    
    Args:
        ai_binding: Cloudflare Workers AI binding (env.AI)
        message_text: User's message text
        current_datetime: Current datetime in Vancouver timezone
        
    Returns:
        dict: Parsed event/todo data
        
    Raises:
        Exception: If AI parsing fails
    """
    try:
        # Build the system prompt
        system_prompt = get_system_prompt(current_datetime)
        
        # Build request payload matching the docs example exactly
        request_payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_text}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": EXTRACTION_SCHEMA
            }
        }
        
        print(f"Request payload: {json.dumps(request_payload, indent=2)}")
        
        # Convert to JavaScript object for the binding
        js_payload = to_js(request_payload)
        
        # Call Workers AI with JSON schema mode
        response = await ai_binding.run(
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
            js_payload
        )
        
        # Parse response
        result = None
        
        # Handle JsProxy objects from Python Workers FFI
        if hasattr(response, 'response'):
            result = response.response
        elif isinstance(response, dict):
            if 'response' in response:
                result = response['response']
            elif 'result' in response:
                result = response['result']
            elif 'text' in response:
                result = response['text']
            else:
                result = response
        else:
            result = response
        
        # Convert JsProxy to Python dict using the built-in to_py() method
        if hasattr(result, 'to_py'):
            result = result.to_py()
        
        print(f"AI raw response: {result}")
        
        # If result is a string, parse it as JSON
        if isinstance(result, str):
            result = json.loads(result)
        
        # Validate required fields
        if not isinstance(result, dict):
            raise ValueError(f"Expected dict, got {type(result)}: {result}")
        
        if 'item_type' not in result or 'title' not in result or 'date' not in result:
            raise ValueError(f"Missing required fields in response: {result}")
        
        # Apply defaults and convert empty strings to None
        if result['item_type'] == 'event':
            if result.get('duration_minutes') is None or result.get('duration_minutes') == 0:
                result['duration_minutes'] = 60
            if result.get('category') is None or result.get('category') == '':
                result['category'] = 'Events'
        
        # Convert empty strings to None for optional fields
        if result.get('time') == '':
            result['time'] = None
        if result.get('location') == '':
            result['location'] = None
        if result.get('description') == '':
            result['description'] = None
        
        return result
        
    except Exception as e:
        print(f"AI parsing error: {e}")
        raise Exception(f"I couldn't understand that. Can you rephrase? (Error: {str(e)})")


