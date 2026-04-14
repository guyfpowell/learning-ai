import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Validate X-Internal-API-Key on every request except /health."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        expected_key = os.getenv("AI_SERVICE_API_KEY", "")
        provided_key = request.headers.get("X-Internal-API-Key", "")

        if not expected_key or provided_key != expected_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"},
            )

        return await call_next(request)
