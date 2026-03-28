#!/bin/bash

# Test script for local Telegram webhook
# Usage: ./test_local.sh [command]
# Example: ./test_local.sh "/brief"

COMMAND="${1:-/brief}"
LOCAL_URL="http://localhost:8787/webhook"

echo "🧪 Testing command: $COMMAND"
echo "📍 Sending to: $LOCAL_URL"
echo ""

curl -X POST "$LOCAL_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"update_id\": 123456789,
    \"message\": {
      \"message_id\": 1,
      \"from\": {
        \"id\": 123456,
        \"is_bot\": false,
        \"first_name\": \"Test\",
        \"username\": \"testuser\"
      },
      \"chat\": {
        \"id\": 123456,
        \"first_name\": \"Test\",
        \"username\": \"testuser\",
        \"type\": \"private\"
      },
      \"date\": $(date +%s),
      \"text\": \"$COMMAND\"
    }
  }"

echo ""
echo ""
echo "✅ Request sent!"
