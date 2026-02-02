"""FastAPI route handlers for NeuraBuddy API."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
import logging

from app.models.schemas import (
    IngestionRequest, IngestionResponse,
    QueryRequest, QueryResponse,
    TeachingRequest, TeachingResponse,
    QuizStartRequest, QuizStartResponse,
    QuizAnswerRequest, QuizAnswerResponse,
    ProgressResponse, UserProgress, DifficultyLevel, SystemType,
    FlashCardRequest, FlashCardResponse,
    FlashCardAnswerRequest, FlashCardAnswerResponse,
    FlashCardSessionComplete, FlashCardAnalysisResponse,
    ClinicalCaseRequest, ClinicalCaseResponse,
    ClinicalSessionStartRequest, ClinicalSessionStartResponse,
    ClinicalSessionInteractionRequest, ClinicalSessionInteractionResponse,
    StudyNotesRequest, StudyNotesResponse
)
from app.ingestion.document_loader import DocumentLoader
from app.chunking.semantic_chunker import SemanticChunker
from app.rag.vector_store import VectorStore
from app.rag.retrieval_chain import RetrievalChain
from app.teaching.socratic_tutor import SocraticTutor
from app.quiz.quiz_engine import QuizEngine
from app.study.study_engine import StudyEngine
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize components (singleton pattern)
vector_store = VectorStore()
retrieval_chain = RetrievalChain(vector_store)
socratic_tutor = SocraticTutor(vector_store)
quiz_engine = QuizEngine(vector_store)
study_engine = StudyEngine(vector_store)

router = APIRouter()


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_document(request: IngestionRequest):
    """
    Ingest a document into the knowledge base.
    
    Supports PDF, HTML, and text files.
    """
    try:
        # Load document
        loader = DocumentLoader()
        document = loader.load_document(
            file_path=request.file_path,
            file_url=request.file_url,
            content=request.content,
            file_type=request.file_type
        )
        
        # Chunk document
        chunker = SemanticChunker()
        chunks = chunker.chunk_document(
            content=document["content"],
            source_metadata=document["metadata"],
            source=request.source
        )
        
        # Add to vector store
        chunk_ids = vector_store.add_chunks(chunks)
        
        return IngestionResponse(
            success=True,
            chunks_created=len(chunk_ids),
            message=f"Successfully ingested document. Created {len(chunk_ids)} chunks.",
            document_id=chunk_ids[0] if chunk_ids else None
        )
    except Exception as e:
        logger.error(f"Error ingesting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ingesting document: {str(e)}")


@router.post("/ingest/file", response_model=IngestionResponse)
async def ingest_file(
    file: UploadFile = File(...),
    source: str = "uploaded_file"
):
    """
    Ingest a document from uploaded file.
    """
    try:
        # Determine file type
        file_type = "text"
        if file.filename.lower().endswith(".pdf"):
            file_type = "pdf"
        elif file.filename.lower().endswith((".pptx", ".ppt")):
            file_type = "pptx"
        elif file.filename.lower().endswith((".html", ".htm")):
            file_type = "html"
        
        # Save file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Load and process
            loader = DocumentLoader()
            document = loader.load_document(file_path=tmp_path, file_type=file_type)
            
            chunker = SemanticChunker()
            chunks = chunker.chunk_document(
                content=document["content"],
                source_metadata=document["metadata"],
                source=source
            )
            
            chunk_ids = vector_store.add_chunks(chunks)
            
            return IngestionResponse(
                success=True,
                chunks_created=len(chunk_ids),
                message=f"Successfully ingested {file.filename}. Created {len(chunk_ids)} chunks.",
                document_id=chunk_ids[0] if chunk_ids else None
            )
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"Error ingesting file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ingesting file: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query the RAG system for neuroanatomy information.
    """
    try:
        result = retrieval_chain.process_query(
            query=request.query,
            user_id=request.user_id,
            difficulty_level=request.difficulty_level,
            system_filter=request.system_filter,
            clinical_only=request.clinical_only
        )
        
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/query/with-files", response_model=QueryResponse)
async def query_with_files(
    query: str = Form(...),
    user_id: Optional[str] = Form(None),
    difficulty_level: Optional[str] = Form(None),
    system_filter: Optional[str] = Form(None),
    clinical_only: bool = Form(False),
    files: List[UploadFile] = File(default=[])
):
    """
    Ingest uploaded files (PDF, PPTX, etc.) then answer the query.
    """
    import tempfile
    import os

    try:
        if files:
            for file in files:
                file_type = "text"
                fn = file.filename.lower()
                if fn.endswith(".pdf"):
                    file_type = "pdf"
                elif fn.endswith((".pptx", ".ppt")):
                    file_type = "pptx"
                elif fn.endswith((".html", ".htm")):
                    file_type = "html"
                content = await file.read()
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                try:
                    loader = DocumentLoader()
                    doc = loader.load_document(file_path=tmp_path, file_type=file_type)
                    chunker = SemanticChunker()
                    chunks = chunker.chunk_document(
                        content=doc["content"],
                        source_metadata=doc["metadata"],
                        source=file.filename
                    )
                    vector_store.add_chunks(chunks)
                finally:
                    os.unlink(tmp_path)

        diff_level = DifficultyLevel(difficulty_level) if difficulty_level else None
        sys_filter = SystemType(system_filter) if system_filter else None
        result = retrieval_chain.process_query(
            query=query,
            user_id=user_id,
            difficulty_level=diff_level,
            system_filter=sys_filter,
            clinical_only=clinical_only
        )
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Error in query with files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teach", response_model=TeachingResponse)
async def teach(request: TeachingRequest):
    """
    Start or continue a Socratic teaching session.
    """
    try:
        result = socratic_tutor.teach(
            topic=request.topic,
            user_id=request.user_id,
            difficulty_level=request.difficulty_level,
            previous_responses=request.previous_responses or []
        )
        
        return TeachingResponse(**result)
    except Exception as e:
        logger.error(f"Error in teaching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in teaching: {str(e)}")


@router.post("/quiz/start", response_model=QuizStartResponse)
async def start_quiz(request: QuizStartRequest):
    """
    Start a new quiz session.
    """
    try:
        result = quiz_engine.generate_quiz(
            user_id=request.user_id,
            topic=request.topic,
            difficulty_level=request.difficulty_level,
            system_filter=request.system_filter,
            num_questions=request.num_questions
        )
        
        return QuizStartResponse(**result)
    except Exception as e:
        logger.error(f"Error starting quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting quiz: {str(e)}")


@router.post("/quiz/answer", response_model=QuizAnswerResponse)
async def submit_answer(request: QuizAnswerRequest):
    """
    Submit an answer to a quiz question.
    """
    try:
        result = quiz_engine.evaluate_answer(
            quiz_id=request.quiz_id,
            question_id=request.question_id,
            answer=request.answer,
            user_id=request.user_id
        )
        
        return QuizAnswerResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error evaluating answer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error evaluating answer: {str(e)}")


@router.get("/quiz/feedback/{quiz_id}/{question_id}")
async def get_feedback(quiz_id: str, question_id: str, user_id: str):
    """
    Get feedback for a specific quiz question.
    """
    try:
        if quiz_id not in quiz_engine.active_quizzes:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        quiz = quiz_engine.active_quizzes[quiz_id]
        if quiz["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if question_id not in quiz["answers"]:
            raise HTTPException(status_code=404, detail="Answer not found")
        
        return quiz["answers"][question_id]["feedback"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting feedback: {str(e)}")


@router.get("/user/progress", response_model=ProgressResponse)
async def get_progress(user_id: str):
    """
    Get user learning progress.
    
    Note: This is a simplified implementation. In production, use a database.
    """
    try:
        # Simplified progress tracking (in production, use a database)
        from datetime import datetime
        
        # Get quiz data for this user
        user_quizzes = [
            q for q in quiz_engine.active_quizzes.values()
            if q["user_id"] == user_id
        ]
        
        # Calculate progress
        topics_studied = list(set(q["topic"] for q in user_quizzes))
        quiz_scores = {}
        difficulty_progression = {}
        
        for quiz in user_quizzes:
            topic = quiz["topic"]
            if topic not in quiz_scores:
                quiz_scores[topic] = []
            
            # Calculate average score for this quiz
            if quiz["answers"]:
                correct = sum(1 for a in quiz["answers"].values() if a["is_correct"])
                total = len(quiz["questions"])
                if total > 0:
                    quiz_scores[topic].append(correct / total)
            
            difficulty_progression[topic] = quiz["difficulty_level"]
        
        # Average scores per topic
        avg_scores = {
            topic: sum(scores) / len(scores) if scores else 0.0
            for topic, scores in quiz_scores.items()
        }
        
        progress = UserProgress(
            user_id=user_id,
            topics_studied=topics_studied,
            quiz_scores=avg_scores,
            difficulty_progression={k: v for k, v in difficulty_progression.items()},
            misconceptions_identified=[],  # TODO: Implement misconception tracking
            strengths=[],  # TODO: Implement strength analysis
            areas_for_improvement=[],  # TODO: Implement improvement analysis
            last_active=datetime.now()
        )
        
        return ProgressResponse(progress=progress)
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting progress: {str(e)}")


@router.post("/study/flash-cards", response_model=FlashCardResponse)
async def generate_flash_cards(request: FlashCardRequest):
    """Generate flash cards from the knowledge base."""
    try:
        result = study_engine.generate_flash_cards(
            topic=request.topic,
            num_cards=request.num_cards,
            difficulty_level=request.difficulty_level,
            system_filter=request.system_filter
        )
        return FlashCardResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating flash cards: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/study/flash-cards/evaluate", response_model=FlashCardAnswerResponse)
async def evaluate_flash_card_answer(request: FlashCardAnswerRequest):
    """Evaluate user's answer to a flash card question."""
    try:
        result = study_engine.evaluate_flash_card_answer(
            user_answer=request.user_answer,
            correct_answer=request.correct_answer,
            question=request.question
        )
        return FlashCardAnswerResponse(**result)
    except Exception as e:
        logger.error(f"Error evaluating flash card answer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/study/flash-cards/analyze", response_model=FlashCardAnalysisResponse)
async def analyze_flash_card_session(request: FlashCardSessionComplete):
    """Analyze completed flash card session and provide recommendations."""
    try:
        result = study_engine.analyze_flash_card_session(
            topic=request.topic,
            total_score=request.total_score,
            max_score=request.max_score,
            card_results=request.card_results
        )
        return FlashCardAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"Error analyzing flash card session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/study/clinical-case", response_model=ClinicalCaseResponse)
async def generate_clinical_case(request: ClinicalCaseRequest):
    """Generate a clinical case vignette (legacy endpoint)."""
    try:
        result = study_engine.generate_clinical_case(
            topic=request.topic,
            difficulty_level=request.difficulty_level,
            system_filter=request.system_filter
        )
        return ClinicalCaseResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating clinical case: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/study/clinical-session/start", response_model=ClinicalSessionStartResponse)
async def start_clinical_session(request: ClinicalSessionStartRequest):
    """Start an interactive clinical case simulation."""
    try:
        result = study_engine.start_clinical_session(
            topic=request.topic,
            difficulty_level=request.difficulty_level,
            system_filter=request.system_filter
        )
        return ClinicalSessionStartResponse(**result)
    except Exception as e:
        logger.error(f"Error starting clinical session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/study/clinical-session/interact", response_model=ClinicalSessionInteractionResponse)
async def interact_clinical_session(request: ClinicalSessionInteractionRequest):
    """Handle interaction in clinical session."""
    try:
        result = study_engine.interact_clinical_session(
            session_id=request.session_id,
            user_message=request.user_message,
            request_hint=request.request_hint
        )
        return ClinicalSessionInteractionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in clinical session interaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/study/notes", response_model=StudyNotesResponse)
async def generate_study_notes(request: StudyNotesRequest):
    """Generate study notes from the knowledge base."""
    try:
        result = study_engine.generate_study_notes(
            topic=request.topic,
            difficulty_level=request.difficulty_level,
            system_filter=request.system_filter,
            include_summary=request.include_summary
        )
        return StudyNotesResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating study notes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    stats = vector_store.get_collection_stats()
    return {
        "status": "healthy",
        "vector_store": stats
    }

