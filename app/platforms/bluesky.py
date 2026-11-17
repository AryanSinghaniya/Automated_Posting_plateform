"""Bluesky AT Protocol platform integration."""

from datetime import datetime, timezone

from app.config import settings
from app.platforms.base import BasePlatform


class BlueskyPlatform(BasePlatform):
    """Platform implementation for Bluesky post publication."""

    name = "bluesky"

    async def publish(self, message: str) -> str:
        """Publish a post to Bluesky using AT Protocol."""
        handle = settings.BLUESKY_HANDLE.strip()
        app_password = settings.BLUESKY_APP_PASSWORD.strip()

        if not handle:
            raise ValueError("BLUESKY_HANDLE not configured")
        if not app_password:
            raise ValueError("BLUESKY_APP_PASSWORD not configured")

        async with self.get_client() as client:
            # Step 1: Create session
            session_url = "https://bsky.social/xrpc/com.atproto.server.createSession"
            session_payload = {
                "identifier": handle,
                "password": app_password,
            }
            session_resp = await client.post(session_url, json=session_payload)
            session_resp.raise_for_status()
            session_data = session_resp.json()

            access_jwt = session_data["accessJwt"]
            did = session_data["did"]
            user_handle = session_data.get("handle", handle)

            # Step 2: Create post record
            record_url = "https://bsky.social/xrpc/com.atproto.repo.createRecord"
            record_headers = {
                "Authorization": f"Bearer {access_jwt}",
            }
            created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            record_payload = {
                "repo": did,
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": message,
                    "createdAt": created_at,
                },
            }
            record_resp = await client.post(record_url, headers=record_headers, json=record_payload)
            record_resp.raise_for_status()
            record_data = record_resp.json()

            uri = record_data["uri"]
            rkey = uri.rstrip("/").split("/")[-1]
            return f"https://bsky.app/profile/{user_handle}/post/{rkey}"

