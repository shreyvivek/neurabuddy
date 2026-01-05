"""NeuraBuddy FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

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

