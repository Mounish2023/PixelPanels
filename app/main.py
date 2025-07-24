"""Main FastAPI application."""
from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from fastapi.middleware.cors import CORSMiddleware

from loguru import logger

from app.config import settings
from app.routes import comic_routes
from contextlib import asynccontextmanager
from app.database import BlobContainerClientSingleton

# Configure logging
logger.add("app.log", rotation="500 MB", level="INFO")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await BlobContainerClientSingleton.get_instance()
    yield
    await BlobContainerClientSingleton.close_instance()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
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
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.get("/scalar")
    async def get_scalar_docs():
        """Get Scalar documentation."""
        return get_scalar_api_reference(
            openapi_url=app.openapi_url,
            title=app.title,
        )
    
    return app

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
