"""Mastodon status platform integration."""

from app.config import settings
from app.platforms.base import BasePlatform


class MastodonPlatform(BasePlatform):
    """Platform implementation for Mastodon status updates."""

    name = "mastodon"

    async def publish(self, message: str) -> str:
        """Publish a status to Mastodon."""
        token = settings.MASTODON_TOKEN.strip()
        if not token:
            raise ValueError("MASTODON_TOKEN not configured")

        base_url = (settings.MASTODON_BASE_URL.strip() or "https://mastodon.social").rstrip("/")
        url = f"{base_url}/api/v1/statuses"
        headers = {
            "Authorization": f"Bearer {token}",
        }
        data = {
            "status": message,
            "visibility": "public",
        }

        async with self.get_client() as client:
            response = await client.post(url, headers=headers, data=data)
            response.raise_for_status()
            res_json = response.json()
            return res_json["url"]

