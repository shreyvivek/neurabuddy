"""Configuration settings for NeuraBuddy backend."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-large"
    
    # ChromaDB Configuration
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "neurabuddy_knowledge_base"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Chunking Configuration
    chunk_size: int = 600  # Target tokens per chunk
    chunk_overlap: int = 100  # Overlap tokens
    
    # RAG Configuration
    retrieval_top_k: int = 5  # Number of chunks to retrieve
    min_retrieval_score: float = 0.7  # Minimum similarity score
    
    # Optional: PostgreSQL with pgvector
    database_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

