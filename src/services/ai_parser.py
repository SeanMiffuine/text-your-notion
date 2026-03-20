"""
AI Parser using Workers AI with JSON Schema for structured output.
Extracts event/todo details from natural language messages.
"""
from datetime import datetime
import json
import re


# JSON Schema for event/todo extraction
EXTRACTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
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
                "type": ["string", "null"],
                "description": "Time in HH:MM format (24-hour), null if not specified"
            },
            "duration_minutes": {
                "type": ["number", "null"],
                "description": "Duration in minutes, default 60 for events"
            },
            "location": {
                "type": ["string", "null"],
                "description": "Location if mentioned"
            },
            "description": {
                "type": ["string", "null"],
                "description": "Additional context or notes"
            }
        },
        "required": ["item_type", "title", "date"]
    }
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
- Time format: 24-hour HH:MM (e.g., "14:00" for 2pm)
- Default duration: 60 minutes for events
- Extract location if mentioned (e.g., "at the office", "in room 5")
- Keep title concise and clear
- Add any additional context to description

Examples:
- "Meeting with Sarah Friday 2pm" → event, date: next Friday, time: "14:00"
- "Buy groceries tomorrow" → todo, date: tomorrow, time: null
- "Dentist appointment next Tuesday 10am for 30 minutes" → event, duration: 30
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
        # Build the prompt
        prompt = f"""{get_system_prompt(current_datetime)}

User message: {message_text}

Extract the following information and respond ONLY with valid JSON (no other text):
{{
  "item_type": "event or todo",
  "title": "event/todo title",
  "date": "YYYY-MM-DD",
  "time": "HH:MM or null",
  "duration_minutes": 60,
  "location": "location or null",
  "description": "description or null"
}}"""
        
        # Call Workers AI - try with prompt parameter
        response = await ai_binding.run(
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast",  # Upgraded to 70B model
            prompt=prompt
        )
        
        # Parse response
        result_text = None
        
        # Try different response formats
        if isinstance(response, dict):
            if 'response' in response:
                result_text = response['response']
            elif 'result' in response:
                result_text = response['result']
            elif 'text' in response:
                result_text = response['text']
            else:
                result_text = str(response)
        elif hasattr(response, 'response'):
            result_text = response.response
        elif hasattr(response, 'result'):
            result_text = response.result
        else:
            result_text = str(response)
        
        print(f"AI raw response: {result_text}")
        
        # Extract JSON from response (might have extra text)
        if isinstance(result_text, str):
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)
            result = json.loads(result_text)
        else:
            result = result_text
        
        # Validate required fields
        if not isinstance(result, dict):
            raise ValueError(f"Expected dict, got {type(result)}: {result}")
        
        if 'item_type' not in result or 'title' not in result or 'date' not in result:
            raise ValueError(f"Missing required fields in response: {result}")
        
        # Apply defaults
        if result['item_type'] == 'event':
            if result.get('duration_minutes') is None:
                result['duration_minutes'] = 60
        
        return result
        
    except Exception as e:
        print(f"AI parsing error: {e}")
        raise Exception(f"I couldn't understand that. Can you rephrase? (Error: {str(e)})")


