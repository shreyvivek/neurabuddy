"""Quiz generation and evaluation engine."""

import uuid
from typing import List, Dict, Any, Optional
import logging

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

from app.core.config import settings
from app.rag.vector_store import VectorStore
from app.models.schemas import (
    QuizQuestionType, DifficultyLevel, SystemType,
    QuizQuestion, QuizFeedback
)

logger = logging.getLogger(__name__)


class QuizEngine:
    """Generates and evaluates quiz questions from knowledge base."""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.5,
            openai_api_key=settings.openai_api_key
        )
        
        # Active quizzes storage (in production, use a database)
        self.active_quizzes: Dict[str, Dict[str, Any]] = {}
        
        # Question generation prompt
        self.question_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a medical education expert creating quiz questions for neuroanatomy.

Generate a {question_type} question based on the following context.

Requirements:
- Test understanding of the anatomical structure, pathway, or clinical correlation
- Match the difficulty level: {difficulty}
- For MCQ: Provide 4 options, with only ONE correct answer
- For short answer: Provide a clear, concise expected answer
- For clinical vignette: Present a patient scenario and ask about the underlying anatomy

Context:
{context}

Generate a question in JSON format:
{{
    "question": "the question text",
    "question_type": "{question_type}",
    "options": ["option1", "option2", "option3", "option4"] (only for MCQ),
    "correct_answer": "the correct answer",
    "structure_tested": "anatomical structure being tested",
    "learning_objective": "what the student should learn",
    "explanation": "why the answer is correct"
}}"""),
            ("human", "Generate a {question_type} question about: {topic}")
        ])
        
        self.question_chain = LLMChain(llm=self.llm, prompt=self.question_prompt)
        
        # Feedback generation prompt
        self.feedback_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are providing feedback on a quiz answer.

Question: {question}
Correct Answer: {correct_answer}
Student Answer: {student_answer}
Explanation: {explanation}
Structure Tested: {structure_tested}

Provide feedback that:
1. Confirms if the answer is correct or explains why it's wrong
2. Links back to the core anatomy
3. Explains the clinical relevance if applicable
4. Encourages further learning

Format as JSON:
{{
    "is_correct": true/false,
    "feedback": "overall feedback message",
    "explanation": "detailed explanation",
    "related_anatomy": "key anatomical points to remember"
}}"""),
            ("human", "Provide feedback on this answer.")
        ])
        
        self.feedback_chain = LLMChain(llm=self.llm, prompt=self.feedback_prompt)
    
    def generate_quiz(
        self,
        user_id: str,
        topic: Optional[str] = None,
        difficulty_level: DifficultyLevel = DifficultyLevel.UNDERGRAD,
        system_filter: Optional[SystemType] = None,
        num_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a quiz from the knowledge base.
        
        Returns:
            Quiz with questions and metadata
        """
        quiz_id = str(uuid.uuid4())
        
        # Retrieve relevant chunks
        query = topic or "neuroanatomy"
        filter_dict = {"difficulty_level": difficulty_level.value}
        if system_filter:
            filter_dict["system"] = system_filter.value
        
        retrieved_chunks = self.vector_store.search(
            query=query,
            top_k=num_questions * 2,  # Get more chunks to ensure variety
            filter_dict=filter_dict
        )
        
        if not retrieved_chunks:
            raise ValueError("No relevant content found for quiz generation")
        
        # Generate questions
        questions = []
        used_chunks = set()
        
        for i in range(num_questions):
            # Select a chunk that hasn't been used
            available_chunks = [c for c in retrieved_chunks if c["chunk_id"] not in used_chunks]
            if not available_chunks:
                break
            
            chunk = available_chunks[i % len(available_chunks)]
            used_chunks.add(chunk["chunk_id"])
            
            # Determine question type (rotate through types)
            question_types = [QuizQuestionType.MCQ, QuizQuestionType.SHORT_ANSWER, QuizQuestionType.CLINICAL_VIGNETTE]
            question_type = question_types[i % len(question_types)]
            
            # Generate question
            question = self._generate_question(
                chunk=chunk,
                question_type=question_type,
                difficulty=difficulty_level,
                topic=topic or chunk["metadata"].get("structure_name", "neuroanatomy")
            )
            
            if question:
                questions.append(question)
        
        if not questions:
            raise ValueError("Failed to generate any questions")
        
        # Store quiz
        self.active_quizzes[quiz_id] = {
            "user_id": user_id,
            "questions": {q.question_id: q for q in questions},
            "answers": {},
            "topic": topic or "General Neuroanatomy",
            "difficulty_level": difficulty_level,
            "started_at": None
        }
        
        return {
            "quiz_id": quiz_id,
            "questions": questions,
            "topic": topic or "General Neuroanatomy",
            "difficulty_level": difficulty_level
        }
    
    def _generate_question(
        self,
        chunk: Dict[str, Any],
        question_type: QuizQuestionType,
        difficulty: DifficultyLevel,
        topic: str
    ) -> Optional[QuizQuestion]:
        """Generate a single question from a chunk."""
        try:
            response_text = self.question_chain.run(
                context=chunk["content"][:1000],  # Limit context length
                topic=topic,
                question_type=question_type.value,
                difficulty=difficulty.value
            )
            
            # Parse response
            question_data = self._parse_json_response(response_text)
            
            if not question_data:
                return None
            
            question_id = str(uuid.uuid4())
            
            # Store explanation in metadata for feedback generation
            explanation = question_data.get("explanation", "")
            
            question_obj = QuizQuestion(
                question_id=question_id,
                question=question_data.get("question", ""),
                question_type=question_type,
                options=question_data.get("options"),
                correct_answer=question_data.get("correct_answer", ""),
                structure_tested=question_data.get("structure_tested", chunk["metadata"].get("structure_name", "Unknown")),
                difficulty=difficulty,
                learning_objective=question_data.get("learning_objective", "Understand neuroanatomy"),
                source_chunk_id=chunk["chunk_id"]
            )
            
            # Store explanation as attribute for later use
            question_obj.explanation = explanation
            
            return question_obj
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}")
            return None
    
    def evaluate_answer(
        self,
        quiz_id: str,
        question_id: str,
        answer: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Evaluate a quiz answer and provide feedback."""
        if quiz_id not in self.active_quizzes:
            raise ValueError(f"Quiz {quiz_id} not found")
        
        quiz = self.active_quizzes[quiz_id]
        
        if quiz["user_id"] != user_id:
            raise ValueError("User does not have access to this quiz")
        
        if question_id not in quiz["questions"]:
            raise ValueError(f"Question {question_id} not found in quiz")
        
        question = quiz["questions"][question_id]
        
        # Generate feedback
        feedback = self._generate_feedback(question, answer)
        
        # Store answer
        quiz["answers"][question_id] = {
            "answer": answer,
            "feedback": feedback,
            "is_correct": feedback.is_correct
        }
        
        # Calculate score
        total_questions = len(quiz["questions"])
        correct_answers = sum(1 for a in quiz["answers"].values() if a["is_correct"])
        score = correct_answers / total_questions if total_questions > 0 else 0.0
        
        return {
            "feedback": feedback,
            "score": score,
            "total_questions": total_questions,
            "questions_answered": len(quiz["answers"])
        }
    
    def _generate_feedback(
        self,
        question: QuizQuestion,
        student_answer: str
    ) -> QuizFeedback:
        """Generate feedback for a student answer."""
        try:
            explanation = getattr(question, "explanation", "")
            if not explanation:
                explanation = f"The correct answer is {question.correct_answer} because it accurately describes the neuroanatomical structure or pathway."
            
            response_text = self.feedback_chain.run(
                question=question.question,
                correct_answer=question.correct_answer,
                student_answer=student_answer,
                explanation=explanation,
                structure_tested=question.structure_tested
            )
            
            feedback_data = self._parse_json_response(response_text)
            
            if not feedback_data:
                # Fallback feedback
                is_correct = student_answer.lower().strip() == question.correct_answer.lower().strip()
                return QuizFeedback(
                    is_correct=is_correct,
                    feedback="Correct!" if is_correct else "Incorrect. Try again.",
                    explanation=f"The correct answer is: {question.correct_answer}",
                    correct_answer=question.correct_answer,
                    related_anatomy=question.structure_tested
                )
            
            return QuizFeedback(
                is_correct=feedback_data.get("is_correct", False),
                feedback=feedback_data.get("feedback", ""),
                explanation=feedback_data.get("explanation", ""),
                correct_answer=question.correct_answer,
                related_anatomy=feedback_data.get("related_anatomy", question.structure_tested)
            )
        except Exception as e:
            logger.error(f"Error generating feedback: {str(e)}")
            # Fallback
            is_correct = student_answer.lower().strip() == question.correct_answer.lower().strip()
            return QuizFeedback(
                is_correct=is_correct,
                feedback="Correct!" if is_correct else "Incorrect.",
                explanation=f"The correct answer is: {question.correct_answer}",
                correct_answer=question.correct_answer,
                related_anatomy=question.structure_tested
            )
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response."""
        import json
        import re
        
        # Try to find JSON in response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        return None

