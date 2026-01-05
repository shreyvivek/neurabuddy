"""Vector database setup and management using ChromaDB."""

import uuid
from typing import List, Dict, Any, Optional
import logging

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector database operations for NeuraBuddy."""
    
    def __init__(self):
        """Initialize ChromaDB client and embeddings."""
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key
        )
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize LangChain Chroma wrapper
        self.vectorstore = Chroma(
            client=self.client,
            collection_name=settings.chroma_collection_name,
            embedding_function=self.embeddings,
            persist_directory=settings.chroma_persist_dir
        )
        
        logger.info(f"Initialized vector store: {settings.chroma_collection_name}")
    
    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        document_id: Optional[str] = None
    ) -> List[str]:
        """
        Add chunks to the vector database.
        
        Args:
            chunks: List of chunk dicts with 'content' and 'metadata'
            document_id: Optional document identifier
        
        Returns:
            List of chunk IDs
        """
        if not chunks:
            return []
        
        chunk_ids = []
        texts = []
        metadatas = []
        
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)
            
            texts.append(chunk["content"])
            
            # Prepare metadata for ChromaDB
            metadata = chunk["metadata"].copy()
            metadata["chunk_id"] = chunk_id
            if document_id:
                metadata["document_id"] = document_id
            
            # ChromaDB requires string values for metadata
            metadata_clean = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata_clean[key] = value
                elif isinstance(value, list):
                    metadata_clean[key] = str(value)
                else:
                    metadata_clean[key] = str(value) if value else ""
            
            metadatas.append(metadata_clean)
        
        # Add to ChromaDB
        self.collection.add(
            ids=chunk_ids,
            documents=texts,
            metadatas=metadatas
        )
        
        logger.info(f"Added {len(chunks)} chunks to vector store")
        
        return chunk_ids
    
    def search(
        self,
        query: str,
        top_k: int = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Metadata filters (e.g., {"system": "brainstem"})
            min_score: Minimum similarity score (0-1)
        
        Returns:
            List of result dicts with 'content', 'metadata', and 'score'
        """
        top_k = top_k or settings.retrieval_top_k
        
        # Build where clause for filtering
        where = None
        if filter_dict:
            where = {}
            for key, value in filter_dict.items():
                where[key] = value
        
        # Search using ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where if where else None
        )
        
        # Format results
        formatted_results = []
        
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                # Calculate similarity score (ChromaDB uses cosine distance)
                # Convert distance to similarity: similarity = 1 - distance
                distances = results.get("distances", [[]])
                distance = distances[0][i] if distances and distances[0] else 1.0
                score = 1.0 - distance  # Convert distance to similarity
                
                # Apply minimum score filter
                if min_score and score < min_score:
                    continue
                
                chunk_id = results["ids"][0][i]
                content = results["documents"][0][i]
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                
                formatted_results.append({
                    "chunk_id": chunk_id,
                    "content": content,
                    "metadata": metadata,
                    "score": score
                })
        
        logger.info(f"Retrieved {len(formatted_results)} chunks for query")
        
        return formatted_results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": settings.chroma_collection_name
        }
    
    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks associated with a document."""
        try:
            # Get all chunks for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False

