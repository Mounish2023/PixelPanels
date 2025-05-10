"""Main FastAPI application."""
import os
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from contextlib import asynccontextmanager
from app.config import settings
from app.routes import comic_routes, interaction_routes, explore_routes
from app.models.database import Base
from app.database import engine

# Configure logging
logger.add("app.log", rotation="500 MB", level="INFO")

async def create_db_and_tables():
    """Create database and tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database and tables created.")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Startup event handler."""
        logger.info("Starting up...")
        await create_db_and_tables()
        yield
        logger.info("Shutting down...")

    app = FastAPI(
        title=settings.APP_NAME,
        description="AI Comic Creator API",
        version="0.1.0",
        debug=settings.DEBUG,
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify your frontend domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(
        comic_routes.router,
        prefix="/api/v1/comics",
        tags=["comics"]
    )

    app.include_router(
        interaction_routes.router,
        prefix="/api/v1/interactions",
        tags=["interactions"]
    )

    app.include_router(
        explore_routes.router,
        prefix="/api/v1/explore",
        tags=["explore"]
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)