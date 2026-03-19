# Personal Notion Assistant Bot

A serverless Telegram bot that uses natural language to create calendar events and todos, plus sends daily morning briefings. Built on Cloudflare Workers with Workers AI.

## Features

- 📅 **Natural Language Event Creation** - "Meeting with Sarah Friday 2pm" → Google Calendar event
- ☑️ **Natural Language Todo Creation** - "Buy groceries tomorrow" → Notion todo
- 🌅 **Daily Morning Briefing** - Automatic summary at 9 AM PST of today's and this week's events/todos
- 🤖 **AI-Powered Parsing** - Uses Cloudflare Workers AI (Llama 3.1 8B) with JSON Schema
- ⚡ **Serverless & Fast** - Runs on Cloudflare's edge network with zero cold starts

## Tech Stack

- **Compute:** Cloudflare Workers (Python)
- **AI/NLP:** Workers AI (Llama 3.1 8B Instruct Fast)
- **Calendar:** Google Calendar API
- **Todos:** Notion API
- **Messaging:** Telegram Bot API
- **Scheduling:** Cloudflare Cron Triggers

## Prerequisites

1. **Cloudflare Workers account** - [Sign up](https://workers.cloudflare.com/)
2. **Python 3.9+** with `uv` package manager
3. **Node.js** (for pywrangler CLI)
4. **Telegram Bot** - Create via [@BotFather](https://t.me/botfather)
5. **Google Calendar API** - Enable and get OAuth credentials
6. **Notion Integration** - Create integration and database

## Setup Instructions

> **Important:** All setup steps are run on your **local machine** (Mac/Linux/Windows), not on Cloudflare Workers. You develop locally, then deploy to Cloudflare's cloud where your bot runs 24/7.

### Where to Run What

**On Your Local Machine:**
- Install tools (uv, pywrangler)
- Write and edit code
- Configure secrets (uploaded to Cloudflare)
- Deploy to Cloudflare
- Test locally before deploying

**On Cloudflare Workers (automatic after deploy):**
- Runs your deployed code 24/7
- Handles Telegram webhooks
- Executes cron jobs (morning briefing)
- Stores your secrets securely

Think of it like: **Your computer = development**, **Cloudflare = production**

---

### 1. Install Tools (on your local machine)

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pywrangler (Cloudflare Workers CLI for Python)
npm install -g pywrangler
```

### 2. Clone and Configure (on your local machine)

```bash
# Clone repository
git clone <your-repo-url>
cd text-your-notion

# Copy environment template
cp .env.example .env
```

### 3. Set Up Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token
4. Get your chat ID:
   - Message your bot
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Find your `chat.id` in the response

### 4. Set Up Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Generate access token (or use service account)

### 5. Set Up Notion

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Create new integration and copy the token
3. Create a database with these properties:
   - **Name** (Title)
   - **Due Date** (Date)
   - **Status** (Status: Not started, In progress, Done)
   - **Description** (Text) - optional
4. Share the database with your integration
5. Copy the database ID from the URL

### 6. Configure Secrets (on your local machine)

These commands upload your secrets to Cloudflare Workers securely:

```bash
# Set environment variables in Cloudflare Workers
# You'll be prompted to enter each value
wrangler secret put TELEGRAM_BOT_TOKEN
wrangler secret put TELEGRAM_CHAT_ID
wrangler secret put GOOGLE_CALENDAR_OAUTH_TOKEN
wrangler secret put NOTION_API_KEY
wrangler secret put NOTION_DATABASE_ID
```

### 7. Deploy (on your local machine)

This uploads your code to Cloudflare's cloud:

```bash
# Deploy to Cloudflare Workers
pywrangler deploy
```

After deployment, your bot runs on Cloudflare's edge network automatically!

### 8. Set Telegram Webhook

```bash
# Set webhook to your Worker URL
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://notion-assistant-bot.<your-subdomain>.workers.dev"}'
```

## Usage

### Creating Events

Send natural language messages to your bot:

- "Meeting with Sarah Friday 2pm"
- "Dentist appointment next Tuesday 10am for 30 minutes"
- "Team standup tomorrow at 9:30am"

The bot will:
- Parse the message with AI
- Create a Google Calendar event
- Send confirmation with details

### Creating Todos

Send messages without specific times:

- "Buy groceries tomorrow"
- "Call mom this weekend"
- "Review project proposal by Friday"

The bot will:
- Parse the message with AI
- Create a Notion todo
- Send confirmation

### Morning Briefing

Every day at 9 AM PST, you'll receive:
- Events scheduled for today
- Todos due today
- Events scheduled this week
- Todos due this week

## Project Structure

```
text-your-notion/
├── src/
│   ├── worker.py              # Main Worker entrypoint
│   ├── handlers/
│   │   ├── telegram.py        # Telegram message handler
│   │   └── briefing.py        # Morning briefing generator
│   ├── services/
│   │   ├── ai_parser.py       # Workers AI with JSON Schema
│   │   ├── calendar.py        # Google Calendar API client
│   │   └── notion.py          # Notion API client
│   └── utils/
│       └── datetime_utils.py  # Vancouver timezone utilities
├── wrangler.toml              # Cloudflare configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Development

### Local Testing

```bash
# Run locally
pywrangler dev

# Test webhook with curl
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "chat": {"id": 123456789},
      "text": "Meeting tomorrow at 2pm"
    }
  }'

# Test cron trigger
curl http://localhost:8787/__scheduled
```

### Debugging

Check logs in Cloudflare dashboard or use:

```bash
wrangler tail
```

## Customization

### Change Briefing Time

Edit `wrangler.toml`:

```toml
[triggers]
crons = ["0 16 * * *"]  # 9 AM PST = 16:00 UTC
```

### Modify AI Parsing

Edit `src/services/ai_parser.py` to adjust:
- JSON Schema structure
- System prompt
- Default values

### Customize Briefing Format

Edit `src/handlers/briefing.py` to change:
- LLM prompt for formatting
- Fallback format
- Emoji usage

## Troubleshooting

### Bot not responding
- Check webhook is set correctly
- Verify environment variables are set
- Check Cloudflare Workers logs

### AI parsing errors
- Ensure message is clear and specific
- Check Workers AI binding is configured
- Verify model name is correct

### API errors
- Verify OAuth tokens are valid
- Check API quotas and limits
- Ensure database/calendar permissions

## Cost Estimate

With Cloudflare Workers free tier:
- 100,000 requests/day
- Workers AI included (beta)
- Cron triggers included

**Expected cost: $0/month** for personal use (< 1,000 messages/day)

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Please open an issue or PR.

## Support

For issues or questions:
1. Check troubleshooting section
2. Review Cloudflare Workers docs
3. Open a GitHub issue
