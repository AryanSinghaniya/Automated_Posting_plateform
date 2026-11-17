"""Configuration settings loaded from environment variables or .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHANNEL: str = ""
    MASTODON_BASE_URL: str = "https://mastodon.social"
    MASTODON_TOKEN: str = ""
    BLUESKY_HANDLE: str = ""
    BLUESKY_APP_PASSWORD: str = ""
    GITHUB_TOKEN: str = ""
    PASTEEE_API_KEY: str = ""
    NTFY_TOPIC: str = ""


settings = Settings()
