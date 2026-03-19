# API Research: Notion vs Notion Calendar

## Key Findings

### 1. Notion and Notion Calendar are Separate Applications

**Notion Calendar** is a standalone desktop and mobile app (formerly called Cron, acquired by Notion in 2022). It is NOT a feature inside Notion itself.

- Separate applications with different interfaces
- Notion Calendar connects to Google Calendar and iCloud Calendar
- Notion Calendar can also connect to Notion databases

### 2. How Notion Calendar Works

**Primary Function:** Calendar management app that syncs with:
- Google Calendar (primary integration)
- iCloud Calendar
- Notion databases (with date properties)

**Important Limitation:** Notion Calendar does NOT have its own API for creating events programmatically. It uses:
- Google Calendar API (for calendar events)
- Notion API (for database entries)

### 3. Implications for Our Features

#### Feature 1: Natural Language Task & Event Creation

**Calendar Events:**
- ✅ FULLY FEATURED: We can create rich calendar events using the **Google Calendar API**
- Supports all common fields: title, description, location, specific times, reminders, attendees
- Notion Calendar will automatically display these events since it syncs with Google Calendar
- This is the recommended approach for time-specific events

**What we can extract from natural language and add to events:**
- Event title/summary
- Date and time (with timezone)
- Duration (start and end times)
- Location (if mentioned)
- Description/notes
- Reminders (can set default: 30 min before for popup, 1 day before for email)
- Attendees (if email addresses are mentioned)

**Todo Items:**
- ✅ FEASIBLE: We can create todo items using the **Notion API**
- Create pages in a Notion database with a date property
- Notion Calendar can display these if the database is connected to Notion Calendar
- User must manually connect the database to Notion Calendar (one-time setup)

**Recommended Architecture:**
```
Telegram Bot → Cloudflare Worker → {
  Calendar Events → Google Calendar API → Notion Calendar (auto-sync)
  Todo Items → Notion API (database pages) → Notion Calendar (if connected)
}
```

#### Feature 2: Daily Morning Briefing

**Data Sources:**
- ✅ FEASIBLE: Query **Google Calendar API** for calendar events
- ✅ FEASIBLE: Query **Notion API** for database entries (todos)
- Combine both sources for a comprehensive briefing

### 4. API Capabilities

#### Notion API
- ✅ Create pages in databases (`pages.create`)
- ✅ Query databases with filters (date ranges)
- ✅ Support for date properties (with optional time)
- ✅ Support for various property types (title, select, status, checkbox, etc.)
- ✅ Bot user authentication via integration tokens

**Example Page Structure:**
```json
{
  "parent": { "database_id": "xxx" },
  "properties": {
    "Title": { "title": [{ "text": { "content": "Task name" } }] },
    "Due date": { "date": { "start": "2023-02-23" } },
    "Status": { "status": { "name": "Not started" } }
  }
}
```

#### Google Calendar API
- ✅ Create events
- ✅ Query events by date range
- ✅ Support for recurring events
- ✅ OAuth 2.0 authentication
- ✅ Descriptions (HTML supported)
- ✅ Reminders (email and popup, up to 5 per event)
- ✅ Specific times with timezone support
- ✅ Location field
- ✅ Attendees
- ✅ Conference data (Google Meet, Zoom, etc.)
- ✅ Color coding
- ✅ Attachments (up to 25 per event)
- ✅ Visibility settings (public, private, confidential)

**Example Event Creation:**
```json
{
  "summary": "Meeting with Sarah",
  "description": "Discuss Q1 project plans",
  "location": "Conference Room A",
  "start": {
    "dateTime": "2026-03-21T14:00:00-07:00",
    "timeZone": "America/Vancouver"
  },
  "end": {
    "dateTime": "2026-03-21T15:00:00-07:00",
    "timeZone": "America/Vancouver"
  },
  "reminders": {
    "useDefault": false,
    "overrides": [
      {"method": "email", "minutes": 1440},  // 1 day before
      {"method": "popup", "minutes": 30}     // 30 min before
    ]
  },
  "attendees": [
    {"email": "[email protected]"}
  ]
}
```

### 5. Revised Technical Approach

**For Calendar Events (time-specific):**
- Use Google Calendar API directly
- Notion Calendar will automatically sync and display these events
- No additional Notion integration needed for calendar events

**For Todo Items (tasks):**
- Use Notion API to create pages in a Notion database
- Database must have a date property
- User connects database to Notion Calendar (one-time manual setup)
- Items will appear in Notion Calendar once connected

**For Morning Briefing:**
- Query Google Calendar API for today's and this week's events
- Query Notion API for database entries with dates in range
- Combine and format the results
- Send via Telegram

### 6. User Setup Requirements

1. Create Google Calendar account (most users already have)
2. Create Notion workspace and database(s) for todos
3. Install Notion Calendar app
4. Connect Google Calendar to Notion Calendar (automatic)
5. Connect Notion database to Notion Calendar (manual, one-time)
6. Provide API credentials to the bot:
   - Google Calendar OAuth tokens
   - Notion integration token
   - Telegram bot token

### 7. Limitations & Considerations

- Notion Calendar has no direct API - we work with Google Calendar and Notion APIs
- Notion database items only appear in Notion Calendar if user connects the database
- Google Calendar events do NOT automatically create Notion pages (one-way sync)
- Notion Calendar is view-only for external calendars (Google, iCloud)
- Maximum 20 databases can be connected to Notion Calendar

## Conclusion

✅ **Both features are fully feasible** with the following approach:

1. Use **Google Calendar API** for calendar events
2. Use **Notion API** for todo items in databases
3. Notion Calendar serves as the unified viewing interface (user-facing)
4. Our bot works behind the scenes with Google Calendar and Notion APIs

This architecture is actually cleaner than originally planned, as we leverage existing, well-documented APIs rather than relying on a hypothetical Notion Calendar API.
