"""Base platform abstraction for social media and publishing services."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import httpx

from app.schemas import PlatformResult

DEFAULT_TIMEOUT = 15.0


class BasePlatform(ABC):
    """Abstract base class for all posting platforms."""

    name: str

    def get_client(self) -> httpx.AsyncClient:
        """Create an HTTP client configured with standard timeout."""
        return httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)

    @abstractmethod
    async def publish(self, message: str) -> str:
        """Publish the message to the platform and return the public URL.

        Raises:
            Exception: If publishing fails or credentials are not configured.
        """
        pass

    async def post(self, message: str) -> PlatformResult:
        """Execute publishing with exception handling, returning a PlatformResult.

        This method guarantees no uncaught exceptions escape.
        """
        try:
            posted_url = await self.publish(message)
            now = datetime.now(timezone.utc)
            return PlatformResult(
                platform=self.name,
                status="success",
                posted_url=posted_url,
                public_access=True,
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M:%S"),
                error=None,
            )
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            body_snippet = exc.response.text[:200].strip()
            error_message = (
                f"{self.name} HTTP {status_code}: {body_snippet}"
                if body_snippet
                else f"{self.name} HTTP {status_code}"
            )
            return PlatformResult(
                platform=self.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error=error_message,
            )
        except httpx.RequestError as exc:
            return PlatformResult(
                platform=self.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error=f"{self.name} request error: {str(exc)}",
            )
        except Exception as exc:
            return PlatformResult(
                platform=self.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error=str(exc),
            )

