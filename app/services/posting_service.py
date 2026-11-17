"""Service layer orchestrating concurrent multi-platform posting."""

import asyncio
from app.platforms.base import BasePlatform
from app.platforms.bluesky import BlueskyPlatform
from app.platforms.gist import GistPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.ntfy import NtfyPlatform
from app.platforms.pasteee import PasteeePlatform
from app.platforms.telegram import TelegramPlatform
from app.schemas import PlatformResult, PostResponse

# Active platform integrations
PLATFORM_CLASSES: list[type[BasePlatform]] = [
    TelegramPlatform,
    MastodonPlatform,
    BlueskyPlatform,
    GistPlatform,
    PasteeePlatform,
    NtfyPlatform,
]


async def post_everywhere(message: str) -> PostResponse:
    """Instantiate and execute posting to all platforms concurrently.

    Args:
        message: Validated message containing exactly one URL.

    Returns:
        PostResponse: Aggregated response with per-platform results.
    """
    platforms = [cls() for cls in PLATFORM_CLASSES]
    results: list[PlatformResult] = await asyncio.gather(
        *(platform.post(message) for platform in platforms)
    )

    success = any(result.status == "success" for result in results)
    return PostResponse(success=success, results=list(results))
