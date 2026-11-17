"""Paste.ee platform integration."""

from app.config import settings
from app.platforms.base import BasePlatform


class PasteeePlatform(BasePlatform):
    """Platform implementation for Paste.ee paste publication."""

    name = "pasteee"

    async def publish(self, message: str) -> str:
        """Publish a paste to Paste.ee."""
        api_key = settings.PASTEEE_API_KEY.strip()
        if not api_key:
            raise ValueError("PASTEEE_API_KEY not configured")

        url = "https://api.paste.ee/v1/pastes"
        headers = {
            "X-Auth-Token": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "description": "Automated post",
            "sections": [
                {
                    "name": "Post",
                    "contents": message,
                }
            ],
        }

        async with self.get_client() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                errors = data.get("errors", [])
                error_msg = errors[0].get("message", "Unknown error") if errors else "Paste.ee API failed"
                raise RuntimeError(f"Paste.ee API error: {error_msg}")

            return data["link"]

