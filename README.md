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

# Install wrangler (Cloudflare Workers CLI)
npm install -g wrangler

# Note: pywrangler is run via 'uv run pywrangler' (no separate install needed)
```

### 2. Clone and Configure (on your local machine)

```bash
# Clone repository
git clone <your-repo-url>
cd text-your-notion

# Create local secrets file
cp .dev.vars.example .dev.vars

# Edit .dev.vars and add your actual tokens
# This file is for LOCAL TESTING ONLY and is git-ignored
```

**Important:** 
- `.dev.vars` is for local development (testing with `uv run pywrangler dev`)
- For production deployment, you still need to use `wrangler secret put` commands
- Never commit `.dev.vars` to git (it's already in `.gitignore`)

### 3. Set Up Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token
4. Get your chat ID:
   - Message your bot
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Find your `chat.id` in the response

**Privacy:** The bot will ONLY respond to messages from your chat ID. Anyone else who tries to message the bot will be silently ignored.

### 4. Set Up Google Calendar API

**Step 1: Create Google Cloud Project**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "Notion Assistant Bot"
3. Enable **Google Calendar API** (APIs & Services → Library)

**Step 2: Create OAuth 2.0 Credentials**
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Configure OAuth consent screen (if needed):
   - User Type: External
   - Add scope: `https://www.googleapis.com/auth/calendar`
   - Add your email as test user
4. Create OAuth client ID:
   - Application type: **Desktop app**
   - Download the JSON file as `client_secret.json`

**Step 3: Get Your Access Token**

Run the helper script to authorize your bot:

```bash
# Install dependencies
cd scripts
pip install -r requirements.txt

# Place your client_secret.json in the scripts folder
# Then run:
python get_google_token.py
```

This will:
- Open your browser for Google authorization
- Generate an access token
- Save it for future use

Copy the **Access Token** to your `.dev.vars` file.

**Note:** Access tokens expire after ~1 hour. For production, you'll want to implement refresh token logic, but for testing, you can regenerate the token as needed.

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

**Two ways to handle secrets:**

**A. For Local Development (testing):**
Edit `.dev.vars` file with your actual tokens:
```bash
# Edit the file
nano .dev.vars

# Or use any text editor
# Add your real tokens to .dev.vars
```

This file is used when you run `uv run pywrangler dev` locally.

**B. For Production Deployment (required):**
Upload secrets to Cloudflare Workers securely:

```bash
# Telegram
wrangler secret put TELEGRAM_BOT_TOKEN
wrangler secret put TELEGRAM_CHAT_ID

# Google Calendar (all 4 values from get_google_token.py)
wrangler secret put GOOGLE_CALENDAR_ACCESS_TOKEN
wrangler secret put GOOGLE_CALENDAR_REFRESH_TOKEN
wrangler secret put GOOGLE_CALENDAR_CLIENT_ID
wrangler secret put GOOGLE_CALENDAR_CLIENT_SECRET

# Notion
wrangler secret put NOTION_API_KEY
wrangler secret put NOTION_DATABASE_ID

# Optional: Google Calendar IDs for category calendars
# If you have multiple calendars, add their IDs here
# The briefing will query all configured calendars
wrangler secret put GOOGLE_CALENDAR_ID_ACADEMIC
wrangler secret put GOOGLE_CALENDAR_ID_BIRTHDAYS
wrangler secret put GOOGLE_CALENDAR_ID_ERRANDS
wrangler secret put GOOGLE_CALENDAR_ID_EVENTS
wrangler secret put GOOGLE_CALENDAR_ID_FINANCE
wrangler secret put GOOGLE_CALENDAR_ID_HOLIDAYS
wrangler secret put GOOGLE_CALENDAR_ID_OCCUPATION
wrangler secret put GOOGLE_CALENDAR_ID_PASSION
```

**Finding Calendar IDs:**
1. Go to Google Calendar settings
2. Select a calendar from the left sidebar
3. Scroll to "Integrate calendar"
4. Copy the "Calendar ID" (looks like: abc123@group.calendar.google.com)

**Important:** 
- `.dev.vars` = Local testing only (git-ignored, never committed)
- `wrangler secret put` = Production deployment (stored securely in Cloudflare)
- You need BOTH for a complete setup
- Calendar IDs are optional - if not set, only the primary calendar will be queried

### 7. Deploy (on your local machine)

This uploads your code to Cloudflare's cloud:

```bash
# Deploy to Cloudflare Workers
uv run pywrangler deploy
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

### Manual Briefing

Trigger a briefing on demand:

- Send `/briefing` to get an immediate daily summary

This is useful for:
- Testing your setup
- Debugging empty briefings
- Getting updates outside the scheduled time

### Morning Briefing

Every day at 7 AM PST, you'll receive:
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
uv run pywrangler dev

# Test webhook with curl (in another terminal)
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
crons = ["0 14 * * *"]  # 7 AM PST = 14:00 UTC
```

### Debug Empty Briefings

If your briefings are empty:

1. Send `/briefing` command to test manually
2. Check logs: `wrangler tail`
3. Verify calendar IDs are set (see step 6 in setup)
4. Confirm events exist in your calendars
5. Check Notion database property names match:
   - "Name" (title)
   - "Due Date" (date)
   - "Status" (status)

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
