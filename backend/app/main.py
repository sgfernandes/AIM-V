from fastapi import FastAPI

from backend.app.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="AIM-V ITV M&V Platform",
        version="0.1.0",
        description="FastAPI backend for the ITV multi-agent M&V platform.",
    )
    app.include_router(router)
    return app


app = create_app()
