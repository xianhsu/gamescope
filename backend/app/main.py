"""FastAPI application factory: middleware, CORS, unified error handlers, OpenAPI."""

from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import AppError, ErrorCode
from app.core.logging import configure_logging, get_logger, new_request_id, request_id_ctx

configure_logging(settings.log_level)
logger = get_logger("app")

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "AI-Powered Gaming News Intelligence Platform — grounded, cited RAG over gaming news."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error_response(status: int, code: str, message: str, request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "request_id": request_id}},
    )


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Attach a request id, time the request, and log method/path/status only (no secrets)."""
    rid = request.headers.get("X-Request-ID") or new_request_id()
    request_id_ctx.set(rid)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except AppError:
        raise
    except Exception:  # pragma: no cover — safety net
        logger.exception("unhandled_exception")
        resp = _error_response(500, ErrorCode.INTERNAL_ERROR, "An unexpected error occurred.", rid)
        resp.headers["X-Request-ID"] = rid
        return resp
    duration_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "request",
        extra={
            "extra": {
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            }
        },
    )
    response.headers["X-Request-ID"] = rid
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    rid = request_id_ctx.get()
    logger.warning("app_error", extra={"extra": {"code": exc.code, "message": exc.message}})
    return _error_response(exc.status_code, exc.code, exc.message, rid)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    rid = request_id_ctx.get()
    detail = "; ".join(
        f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in exc.errors()[:5]
    )
    return _error_response(422, ErrorCode.INVALID_REQUEST, detail or "Invalid request.", rid)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"name": settings.app_name, "version": __version__, "docs": "/api/docs"}


app.include_router(api_router, prefix=settings.api_v1_prefix)
