from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.config.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Criteria API",
        description="Criteria API",
        version="0.0.1",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )
    app.include_router(router)
    return app


app = create_app()
