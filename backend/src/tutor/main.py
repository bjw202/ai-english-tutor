"""FastAPI application for AI English Tutor.

Main entry point for the FastAPI application. Creates and configures
the app with CORS middleware and API routers.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tutor.config import settings
from tutor.routers import tutor


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance

    Example:
        >>> app = create_app()
        >>> # Use with uvicorn: uvicorn tutor.main:app --reload
    """
    app = FastAPI(
        title="AI English Tutor",
        description="AI-based personalized English learning tutor backend system",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(tutor.router, prefix="/api/v1")

    return app


# Global app instance for running with uvicorn directly
app = create_app()
