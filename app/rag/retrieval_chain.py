"""RAG retrieval chain with intent classification and context grounding."""

from typing import List, Dict, Any, Optional
import logging

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from app.core.config import settings
from app.rag.vector_store import VectorStore
from app.models.schemas import QueryIntent, SystemType, DifficultyLevel

logger = logging.getLogger(__name__)


class RetrievalChain:
    """RAG chain for query processing and retrieval."""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,  # Low temperature for factual accuracy
            openai_api_key=settings.openai_api_key
        )
        
        # Intent classification prompt
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intent classifier for a neuroanatomy educational chatbot.
Classify the user's query into one of these intents:
- factual_explanation: User wants a direct explanation of a concept
- concept_clarification: User is confused and needs clarification
- quiz_request: User wants to be quizzed or tested
- follow_up_question: User is asking a follow-up to a previous answer
- misconception_correction: User has a misunderstanding that needs correction

Respond with ONLY the intent name, nothing else."""),
            ("human", "Query: {query}")
        ])
        
        self.intent_chain = LLMChain(llm=self.llm, prompt=self.intent_prompt)
        
        # Answer generation prompt
        self.answer_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are NeuraBuddy, a medical-grade neuroanatomy teaching assistant.

CRITICAL RULES:
1. ONLY use information from the provided context. Do NOT use any external knowledge.
2. If the context does not contain enough information to answer, say "I don't have enough information in my knowledge base to answer this question accurately."
3. NEVER guess or hallucinate anatomical structures, pathways, or clinical information.
4. Always cite which structures/systems you're discussing.
5. Use precise anatomical terminology.
6. If discussing clinical correlations, clearly state the connection between anatomy and symptoms.
7. Format your response in clear markdown: use **bold** for key terms, bullet points (- ) for lists, and ## for major sections when appropriate.

Context:
{context}

User Query: {query}

Provide a clear, accurate, and educational response based ONLY on the context above. Use markdown for readability."""),
            ("human", "{query}")
        ])
        
        self.answer_chain = LLMChain(llm=self.llm, prompt=self.answer_prompt)
    
    def process_query(
        self,
        query: str,
        user_id: Optional[str] = None,
        difficulty_level: Optional[DifficultyLevel] = None,
        system_filter: Optional[SystemType] = None,
        clinical_only: bool = False
    ) -> Dict[str, Any]:
        """
        Process a user query through the RAG pipeline.
        
        Returns:
            Dict with 'answer', 'sources', 'confidence', 'intent'
        """
        # Step 1: Classify intent
        intent = self._classify_intent(query)
        
        # Step 2: Build filters
        filter_dict = {}
        if system_filter:
            filter_dict["system"] = system_filter.value
        if clinical_only:
            filter_dict["clinical_relevance"] = True
        if difficulty_level:
            filter_dict["difficulty_level"] = difficulty_level.value
        
        # Step 3: Retrieve relevant chunks
        # First try with normal threshold
        retrieved_chunks = self.vector_store.search(
            query=query,
            top_k=settings.retrieval_top_k,
            filter_dict=filter_dict if filter_dict else None,
            min_score=settings.min_retrieval_score
        )
        
        # If no results, try with lower threshold (in case knowledge base is sparse)
        if not retrieved_chunks:
            retrieved_chunks = self.vector_store.search(
                query=query,
                top_k=settings.retrieval_top_k,
                filter_dict=filter_dict if filter_dict else None,
                min_score=0.3  # Lower threshold for sparse knowledge bases
            )
        
        # Step 4: Check retrieval confidence - try fallback strategies
        if not retrieved_chunks:
            stats = self.vector_store.get_collection_stats()
            if stats["total_chunks"] == 0:
                # Knowledge base empty - use general knowledge for educational queries
                return self._fallback_general_knowledge(query, intent)
            else:
                # Try broader retrieval for summarize/explain type queries
                query_lower = query.lower()
                broad_queries = [
                    "key points", "main points", "summary", "overview",
                    "neuroanatomy", "anatomy", "key concepts"
                ]
                if any(w in query_lower for w in ["summarize", "summary", "key points", "main points"]):
                    broad_queries = ["key points", "main points", "summary"] + broad_queries
                for bq in broad_queries:
                    retrieved_chunks = self.vector_store.search(
                        query=bq,
                        top_k=settings.retrieval_top_k * 2,
                        filter_dict=None,
                        min_score=0.2
                    )
                    if retrieved_chunks:
                        break
                if not retrieved_chunks:
                    return self._fallback_general_knowledge(query, intent, stats["total_chunks"])
        
        # Calculate average confidence
        avg_confidence = sum(chunk["score"] for chunk in retrieved_chunks) / len(retrieved_chunks)
        
        # Step 5: Generate answer from context
        context = self._format_context(retrieved_chunks)
        
        answer = self.answer_chain.run(
            context=context,
            query=query
        )
        
        # Format sources - include content for frontend display
        sources = [
            {
                "chunk_id": chunk["chunk_id"],
                "structure_name": chunk["metadata"].get("structure_name", "Unknown"),
                "system": chunk["metadata"].get("system", "other"),
                "source": chunk["metadata"].get("source", "Unknown"),
                "score": chunk["score"],
                "preview": chunk["metadata"].get("chunk_text_preview", chunk["content"][:300]) or chunk["content"][:300],
                "content": chunk["content"][:500]
            }
            for chunk in retrieved_chunks
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "confidence": avg_confidence,
            "intent": QueryIntent(intent.strip().lower())
        }
    
    def _classify_intent(self, query: str) -> str:
        """Classify the intent of a user query."""
        try:
            intent = self.intent_chain.run(query=query)
            return intent.strip().lower()
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            return "factual_explanation"  # Default fallback
    
    def _fallback_general_knowledge(
        self,
        query: str,
        intent: str,
        total_chunks: int = 0
    ) -> Dict[str, Any]:
        """Use LLM general knowledge when KB is empty or retrieval fails for summarize/explain queries."""
        fallback_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are NeuraBuddy, an expert neuroanatomy teaching assistant.
The user asked: {query}

{context}

Provide a helpful, accurate, educational response. Use your knowledge of neuroanatomy.
If the knowledge base is empty, encourage them to upload documents and provide a brief, accurate overview of common neuroanatomy topics that relate to their question.
Be concise but informative. Use proper anatomical terminology.
Format with markdown: **bold** for key terms, bullet points (- ) for lists."""),
            ("human", "{query}")
        ])
        fallback_chain = LLMChain(llm=self.llm, prompt=fallback_prompt)
        if total_chunks == 0:
            context = "The user has not uploaded any documents yet."
        else:
            context = f"Retrieval found no direct matches, but the knowledge base has {total_chunks} chunks."
        answer = fallback_chain.run(query=query, context=context)
        return {
            "answer": answer,
            "sources": [],
            "confidence": 0.5,
            "intent": QueryIntent(intent.strip().lower()) if intent else QueryIntent.FACTUAL
        }

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into context string."""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            content = chunk["content"]
            metadata = chunk["metadata"]
            
            context_part = f"[Source {i}]\n"
            context_part += f"Structure: {metadata.get('structure_name', 'N/A')}\n"
            context_part += f"System: {metadata.get('system', 'N/A')}\n"
            context_part += f"Source: {metadata.get('source', 'N/A')}\n"
            context_part += f"Content:\n{content}\n"
            context_part += "---\n"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)

