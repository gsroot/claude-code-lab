"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.api.routes import auth, content, websocket
from src.mcp.client import mcp_manager
from src.utils.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Content Mate API...")

    # Initialize MCP connections (optional - can be lazy loaded)
    try:
        await mcp_manager.initialize()
    except Exception as e:
        logger.warning(f"MCP initialization failed (non-critical): {e}")

    logger.info("Content Mate API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Content Mate API...")
    await mcp_manager.close()
    logger.info("Content Mate API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Content Mate",
    description="Multi-agent AI content creation platform powered by LangGraph and MCP",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["https://contentmate.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(content.router, prefix="/api/v1", tags=["content"])
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Content Mate",
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
