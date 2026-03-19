# Personal Notion Assistant Bot

> **Research Documentation:** See `/design/research/` for detailed API capabilities and implementation references

## System Vision
A serverless Telegram bot that uses natural language to create calendar events and todos, plus sends daily morning briefings. All running on Cloudflare Workers at the edge.

---

## Tech Stack

| Component | Technology | Why |
|:----------|:-----------|:----|
| **Messaging** | Telegram Bot API | Free, webhooks, rich formatting |
| **Compute** | Cloudflare Workers (Python) | Serverless, edge network, zero cold starts |
| **AI/NLP** | Workers AI (Llama 3.1 8B) | Built-in LLM, no external API needed |
| **Calendar** | Google Calendar API | Standard API, syncs to Notion Calendar |
| **Todos** | Notion API | Flexible database, syncs to Notion Calendar |
| **Scheduling** | Cloudflare Cron Triggers | Built-in, reliable |

**Why Cloudflare Workers:**
- All-in-one: compute + AI + scheduling + secrets
- Free tier covers our use case (100K requests/day)
- Runs globally at the edge (low latency)
- No infrastructure to manage

---

## Features

### 1. Natural Language Event/Todo Creation

**What it does:**
- Send "Meeting with Sarah Friday 2pm" → Creates Google Calendar event
- Send "Buy groceries tomorrow" → Creates Notion todo

**How it works:**
1. User sends message to Telegram bot
2. Telegram webhooks to Cloudflare Worker
3. Worker uses Workers AI to parse message (extract title, date, time, type)
4. Worker calls Google Calendar API (for events) or Notion API (for todos)
5. Worker sends confirmation back to Telegram

---

### 2. Daily Morning Briefing

**What it does:**
- Every day at 9 AM PST, sends summary of:
  - Events/todos due today
  - Events/todos due this week

**How it works:**
1. Cloudflare Cron triggers at 9 AM PST
2. Worker queries Google Calendar API + Notion API
3. Worker formats results
4. Worker sends message via Telegram

---

## Architecture

### Data Flow

```
User → Telegram → Cloudflare Worker → Workers AI (parse) → Google Calendar / Notion → Confirmation
                       ↓
                  Cron (9 AM PST) → Query APIs → Format → Send to Telegram
```

### Key Decisions

- **Stateless:** No database. Google Calendar + Notion are the source of truth
- **Webhooks:** Instant response, only runs when needed
- **Timezone:** America/Vancouver (PST/PDT) for cron and date parsing
- **Security:** All API keys in Cloudflare Environment Variables
- **Edge AI:** Workers AI runs at the edge (no external LLM API)

### Important Note
Notion Calendar is a standalone app (not an API). It syncs with Google Calendar and Notion databases. Our bot creates data via Google Calendar API and Notion API, which automatically appear in Notion Calendar.

---

## Data Schema

**Google Calendar Events:**
- Summary (title)
- Start/End (datetime with timezone)
- Description, Location (optional)

**Notion Todo Database:**
- Name (title)
- Due Date (date property)
- Category (Select: Work, Art, Personal)
- Status (Select: Not started, In progress, Done)
- Priority (Select: High, Medium, Low)
- Bot_ID (text, for tracking)

User must connect Notion database to Notion Calendar (one-time setup).

---

## Implementation Steps

1. **Setup Accounts:**
   - Cloudflare Workers account
   - Google Calendar + enable API
   - Notion workspace + create Todo database
   - Telegram bot (@BotFather)
   - Notion Calendar app (connect Google Calendar + Notion database)

2. **Install Tools:**
   - `uv` and `pywrangler` CLI

3. **Configure APIs:**
   - Google Calendar OAuth 2.0 credentials
   - Notion integration token
   - Telegram bot token
   - Store all in Cloudflare Environment Variables

4. **Build Worker:**
   - `pywrangler init` to create project
   - Implement `fetch()` handler (webhooks)
   - Implement `scheduled()` handler (cron)
   - Integrate Workers AI for NLP
   - Add Google Calendar + Notion API calls

5. **Configure Cron:**
   - In `wrangler.toml`: `crons = ["0 9 * * *"]`
   - Timezone: America/Vancouver

6. **Test & Deploy:**
   - Test locally: `pywrangler dev`
   - Deploy: `pywrangler deploy`
   - Set Telegram webhook to Worker URL

---

## Reference Documentation

When implementing, refer to these research documents in `/design/research/`:

- **`cloudflare-workers-research.md`** - Workers AI models, Python syntax, cron triggers, pricing
- **`google-calendar-capabilities.md`** - Full API capabilities, event creation examples, reminders
- **`api-research.md`** - How Notion Calendar works, API integration strategy

### Key API References

**Cloudflare Workers AI:**
- Model: `@cf/meta/llama-3.1-8b-instruct-fast`
- Use for parsing natural language messages
- See research doc for code examples

**Google Calendar API:**
- Endpoint: `POST https://www.googleapis.com/calendar/v3/calendars/primary/events`
- Supports: descriptions, reminders, specific times, locations, attendees
- See research doc for full event schema

**Notion API:**
- Endpoint: `POST https://api.notion.com/v1/pages`
- Version header: `Notion-Version: 2022-06-28`
- See research doc for page creation examples

**Telegram Bot API:**
- Webhook setup: `POST https://api.telegram.org/bot<token>/setWebhook`
- Send message: `POST https://api.telegram.org/bot<token>/sendMessage`