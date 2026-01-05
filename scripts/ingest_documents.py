"""Script to ingest documents into the NeuraBuddy knowledge base."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.document_loader import DocumentLoader
from app.chunking.semantic_chunker import SemanticChunker
from app.rag.vector_store import VectorStore
from app.core.config import settings
from app.core.logging_config import logger


def ingest_file(file_path: str, source: str = "manual_ingestion"):
    """Ingest a single file into the knowledge base."""
    logger.info(f"Ingesting file: {file_path}")
    
    # Determine file type
    file_path_obj = Path(file_path)
    if file_path_obj.suffix.lower() == ".pdf":
        file_type = "pdf"
    elif file_path_obj.suffix.lower() in [".html", ".htm"]:
        file_type = "html"
    else:
        file_type = "text"
    
    # Load document
    loader = DocumentLoader()
    document = loader.load_document(file_path=file_path, file_type=file_type)
    
    # Chunk document
    chunker = SemanticChunker()
    chunks = chunker.chunk_document(
        content=document["content"],
        source_metadata=document["metadata"],
        source=source
    )
    
    # Add to vector store
    vector_store = VectorStore()
    chunk_ids = vector_store.add_chunks(chunks)
    
    logger.info(f"Successfully ingested {file_path}: {len(chunk_ids)} chunks created")
    return len(chunk_ids)


def ingest_directory(directory: str, source: str = "batch_ingestion"):
    """Ingest all supported files from a directory."""
    directory_path = Path(directory)
    
    if not directory_path.exists():
        logger.error(f"Directory not found: {directory}")
        return
    
    supported_extensions = [".pdf", ".html", ".htm", ".txt"]
    files = [
        f for f in directory_path.rglob("*")
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]
    
    logger.info(f"Found {len(files)} files to ingest")
    
    total_chunks = 0
    for file_path in files:
        try:
            chunks = ingest_file(str(file_path), source=source)
            total_chunks += chunks
        except Exception as e:
            logger.error(f"Error ingesting {file_path}: {str(e)}")
    
    logger.info(f"Batch ingestion complete: {total_chunks} total chunks created")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest documents into NeuraBuddy knowledge base")
    parser.add_argument("path", help="File or directory path to ingest")
    parser.add_argument("--source", default="manual_ingestion", help="Source identifier")
    parser.add_argument("--directory", action="store_true", help="Treat path as directory")
    
    args = parser.parse_args()
    
    if args.directory:
        ingest_directory(args.path, source=args.source)
    else:
        ingest_file(args.path, source=args.source)

