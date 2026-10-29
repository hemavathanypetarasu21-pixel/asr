"""FastAPI application: middleware, routers and lifecycle. Start it with `python server.py`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import truststore

# Use the OS certificate store for outbound HTTPS (Supabase JWKS, Gemini, model downloads),
# so TLS inspection by antivirus or corporate proxies does not break verification.
# Done here (not in server.py) because reload workers import this module in a fresh process.
truststore.inject_into_ssl()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from api.routers import routers  # noqa: E402
from src.config import settings  # noqa: E402
from src.db import close_database, connect_database  # noqa: E402


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await connect_database()
    yield
    await close_database()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in routers:
        application.include_router(router)

    @application.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    return application


app = create_app()
