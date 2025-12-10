"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.api.routes import content
from src.mcp.client import mcp_manager
from src.utils.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting ContentForge AI API...")

    # Initialize MCP connections (optional - can be lazy loaded)
    try:
        await mcp_manager.initialize()
    except Exception as e:
        logger.warning(f"MCP initialization failed (non-critical): {e}")

    logger.info("ContentForge AI API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down ContentForge AI API...")
    await mcp_manager.close()
    logger.info("ContentForge AI API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="ContentForge AI",
    description="Multi-agent AI content creation platform powered by LangGraph and MCP",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["https://contentforge.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(content.router, prefix="/api/v1", tags=["content"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "ContentForge AI",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
    )
