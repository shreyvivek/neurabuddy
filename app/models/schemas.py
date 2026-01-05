"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class DifficultyLevel(str, Enum):
    """Difficulty levels for content."""
    UNDERGRAD = "undergrad"
    MED = "med"
    ADVANCED = "advanced"


class SystemType(str, Enum):
    """Neuroanatomical systems."""
    LIMBIC = "limbic"
    BRAINSTEM = "brainstem"
    CORTICAL = "cortical"
    CEREBELLAR = "cerebellar"
    SPINAL = "spinal"
    VASCULAR = "vascular"
    CRANIAL_NERVE = "cranial_nerve"
    DEVELOPMENTAL = "developmental"
    OTHER = "other"


class QueryIntent(str, Enum):
    """Query intent classification."""
    FACTUAL = "factual_explanation"
    CLARIFICATION = "concept_clarification"
    QUIZ = "quiz_request"
    FOLLOW_UP = "follow_up_question"
    MISCONCEPTION = "misconception_correction"


# ============ Ingestion Models ============

class IngestionRequest(BaseModel):
    """Request model for document ingestion."""
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    content: Optional[str] = None
    source: str = Field(..., description="Source identifier (e.g., 'Neuroscience Online', 'StatPearls')")
    file_type: Literal["pdf", "html", "text"] = Field(..., description="Document type")


class IngestionResponse(BaseModel):
    """Response model for document ingestion."""
    success: bool
    chunks_created: int
    message: str
    document_id: Optional[str] = None


# ============ Query Models ============

class QueryRequest(BaseModel):
    """Request model for RAG queries."""
    query: str = Field(..., description="User's question")
    user_id: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    system_filter: Optional[SystemType] = None
    clinical_only: bool = False


class QueryResponse(BaseModel):
    """Response model for RAG queries."""
    answer: str
    sources: List[Dict[str, Any]] = Field(..., description="Retrieved chunks with metadata")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Retrieval confidence score")
    intent: QueryIntent


# ============ Teaching Models ============

class TeachingRequest(BaseModel):
    """Request model for Socratic teaching."""
    topic: str = Field(..., description="Topic to teach")
    user_id: str
    difficulty_level: DifficultyLevel = DifficultyLevel.UNDERGRAD
    previous_responses: Optional[List[str]] = Field(default=[], description="User's previous answers")


class TeachingResponse(BaseModel):
    """Response model for Socratic teaching."""
    question: Optional[str] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None
    is_complete: bool = False
    next_step: Optional[str] = None
    concepts_covered: List[str] = []


# ============ Quiz Models ============

class QuizQuestionType(str, Enum):
    """Types of quiz questions."""
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    CLINICAL_VIGNETTE = "clinical_vignette"


class QuizStartRequest(BaseModel):
    """Request model to start a quiz."""
    user_id: str
    topic: Optional[str] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.UNDERGRAD
    system_filter: Optional[SystemType] = None
    num_questions: int = Field(default=5, ge=1, le=20)


class QuizQuestion(BaseModel):
    """Model for a quiz question."""
    question_id: str
    question: str
    question_type: QuizQuestionType
    options: Optional[List[str]] = None  # For MCQ
    correct_answer: str
    structure_tested: str
    difficulty: DifficultyLevel
    learning_objective: str
    source_chunk_id: str


class QuizStartResponse(BaseModel):
    """Response model for quiz start."""
    quiz_id: str
    questions: List[QuizQuestion]
    topic: str
    difficulty_level: DifficultyLevel


class QuizAnswerRequest(BaseModel):
    """Request model for quiz answer submission."""
    quiz_id: str
    question_id: str
    answer: str
    user_id: str


class QuizFeedback(BaseModel):
    """Model for quiz answer feedback."""
    is_correct: bool
    feedback: str
    explanation: str
    correct_answer: str
    related_anatomy: str
    next_question_id: Optional[str] = None


class QuizAnswerResponse(BaseModel):
    """Response model for quiz answer."""
    feedback: QuizFeedback
    score: float = Field(..., ge=0.0, le=1.0)
    total_questions: int
    questions_answered: int


# ============ Progress Models ============

class UserProgress(BaseModel):
    """Model for user learning progress."""
    user_id: str
    topics_studied: List[str]
    quiz_scores: Dict[str, float]  # topic -> average score
    difficulty_progression: Dict[str, DifficultyLevel]  # topic -> current difficulty
    misconceptions_identified: List[str]
    strengths: List[str]
    areas_for_improvement: List[str]
    last_active: datetime


class ProgressResponse(BaseModel):
    """Response model for user progress."""
    progress: UserProgress

