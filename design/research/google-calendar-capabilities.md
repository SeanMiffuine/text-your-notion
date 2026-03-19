# Google Calendar API - Full Capabilities

## Yes, we can add everything! ✅

The Google Calendar API is extremely comprehensive and supports all the features you'd expect from a modern calendar application.

## Supported Features

### Basic Event Information
- ✅ **Summary/Title** - Event name
- ✅ **Description** - Full HTML support for rich formatting
- ✅ **Location** - Free-form text for event location
- ✅ **Start/End Times** - Precise datetime with timezone support
- ✅ **All-day Events** - Using date format instead of dateTime
- ✅ **Timezone** - IANA timezone database names (e.g., "America/Vancouver")

### Reminders
- ✅ **Multiple Reminders** - Up to 5 reminders per event
- ✅ **Reminder Types:**
  - `popup` - UI notification
  - `email` - Email reminder
- ✅ **Timing** - Specify minutes before event (0 to 40,320 minutes = 4 weeks)
- ✅ **Custom or Default** - Use calendar defaults or override with custom reminders

**Example:**
```json
"reminders": {
  "useDefault": false,
  "overrides": [
    {"method": "email", "minutes": 1440},  // 1 day before
    {"method": "popup", "minutes": 30},    // 30 minutes before
    {"method": "popup", "minutes": 10}     // 10 minutes before
  ]
}
```

### Time Specifications
- ✅ **Specific Times** - Down to the second precision
- ✅ **Timezone Support** - Per-event timezone specification
- ✅ **RFC3339 Format** - Standard datetime format
- ✅ **All-day Events** - Simple date format (yyyy-mm-dd)

**Example:**
```json
"start": {
  "dateTime": "2026-03-21T14:00:00-07:00",
  "timeZone": "America/Vancouver"
}
```

### Recurring Events
- ✅ **Recurrence Rules** - RRULE, EXRULE, RDATE, EXDATE (RFC5545)
- ✅ **Complex Patterns** - Daily, weekly, monthly, yearly with exceptions
- ✅ **End Conditions** - Until date or count

### Attendees & Collaboration
- ✅ **Multiple Attendees** - Add email addresses
- ✅ **Optional Attendees** - Mark attendees as optional
- ✅ **Response Status** - Track accepted/declined/tentative
- ✅ **Guest Permissions:**
  - Can invite others
  - Can modify event
  - Can see other guests

### Conference/Video Calls
- ✅ **Google Meet** - Auto-generate Meet links
- ✅ **Zoom Integration** - Add Zoom links
- ✅ **Custom Links** - Any video conferencing URL
- ✅ **Phone Numbers** - Conference dial-in numbers

### Visual & Organization
- ✅ **Color Coding** - 11 predefined colors
- ✅ **Visibility** - Public, private, or confidential
- ✅ **Status** - Confirmed, tentative, or cancelled
- ✅ **Transparency** - Show as busy or available

### Attachments & Links
- ✅ **File Attachments** - Up to 25 per event
- ✅ **Google Drive Files** - Direct integration
- ✅ **Source Links** - Link to originating document/webpage

### Advanced Features
- ✅ **Working Location** - Home, office, or custom location
- ✅ **Out of Office** - Special event type with auto-decline
- ✅ **Focus Time** - Block time with auto-decline
- ✅ **Extended Properties** - Custom metadata (private or shared)

## What This Means for Our Bot

### Natural Language Parsing Can Extract:
1. **Event title** - "Meeting with Sarah"
2. **Date/time** - "Friday at 2pm", "tomorrow at 9am", "next Monday 3:30pm"
3. **Duration** - "for 1 hour", "30 minute meeting"
4. **Location** - "at Conference Room A", "in Building 5"
5. **Description** - Additional context from the message
6. **Attendees** - Email addresses mentioned in the message

### Default Settings We Can Apply:
- **Reminders:** Always add 30-minute popup reminder
- **Timezone:** America/Vancouver (PST/PDT)
- **Status:** Confirmed
- **Visibility:** Default (respects calendar settings)
- **Color:** Can assign based on category (work, personal, art)

### Example Bot Interactions:

**User:** "Meeting with Sarah Friday 2pm for 1 hour at the office"

**Bot creates:**
```json
{
  "summary": "Meeting with Sarah",
  "location": "Office",
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
      {"method": "popup", "minutes": 30}
    ]
  }
}
```

**User:** "Dentist appointment next Tuesday 10am, remind me 1 day before and 1 hour before"

**Bot creates:**
```json
{
  "summary": "Dentist appointment",
  "start": {
    "dateTime": "2026-03-24T10:00:00-07:00",
    "timeZone": "America/Vancouver"
  },
  "end": {
    "dateTime": "2026-03-24T11:00:00-07:00",
    "timeZone": "America/Vancouver"
  },
  "reminders": {
    "useDefault": false,
    "overrides": [
      {"method": "email", "minutes": 1440},  // 1 day
      {"method": "popup", "minutes": 60}     // 1 hour
    ]
  }
}
```

## API Limits & Quotas

- **Free Tier:** 1,000,000 queries per day
- **Rate Limit:** 10 queries per second per user
- **Event Size:** Reasonable for typical use (descriptions can be quite long)

## Conclusion

The Google Calendar API is feature-complete for our needs. We can create rich, detailed calendar events with:
- ✅ Specific times and timezones
- ✅ Multiple customizable reminders
- ✅ Descriptions and locations
- ✅ Attendees and collaboration features
- ✅ All standard calendar features

This gives us everything we need to build a powerful natural language calendar assistant!
