"""GitHub Gist platform integration."""

from app.config import settings
from app.platforms.base import BasePlatform


class GistPlatform(BasePlatform):
    """Platform implementation for GitHub Gist creation."""

    name = "gist"

    async def publish(self, message: str) -> str:
        """Create a public GitHub Gist."""
        token = settings.GITHUB_TOKEN.strip()
        if not token:
            raise ValueError("GITHUB_TOKEN not configured")

        url = "https://api.github.com/gists"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        payload = {
            "description": "Automated post",
            "public": True,
            "files": {
                "post.md": {
                    "content": message,
                }
            },
        }

        async with self.get_client() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["html_url"]

