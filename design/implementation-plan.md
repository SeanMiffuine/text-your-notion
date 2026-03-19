# Implementation Plan - Personal Notion Assistant Bot

## Decisions Made

### 2A. AI Parsing Strategy
✅ **Use Workers AI JSON Mode with JSON Schema**

Workers AI supports structured JSON output natively via `response_format` parameter:
- Model: `@cf/meta/llama-3.1-8b-instruct-fast` (supports JSON Mode)
- Define JSON Schema for event/todo extraction
- LLM returns validated JSON object
- No manual parsing needed

**Schema Structure:**
```json
{
  "type": "object",
  "properties": {
    "item_type": {"type": "string", "enum": ["event", "todo"]},
    "title": {"type": "string"},
    "date": {"type": "string"},
    "time": {"type": "string"},
    "duration_minutes": {"type": "number"},
    "location": {"type": "string"},
    "description": {"type": "string"}
  },
  "required": ["item_type", "title", "date"]
}
```

### 2B. Date/Time Parsing
✅ **Use Python's built-in `datetime` + `zoneinfo` (Python 3.9+)**

- All operations in `America/Vancouver` timezone
- Default duration: 60 minutes if not specified
- Convert relative dates ("tomorrow", "Friday") to absolute dates
- No external libraries needed (keep it simple)

### 2C. Event vs Todo Classification
✅ **LLM decides via `item_type` field in JSON Schema**

- AI determines if message is "event" or "todo"
- Enum constraint ensures valid values only
- Fallback: if time specified → event, else → todo

### 2D. Error Handling
✅ **Log errors to Telegram chat**

- AI parsing fails → Send "I couldn't understand that. Can you rephrase?"
- API call fails → Send "Something went wrong: [error message]"
- Keep user informed, no silent failures

### 3. Authentication
✅ **Single Google Calendar (Service Account approach)**

- One Google Calendar for all events (single user - you)
- One Notion workspace for todos
- Simpler OAuth flow
- Can expand to multi-user later

### Other Decisions
- **Single user (v1)** - Build for one user first
- **Notion schema** - You'll set up the database structure
- **Morning briefing** - Custom LLM prompt for formatting
- **API credentials** - You'll provide all tokens

---

## Project Structure

```
text-your-notion/
├── src/
│   ├── worker.py              # Main Worker entrypoint (fetch + scheduled)
│   ├── handlers/
│   │   ├── telegram.py        # Process Telegram messages
│   │   └── briefing.py        # Generate morning briefing
│   ├── services/
│   │   ├── ai_parser.py       # Workers AI with JSON Schema
│   │   ├── calendar.py        # Google Calendar API client
│   │   └── notion.py          # Notion API client
│   └── utils/
│       └── datetime_utils.py  # Vancouver timezone helpers
├── wrangler.toml              # Cloudflare config + cron
├── requirements.txt           # Python dependencies
├── .env.example              # Template for secrets
└── README.md                 # Setup instructions
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
1. Initialize Cloudflare Worker project with `pywrangler`
2. Set up `wrangler.toml` with cron trigger (9 AM PST)
3. Create basic Worker entrypoint (fetch + scheduled handlers)
4. Configure environment variables

### Phase 2: AI Parsing
1. Implement `ai_parser.py` with JSON Schema
2. Define event/todo extraction schema
3. Test with sample messages locally

### Phase 3: API Integrations
1. Implement `calendar.py` - Google Calendar event creation
2. Implement `notion.py` - Notion page creation
3. Add datetime utilities for Vancouver timezone

### Phase 4: Telegram Integration
1. Implement `telegram.py` - webhook handler
2. Parse incoming messages
3. Send confirmation/error messages back

### Phase 5: Morning Briefing
1. Implement `briefing.py` - query APIs
2. Format results with LLM
3. Send via Telegram

### Phase 6: Testing & Deployment
1. Test locally with mock webhooks
2. Deploy to Cloudflare Workers
3. Set Telegram webhook URL
4. Test end-to-end with real bot

---

## Technical Specifications

### Workers AI JSON Schema

```python
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
                "description": "Short title/summary"
            },
            "date": {
                "type": "string",
                "description": "Date in YYYY-MM-DD format"
            },
            "time": {
                "type": "string",
                "description": "Time in HH:MM format (24-hour), null if not specified"
            },
            "duration_minutes": {
                "type": "number",
                "description": "Duration in minutes, default 60"
            },
            "location": {
                "type": "string",
                "description": "Location if mentioned"
            },
            "description": {
                "type": "string",
                "description": "Additional context"
            }
        },
        "required": ["item_type", "title", "date"]
    }
}
```

### System Prompt for AI Parser

```
You are a calendar assistant. Extract event/todo details from user messages.

Rules:
- Timezone: America/Vancouver (PST/PDT)
- Current date/time: {current_datetime}
- If specific time mentioned → item_type: "event"
- If no time or vague time → item_type: "todo"
- Convert relative dates: "tomorrow", "Friday", "next Monday" → YYYY-MM-DD
- Default duration: 60 minutes
- Extract location if mentioned
- Keep title concise
```

### Cron Configuration (wrangler.toml)

```toml
[triggers]
crons = ["0 16 * * *"]  # 9 AM PST = 16:00 UTC (PST is UTC-8)
# Note: Adjust for PDT (UTC-7) during daylight saving time
```

### Environment Variables

```bash
TELEGRAM_BOT_TOKEN=your_telegram_token
GOOGLE_CALENDAR_OAUTH_TOKEN=your_google_token
NOTION_API_KEY=your_notion_key
NOTION_DATABASE_ID=your_database_id
TELEGRAM_CHAT_ID=your_chat_id  # For morning briefing
```

---

## Next Steps

1. Initialize project structure
2. Set up `wrangler.toml` and dependencies
3. Implement core Worker handlers
4. Build AI parser with JSON Schema
5. Integrate Google Calendar and Notion APIs
6. Test and deploy

Ready to start coding! 🚀
