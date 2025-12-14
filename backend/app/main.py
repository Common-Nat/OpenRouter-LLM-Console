from contextlib import asynccontextmanager
import logging
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.logging_config import configure_logging, request_id_ctx_var
from .db import init_db
from .api.routes.health import router as health_router
from .api.routes.models import router as models_router
from .api.routes.profiles import router as profiles_router
from .api.routes.sessions import router as sessions_router
from .api.routes.messages import router as messages_router
from .api.routes.stream import router as stream_router
from .api.routes.usage import router as usage_router
from .api.routes.documents import router as documents_router

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_title, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
