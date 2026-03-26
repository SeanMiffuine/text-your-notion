#!/bin/bash

# Deploy Secrets to Cloudflare Workers
# This script reads from .dev.vars and uploads secrets to Cloudflare

set -e

echo "🚀 Deploying secrets to Cloudflare Workers..."
echo ""

# Check if .dev.vars exists
if [ ! -f .dev.vars ]; then
    echo "❌ Error: .dev.vars file not found"
    exit 1
fi

# Source the .dev.vars file
source .dev.vars

# Function to put secret
put_secret() {
    local key=$1
    local value=$2
    
    if [ -z "$value" ]; then
        echo "⚠️  Skipping $key (empty value)"
        return
    fi
    
    echo "📤 Uploading $key..."
    echo "$value" | wrangler secret put "$key"
}

# Upload all secrets
echo "Uploading Telegram secrets..."
put_secret "TELEGRAM_BOT_TOKEN" "$TELEGRAM_BOT_TOKEN"
put_secret "TELEGRAM_CHAT_ID" "$TELEGRAM_CHAT_ID"

echo ""
echo "Uploading Google Calendar secrets..."
put_secret "GOOGLE_CALENDAR_ACCESS_TOKEN" "$GOOGLE_CALENDAR_ACCESS_TOKEN"
put_secret "GOOGLE_CALENDAR_REFRESH_TOKEN" "$GOOGLE_CALENDAR_REFRESH_TOKEN"
put_secret "GOOGLE_CALENDAR_CLIENT_ID" "$GOOGLE_CALENDAR_CLIENT_ID"
put_secret "GOOGLE_CALENDAR_CLIENT_SECRET" "$GOOGLE_CALENDAR_CLIENT_SECRET"

echo ""
echo "Uploading Google Calendar ID mappings..."
put_secret "GOOGLE_CALENDAR_ID_ACADEMIC" "$GOOGLE_CALENDAR_ID_ACADEMIC"
put_secret "GOOGLE_CALENDAR_ID_BIRTHDAYS" "$GOOGLE_CALENDAR_ID_BIRTHDAYS"
put_secret "GOOGLE_CALENDAR_ID_ERRANDS" "$GOOGLE_CALENDAR_ID_ERRANDS"
put_secret "GOOGLE_CALENDAR_ID_EVENTS" "$GOOGLE_CALENDAR_ID_EVENTS"
put_secret "GOOGLE_CALENDAR_ID_FINANCE" "$GOOGLE_CALENDAR_ID_FINANCE"
put_secret "GOOGLE_CALENDAR_ID_OCCUPATION" "$GOOGLE_CALENDAR_ID_OCCUPATION"
put_secret "GOOGLE_CALENDAR_ID_PASSION" "$GOOGLE_CALENDAR_ID_PASSION"

echo ""
echo "Uploading Notion secrets..."
put_secret "NOTION_API_KEY" "$NOTION_API_KEY"
put_secret "NOTION_DATABASE_ID" "$NOTION_DATABASE_ID"

echo ""
echo "✅ All secrets uploaded successfully!"
echo ""
echo "Next steps:"
echo "1. Deploy your worker: uv run pywrangler deploy"
echo "2. Set Telegram webhook to your worker URL"
