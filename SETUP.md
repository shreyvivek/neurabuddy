# NeuraBuddy Setup Guide

## Prerequisites

- Python 3.9 or higher
- OpenAI API key
- 8GB+ RAM recommended for vector operations

## Installation

1. **Create a virtual environment** (recommended):
```bash
cd neurabuddy
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Running the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

## Ingesting Documents

### Using the API

```bash
# Ingest a file via API
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "data/raw/neuroanatomy.pdf",
    "source": "Neuroscience Online",
    "file_type": "pdf"
  }'
```

### Using the Script

```bash
# Ingest a single file
python scripts/ingest_documents.py data/raw/document.pdf --source "StatPearls"

# Ingest all files in a directory
python scripts/ingest_documents.py data/raw/ --directory --source "Batch Import"
```

## Testing the API

### Query Endpoint
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the function of the hippocampus?",
    "difficulty_level": "undergrad"
  }'
```

### Teaching Endpoint
```bash
curl -X POST "http://localhost:8000/api/v1/teach" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "cranial nerve anatomy",
    "user_id": "user123",
    "difficulty_level": "med"
  }'
```

### Quiz Endpoint
```bash
# Start a quiz
curl -X POST "http://localhost:8000/api/v1/quiz/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "topic": "brainstem",
    "difficulty_level": "undergrad",
    "num_questions": 5
  }'
```

## Project Structure

```
neurabuddy/
├── app/
│   ├── api/              # FastAPI routes
│   ├── core/             # Configuration
│   ├── ingestion/        # Document processing
│   ├── chunking/         # Semantic chunking
│   ├── rag/              # RAG pipeline
│   ├── teaching/         # Pedagogical logic
│   ├── quiz/             # Quiz engine
│   └── models/           # Pydantic schemas
├── data/
│   ├── raw/              # Place documents here
│   └── processed/        # Processed documents
├── scripts/              # Utility scripts
├── chroma_db/            # Vector database (auto-created)
└── main.py               # Application entry point
```

## Data Sources

Recommended authoritative sources:
- Neuroscience Online (UTMB)
- StatPearls Neuroanatomy articles
- Functional Neuroanatomy modules
- NIH Brain Basics
- Open-access atlases

Place PDF, HTML, or text files in `data/raw/` before ingestion.

## Troubleshooting

### Import Errors
If you see import errors, ensure:
1. Virtual environment is activated
2. All dependencies are installed: `pip install -r requirements.txt`

### ChromaDB Issues
If ChromaDB fails to initialize:
1. Check write permissions in the project directory
2. Delete `chroma_db/` folder and restart (will recreate)

### OpenAI API Errors
1. Verify your API key in `.env`
2. Check API quota and billing
3. Ensure you have access to `gpt-4-turbo-preview` and `text-embedding-3-large`

## Next Steps

1. Ingest your neuroanatomy documents
2. Test queries to verify knowledge base
3. Customize prompts in `app/rag/retrieval_chain.py` and `app/teaching/socratic_tutor.py`
4. Adjust chunking parameters in `app/core/config.py`
5. Deploy to production (consider using pgvector for cloud deployment)

