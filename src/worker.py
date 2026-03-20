"""
Main Cloudflare Worker entrypoint for Notion Assistant Bot.
Handles Telegram webhooks and scheduled morning briefings.
"""
from js import Response
import json
from handlers.telegram import handle_message
from handlers.briefing import generate_briefing


class NotionAssistantBot:
    """Main Worker class with fetch and scheduled handlers."""
    
    def __init__(self, env):
        self.env = env
    
    async def fetch(self, request):
        """
        Handle incoming HTTP requests (Telegram webhooks).
        
        Args:
            request: Incoming HTTP request from Telegram
            
        Returns:
            Response object
        """
        try:
            # Only accept POST requests
            if request.method != "POST":
                return Response.json(
                    {"error": "Method not allowed"},
                    status=405
                )
            
            # Parse Telegram webhook payload
            body_text = await request.text()
            data = json.loads(body_text)
            
            # Check if this is a message update
            if "message" not in data:
                return Response.json({"ok": True}, status=200)
            
            message = data["message"]
            
            # Extract message details
            chat_id = message["chat"]["id"]
            text = message.get("text", "")
            
            # Security: Only respond to authorized chat ID
            authorized_chat_id = int(self.env.TELEGRAM_CHAT_ID)
            if chat_id != authorized_chat_id:
                print(f"Unauthorized access attempt from chat_id: {chat_id}")
                return Response.json({"ok": True}, status=200)
            
            # Ignore empty messages
            if not text:
                return Response.json({"ok": True}, status=200)
            
            # Process message and get response
            response_text = await handle_message(self.env, chat_id, text)
            
            # Send response to Telegram
            await self._send_telegram_message(chat_id, response_text)
            
            return Response.json({"ok": True}, status=200)
            
        except Exception as e:
            print(f"Error in fetch handler: {e}")
            # Try to send error to user
            try:
                if "message" in data:
                    chat_id = data["message"]["chat"]["id"]
                    await self._send_telegram_message(
                        chat_id,
                        f"❌ Something went wrong: {str(e)}"
                    )
            except:
                pass
            
            return Response.json(
                {"error": str(e)},
                status=500
            )
    
    async def scheduled(self, event):
        """
        Handle scheduled cron triggers (morning briefing at 9 AM PST).
        
        Args:
            event: Scheduled event object with cron info
        """
        try:
            print(f"Cron trigger fired: {event.cron}")
            
            # Generate briefing
            briefing_text = await generate_briefing(self.env)
            
            # Send to Telegram
            chat_id = self.env.TELEGRAM_CHAT_ID
            await self._send_telegram_message(chat_id, briefing_text)
            
        except Exception as e:
            print(f"Error in scheduled handler: {e}")
    
    async def _send_telegram_message(self, chat_id, text):
        """
        Send a message via Telegram Bot API.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text to send
        """
        import httpx
        
        url = f"https://api.telegram.org/bot{self.env.TELEGRAM_BOT_TOKEN}/sendMessage"
        
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }
            )


# Worker entrypoint
async def on_fetch(request, env):
    """Cloudflare Workers fetch handler."""
    bot = NotionAssistantBot(env)
    return await bot.fetch(request)


async def on_scheduled(event, env, ctx):
    """Cloudflare Workers scheduled handler."""
    bot = NotionAssistantBot(env)
    await bot.scheduled(event)
