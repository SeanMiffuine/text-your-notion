#!/bin/bash

# Set Telegram Webhook
# This tells Telegram where to send messages for your bot

set -e

# Load bot token from .dev.vars
source .dev.vars

WORKER_URL="https://text-your-notion.work-seantang.workers.dev"

echo "🔗 Setting Telegram webhook..."
echo "Worker URL: $WORKER_URL"
echo ""

curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${WORKER_URL}\"}"

echo ""
echo ""
echo "✅ Webhook set! Your bot is now live."
echo ""
echo "Test it by sending a message to your bot on Telegram!"
