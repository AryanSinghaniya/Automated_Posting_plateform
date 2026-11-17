"""Pydantic schemas and request/response models."""

import re
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl, TypeAdapter, ValidationError, field_validator

URL_REGEX = re.compile(r"https?://\S+")
HTTP_URL_ADAPTER = TypeAdapter(HttpUrl)


class PostRequest(BaseModel):
    """Request model for publishing a message."""

    message: str = Field(
        ...,
        description="The message to post. Must contain exactly one valid HTTP/HTTPS URL and be at most 200 characters.",
        examples=["Check out our new release at https://example.com/announcement !"],
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate that message is non-empty, <=200 chars, and contains exactly one valid URL."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty.")

        if len(v) > 200:
            raise ValueError(f"Message exceeds maximum length of 200 characters (got {len(v)}).")

        urls = URL_REGEX.findall(v)
        if len(urls) == 0:
            raise ValueError("Message must contain exactly one link (found 0).")
        if len(urls) > 1:
            raise ValueError(f"Message must contain exactly one link (found {len(urls)}).")

        raw_url = urls[0]
        try:
            HTTP_URL_ADAPTER.validate_python(raw_url)
        except ValidationError as e:
            error_details = e.errors()[0]["msg"] if e.errors() else str(e)
            raise ValueError(f"Invalid URL '{raw_url}': {error_details}") from e

        return v


class PlatformResult(BaseModel):
    """Result of publishing to a single platform."""

    platform: str
    status: Literal["success", "failed"]
    posted_url: str | None = None
    public_access: bool
    date: str | None = None
    time: str | None = None
    error: str | None = None


class PostResponse(BaseModel):
    """Response model for the /posting endpoint."""

    success: bool
    results: list[PlatformResult]

