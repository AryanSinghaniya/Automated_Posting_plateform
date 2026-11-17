"""Platform integrations for automated posting."""

from app.platforms.base import BasePlatform
from app.platforms.bluesky import BlueskyPlatform
from app.platforms.gist import GistPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.ntfy import NtfyPlatform
from app.platforms.pasteee import PasteeePlatform
from app.platforms.telegram import TelegramPlatform

__all__ = [
    "BasePlatform",
    "BlueskyPlatform",
    "GistPlatform",
    "MastodonPlatform",
    "NtfyPlatform",
    "PasteeePlatform",
    "TelegramPlatform",
]
