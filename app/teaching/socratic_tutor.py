"""Socratic teaching method implementation with adaptive difficulty."""

from typing import List, Dict, Any, Optional
import logging

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from app.core.config import settings
from app.rag.vector_store import VectorStore
from app.models.schemas import DifficultyLevel

logger = logging.getLogger(__name__)


class SocraticTutor:
    """Implements Socratic teaching method with progressive revelation."""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,  # Slightly higher for more engaging questions
            openai_api_key=settings.openai_api_key
        )
        
        # Teaching prompt template
        self.teaching_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are NeuraBuddy, a Socratic tutor for neuroanatomy.

Your teaching approach:
1. Ask guiding questions that help students discover answers themselves
2. Reveal information progressively (don't give everything at once)
3. Connect: anatomy → pathway → clinical outcome
4. Encourage reasoning about structure → function → deficit

If the student has answered previous questions, use their responses to guide your next question.
If they're struggling, provide a hint but still ask a question.
If they've demonstrated understanding, move to the next concept or increase complexity.

Context about the topic:
{context}

Previous student responses: {previous_responses}

Current teaching stage: {stage}

Generate either:
- A guiding question (if student hasn't fully understood yet)
- An explanation with a follow-up question (if student is ready for the next step)
- A summary and next topic (if current topic is complete)

Format your response as JSON:
{{
    "question": "guiding question or null",
    "explanation": "explanation if ready, or null",
    "hint": "hint if student struggling, or null",
    "is_complete": false,
    "next_step": "what to explore next",
    "concepts_covered": ["list", "of", "concepts"]
}}"""),
            ("human", "Topic: {topic}\nDifficulty: {difficulty}")
        ])
        
        self.teaching_chain = LLMChain(llm=self.llm, prompt=self.teaching_prompt)
    
    def teach(
        self,
        topic: str,
        user_id: str,
        difficulty_level: DifficultyLevel,
        previous_responses: List[str] = None
    ) -> Dict[str, Any]:
        """
        Conduct a Socratic teaching session.
        
        Args:
            topic: Topic to teach
            user_id: User identifier
            difficulty_level: Current difficulty level
            previous_responses: List of user's previous answers
        
        Returns:
            Teaching response with question, explanation, hints, etc.
        """
        previous_responses = previous_responses or []
        
        # Retrieve relevant context
        retrieved_chunks = self.vector_store.search(
            query=topic,
            top_k=3,
            filter_dict={"difficulty_level": difficulty_level.value} if difficulty_level else None
        )
        
        if not retrieved_chunks:
            return {
                "question": None,
                "explanation": "I don't have enough information about this topic in my knowledge base.",
                "hint": None,
                "is_complete": True,
                "next_step": "Try asking about a different neuroanatomy topic.",
                "concepts_covered": []
            }
        
        # Determine teaching stage
        stage = self._determine_stage(len(previous_responses), retrieved_chunks)
        
        # Format context
        context = self._format_context(retrieved_chunks)
        
        # Generate teaching response
        try:
            response_text = self.teaching_chain.run(
                context=context,
                topic=topic,
                difficulty=difficulty_level.value,
                previous_responses="\n".join([f"- {r}" for r in previous_responses]) if previous_responses else "None",
                stage=stage
            )
            
            # Parse JSON response (LLM should return JSON)
            import json
            # Try to extract JSON from response
            response = self._parse_llm_response(response_text)
            
            return response
        except Exception as e:
            logger.error(f"Error in teaching: {str(e)}")
            # Fallback response
            return {
                "question": f"What do you know about {topic}?",
                "explanation": None,
                "hint": None,
                "is_complete": False,
                "next_step": "Explore the anatomical structures involved",
                "concepts_covered": [topic]
            }
    
    def _determine_stage(self, num_responses: int, chunks: List[Dict[str, Any]]) -> str:
        """Determine the current teaching stage."""
        if num_responses == 0:
            return "introduction"
        elif num_responses < 2:
            return "exploration"
        elif num_responses < 4:
            return "deepening"
        else:
            return "synthesis"
    
    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format chunks for teaching context."""
        context_parts = []
        for chunk in chunks:
            context_parts.append(f"Structure: {chunk['metadata'].get('structure_name', 'N/A')}")
            context_parts.append(f"Content: {chunk['content'][:500]}...")
            context_parts.append("---")
        return "\n".join(context_parts)
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response, extracting JSON if present."""
        import json
        import re
        
        # Try to find JSON in the response
        json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: return structured response
        return {
            "question": response_text.split("\n")[0] if response_text else None,
            "explanation": None,
            "hint": None,
            "is_complete": False,
            "next_step": "Continue exploring",
            "concepts_covered": []
        }

