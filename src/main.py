from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.config.settings import settings
from src.core.http import close_clients


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_clients()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Criteria API",
        description="API for evaluating repository compliance across eight criteria areas",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )
    app.include_router(router)
    return app


app = create_app()
