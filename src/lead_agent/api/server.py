"""FastAPI server for Lead Agent REST API."""

import argparse
import sys
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import router


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Lead Agent API server")
    yield
    # Shutdown
    logger.info("Shutting down Lead Agent API server")


# Create FastAPI application
app = FastAPI(
    title="Lead Agent API",
    description="REST API for Lead Agent workflow orchestration system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Lead Agent API",
        "version": "1.0.0",
        "description": "REST API for Lead Agent workflow orchestration system",
        "docs_url": "/docs",
        "health_url": "/api/v1/health"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred"
        }
    )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return app


def main():
    """Main entry point for the API server."""
    parser = argparse.ArgumentParser(description="Lead Agent API Server")
    parser.add_argument(
        "--host", 
        default="127.0.0.1", 
        help="Host to bind the server to"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="Number of worker processes"
    )
    parser.add_argument(
        "--config", 
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    log_level = "debug" if args.debug else "info"
    
    logger.info(
        "Starting Lead Agent API server",
        host=args.host,
        port=args.port,
        debug=args.debug,
        reload=args.reload,
        workers=args.workers
    )
    
    # Run the server
    uvicorn.run(
        "lead_agent.api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=log_level,
        workers=args.workers if not args.reload else 1,
        access_log=True
    )


if __name__ == "__main__":
    main()
