"""Application entry point."""

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    """Build and wire the FastAPI application.

    Using a factory (instead of a module-level `app = FastAPI()`) lets tests
    build isolated instances with their own dependency overrides.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "Personal finance management API: transactions, categories, budgets and alerts."
        ),
    )

    app.include_router(health_router)
    app.include_router(api_router)

    return app


app = create_app()
