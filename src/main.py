from fastapi import FastAPI
from src.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Criteria API",
        description="Criteria API",
        version="0.0.1",
    )
    app.include_router(router)
    return app


app = create_app()
