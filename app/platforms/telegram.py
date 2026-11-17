"""Telegram channel platform integration."""

from app.config import settings
from app.platforms.base import BasePlatform


class TelegramPlatform(BasePlatform):
    """Platform implementation for Telegram channel broadcast."""

    name = "telegram"

    async def publish(self, message: str) -> str:
        """Publish a message to a Telegram channel."""
        bot_token = settings.TELEGRAM_BOT_TOKEN.strip()
        channel = settings.TELEGRAM_CHANNEL.strip()

        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not configured")
        if not channel:
            raise ValueError("TELEGRAM_CHANNEL not configured")

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": channel,
            "text": message,
        }

        async with self.get_client() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                error_desc = data.get("description", "Unknown Telegram error")
                raise RuntimeError(f"Telegram API returned not ok: {error_desc}")

            message_id = data["result"]["message_id"]
            channel_name = channel.lstrip("@")
            return f"https://t.me/{channel_name}/{message_id}"

