"""ntfy.sh pub-sub web feed platform integration."""

from app.config import settings
from app.platforms.base import BasePlatform


class NtfyPlatform(BasePlatform):
    """Platform implementation for ntfy.sh public web topic broadcast."""

    name = "ntfy"

    async def publish(self, message: str) -> str:
        """Publish a message to an ntfy.sh public topic."""
        topic = settings.NTFY_TOPIC.strip()
        if not topic:
            raise ValueError("NTFY_TOPIC not configured")

        url = "https://ntfy.sh"
        payload = {
            "topic": topic,
            "title": "Automated Post",
            "message": message,
        }

        async with self.get_client() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return f"https://ntfy.sh/{topic}"

