"""
Request Correlation ID, Structured JSON Logging & Error Envelope Middleware.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("unilog.api")


async def correlation_id_middleware(request: Request, call_next: Callable) -> Response:
    """Assign X-Request-ID to incoming request and attach to response headers."""
    request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id

    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)

    response.headers["X-Request-ID"] = request_id

    # Structured JSON log (strictly omitting secrets, passwords, or tokens)
    log_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
        "client_ip": request.client.host if request.client else "unknown",
    }
    # Log non-sensitive access record
    if response.status_code >= 400:
        logger.warning(json.dumps(log_data))
    else:
        logger.info(json.dumps(log_data))

    return response


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform error response envelopes for all exceptions."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
        error_code = "HTTP_ERROR"
        if exc.status_code == 401:
            error_code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            error_code = "FORBIDDEN"
        elif exc.status_code == 404:
            error_code = "NOT_FOUND"
        elif exc.status_code == 429:
            error_code = "RATE_LIMIT_EXCEEDED"

        headers = dict(exc.headers or {})
        headers["X-Request-ID"] = request_id

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": str(exc.detail),
                "error": {
                    "code": error_code,
                    "message": str(exc.detail),
                    "request_id": request_id,
                    "status_code": exc.status_code,
                }
            },
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.errors(),
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Input validation failed. Please check field formats.",
                    "request_id": request_id,
                    "details": exc.errors(),
                }
            },
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
        logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please contact system support.",
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id},
        )
