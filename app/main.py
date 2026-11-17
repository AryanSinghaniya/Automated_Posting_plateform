"""FastAPI application entry point."""

import logging
from fastapi import FastAPI, status
from app.schemas import PostRequest, PostResponse
from app.services.posting_service import post_everywhere

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("automated_posting")

app = FastAPI(
    title="Automated Multi-Platform Posting API",
    description="Publishes a short message with exactly one link to multiple third-party platforms concurrently.",
    version="1.0.0",
)


@app.get("/health", status_code=status.HTTP_200_OK, summary="Health Check")
async def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}


@app.post(
    "/posting",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
    summary="Post message across all configured platforms",
)
async def create_post(payload: PostRequest) -> PostResponse:
    """Validate message and publish concurrently to all supported platforms."""
    logger.info("Received posting request with message length: %d", len(payload.message))

    response = await post_everywhere(payload.message)

    # Log each platform result (never log secrets)
    for res in response.results:
        logger.info(
            "Platform: %s | Status: %s | URL: %s | Error: %s",
            res.platform,
            res.status,
            res.posted_url,
            res.error,
        )

    return response

