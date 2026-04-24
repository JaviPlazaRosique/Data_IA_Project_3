import logging
import time
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import Response
from jose import JWTError, jwt
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import router as v1_router
from app.config import settings
from app.core.limiter import limiter
from app.db.firestore import get_firestore
from app.db.session import engine

logger = logging.getLogger("audit")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    get_firestore()  # initialise Firebase app at startup
    yield
    await engine.dispose()


app = FastAPI(
    title="The Electric Curator — Portal API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

class CSPMiddleware(BaseHTTPMiddleware):
    """Art. 32 / Art. 25 — Content Security Policy headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none';"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Art. 5(2) accountability — logs method, path, user_id, and duration.

    No request or response bodies are logged to avoid capturing personal data.
    Logs go to stdout (Cloud Run → Cloud Logging). Set a 90-day retention policy
    in GCP Console → Cloud Logging → Log buckets.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000)

        user_id: str | None = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                payload = jwt.decode(
                    auth_header[7:],
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_exp": False},
                )
                user_id = payload.get("sub")
            except JWTError:
                pass

        logger.info(
            '{"method": "%s", "path": "%s", "status": %d, "user_id": "%s", "duration_ms": %d}',
            request.method,
            request.url.path,
            response.status_code,
            user_id or "anonymous",
            duration_ms,
        )
        return response


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(CSPMiddleware)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/api/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
