"""FastAPI application entry point.

This module initializes the FastAPI application with all routes,
middleware, and configuration.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.

    Args:
        app: FastAPI application instance

    Yields:
        Control to the application
    """
    # Startup
    print("🚀 Starting Social Media Post Generation Agent System")
    print(f"   Environment: {settings.environment}")
    print(f"   API Host: {settings.api_host}:{settings.api_port}")

    # Initialize database (development only - use Alembic in production)
    if settings.environment == "development":
        print("   Initializing database tables...")
        init_db()

    yield

    # Shutdown
    print("👋 Shutting down Social Media Post Generation Agent System")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Social Media Post Generation Agent",
        description="Agentic system for generating multi-platform social media posts",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    # TODO: Import and include routers
    # from src.api.routes import router
    # app.include_router(router, prefix="/api")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "environment": settings.environment,
            "version": "0.1.0",
        }

    return app


# Application instance
app = create_app()
