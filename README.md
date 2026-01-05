<<<<<<< HEAD
# neurabuddy
RAG based chatbot for the brain. An anatomical teaching assistant with pedagogical teaching methods and socratic questioning
=======
# NeuraBuddy Backend

A RAG-based educational chatbot backend for neuroanatomy learning, built with FastAPI, LangChain, and ChromaDB.

## Features

- **RAG Pipeline**: Retrieval-Augmented Generation using OpenAI embeddings and ChromaDB
- **Data Ingestion**: Supports PDF, HTML, and text documents
- **Semantic Chunking**: Structure-aware chunking with rich metadata
- **Pedagogical Logic**: Socratic teaching method with adaptive difficulty
- **Quiz Engine**: MCQ, short-answer, and clinical vignette generation
- **Medical-Grade**: Strictly grounded responses, no hallucinations

## Architecture

```
neurabuddy/
├── app/
│   ├── api/              # FastAPI routes
│   ├── core/             # Configuration and utilities
│   ├── ingestion/        # Document processing pipeline
│   ├── chunking/         # Semantic chunking logic
│   ├── rag/              # RAG chain and retrieval
│   ├── teaching/         # Pedagogical logic
│   ├── quiz/             # Quiz generation and evaluation
│   └── models/           # Pydantic models
├── data/                 # Document storage
├── chroma_db/            # Vector database (gitignored)
└── main.py               # Application entry point
```

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. **Run the server**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `POST /ingest` - Ingest documents into the knowledge base
- `POST /query` - Query the RAG system
- `POST /teach` - Start a Socratic teaching session
- `POST /quiz/start` - Start a quiz
- `POST /quiz/answer` - Submit a quiz answer
- `GET /quiz/feedback` - Get feedback on a quiz answer
- `GET /user/progress` - Get user learning progress

## Data Ingestion

Place your neuroanatomy documents in `data/raw/` and use the `/ingest` endpoint to process them.

Supported formats:
- PDF files
- HTML pages
- Plain text files

## Development

The system is designed to be modular and extensible. Key components:

- **Ingestion Pipeline**: `app/ingestion/`
- **Chunking Logic**: `app/chunking/`
- **RAG Chain**: `app/rag/`
- **Teaching Logic**: `app/teaching/`
- **Quiz Engine**: `app/quiz/`

>>>>>>> 50b435a (Initial commit)
