"""NeuraBuddy FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import os

from app.api.routes import router
from app.core.config import settings
from app.core.logging_config import logger

# Initialize FastAPI app
app = FastAPI(
    title="NeuraBuddy API",
    description="RAG-based educational chatbot for neuroanatomy learning",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["neurabuddy"])

# Serve frontend static files
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    # Mount static assets
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend for all non-API routes."""
        # Don't serve API routes
        if full_path.startswith("api/") or full_path == "docs" or full_path == "openapi.json":
            return {"error": "Not found"}
        # Serve static files if they exist
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Default to index.html for SPA routing
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Frontend not found"}


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting NeuraBuddy API server...")
    logger.info(f"OpenAI Model: {settings.openai_model}")
    logger.info(f"Embedding Model: {settings.openai_embedding_model}")
    logger.info(f"Vector Store: {settings.chroma_collection_name}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down NeuraBuddy API server...")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "NeuraBuddy API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

