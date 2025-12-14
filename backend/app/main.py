from contextlib import asynccontextmanager
import logging
import time
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.logging_config import configure_logging, request_id_ctx_var
from .core.ratelimit import limiter
from .db import init_db
from .api.routes.health import router as health_router
from .api.routes.models import router as models_router
from .api.routes.profiles import router as profiles_router
from .api.routes.sessions import router as sessions_router
from .api.routes.messages import router as messages_router
from .api.routes.stream import router as stream_router
from .api.routes.usage import router as usage_router
from .api.routes.documents import router as documents_router
from .api.routes.logs import router as logs_router

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    # Security check: Warn if exposed beyond localhost without HTTPS
    non_localhost_origins = [
        origin for origin in settings.origins_list
        if "localhost" not in origin and "127.0.0.1" not in origin
    ]
    if non_localhost_origins:
        logger.warning(
            "Application configured with non-localhost origins. "
            "Ensure HTTPS is enforced via reverse proxy (nginx/caddy/traefik). "
            "Never expose FastAPI directly to the internet without TLS.",
            extra={
                "action": "security_check",
                "non_localhost_origins": non_localhost_origins
            }
        )
    
    yield


app = FastAPI(title=settings.app_title, lifespan=lifespan)

# Register rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Add X-Error-Code header to all HTTPException responses."""
    headers = dict(exc.headers) if exc.headers else {}
    
    # Add request ID to headers
    headers["X-Request-ID"] = request_id_ctx_var.get("-")
    
    # Add error code to headers if present in detail
    if isinstance(exc.detail, dict) and "error_code" in exc.detail:
        headers["X-Error-Code"] = exc.detail["error_code"]
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
        headers=headers
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,  # Restricted to configured origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    token = request_id_ctx_var.set(request_id)
    start_time = time.perf_counter()
    response = None

    try:
        response = await call_next(request)
        return response
    except Exception:
        logger.exception("Unhandled exception during request", extra={"path": request.url.path, "method": request.method})
        raise
    finally:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code if response is not None else 500
        if response is not None:
            response.headers["X-Request-ID"] = request_id
        logger.info(
            "Request completed",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": status_code,
                "latency_ms": round(elapsed_ms, 2),
            },
        )
        request_id_ctx_var.reset(token)


app.include_router(health_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(profiles_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(messages_router, prefix="/api")
app.include_router(stream_router, prefix="/api")
app.include_router(usage_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(logs_router, prefix="/api/logs", tags=["logs"])
