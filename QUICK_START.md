# NeuraBuddy Quick Start Guide

## The Issue: Empty Knowledge Base

You're seeing "I don't have enough information" because the knowledge base is empty. You need to upload documents first!

## How to Add Documents

### Option 1: Using the Web UI (Recommended)

1. **Start the backend:**
   ```bash
   python main.py
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Upload documents:**
   - Go to http://localhost:3000
   - Click on the "Upload" tab in the navigation
   - Drag and drop or select PDF, HTML, or TXT files
   - Enter a source name (e.g., "Neuroscience Online", "StatPearls")
   - Click "Upload Document"

### Option 2: Using the API

```bash
# Upload a file via API
curl -X POST "http://localhost:8000/api/v1/ingest/file" \
  -F "file=@path/to/your/document.pdf" \
  -F "source=Neuroscience Online"
```

### Option 3: Using the Python Script

```bash
# Ingest a single file
python scripts/ingest_documents.py path/to/document.pdf --source "My Source"

# Ingest all files in a directory
python scripts/ingest_documents.py data/raw/ --directory --source "Batch Import"
```

## What Documents to Upload

Good sources for neuroanatomy content:
- **PDF textbooks** on neuroanatomy
- **HTML pages** from educational sites (e.g., Neuroscience Online)
- **Text files** with neuroanatomy content
- **Clinical notes** or study guides

## After Uploading

Once you've uploaded documents:
1. Go back to the "Ask Questions" tab
2. Try your question again: "Describe the cranial nerves"
3. The system should now find relevant information!

## Troubleshooting

### Still getting "no information" after uploading?

1. **Check if documents were ingested:**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
   Look for `total_chunks` - it should be > 0

2. **Try a more general question:**
   - Instead of "Describe cranial nerve VII", try "cranial nerves"
   - Instead of specific structures, try broader topics

3. **Check the minimum score threshold:**
   - The default is 0.7 (70% similarity)
   - If your documents are very different from the query, lower scores might be needed
   - The system now automatically tries a lower threshold (0.3) if no results are found

### Documents not uploading?

1. **Check file format:** Only PDF, HTML, and TXT are supported
2. **Check file size:** Very large files might timeout
3. **Check backend logs:** Look for error messages
4. **Check OpenAI API key:** Make sure it's set in your `.env` file

## Example Queries to Try

Once you have documents uploaded:
- "What are the cranial nerves?"
- "Explain the blood supply to the brain"
- "Describe the hippocampus"
- "What is the function of the cerebellum?"
- "Explain the limbic system"

## Need Help?

- Check the main README.md for detailed setup
- Review the API documentation at http://localhost:8000/docs
- Check backend logs for error messages
