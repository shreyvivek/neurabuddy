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

Context:
{context}

User Query: {query}

Provide a clear, accurate, and educational response based ONLY on the context above."""),
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
        retrieved_chunks = self.vector_store.search(
            query=query,
            top_k=settings.retrieval_top_k,
            filter_dict=filter_dict if filter_dict else None,
            min_score=settings.min_retrieval_score
        )
        
        # Step 4: Check retrieval confidence
        if not retrieved_chunks:
            return {
                "answer": "I don't have enough information in my knowledge base to answer this question accurately. Please try rephrasing or asking about a different topic.",
                "sources": [],
                "confidence": 0.0,
                "intent": intent
            }
        
        # Calculate average confidence
        avg_confidence = sum(chunk["score"] for chunk in retrieved_chunks) / len(retrieved_chunks)
        
        # Step 5: Generate answer from context
        context = self._format_context(retrieved_chunks)
        
        answer = self.answer_chain.run(
            context=context,
            query=query
        )
        
        # Format sources
        sources = [
            {
                "chunk_id": chunk["chunk_id"],
                "structure_name": chunk["metadata"].get("structure_name", "Unknown"),
                "system": chunk["metadata"].get("system", "other"),
                "source": chunk["metadata"].get("source", "Unknown"),
                "score": chunk["score"],
                "preview": chunk["metadata"].get("chunk_text_preview", "")[:150]
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

