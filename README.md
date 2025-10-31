# Tender Document Chatbot

A web application that allows users to upload tender documents (PDF, Word, Excel) and chat with them using AI. Built with FastAPI backend, React frontend, and powered by Llama 3.1 8B via Ollama with RAG (Retrieval Augmented Generation).

## Features

- 📄 **Multi-format Support**: Upload PDF, Word (.docx), and Excel (.xlsx, .xls) files
- 💬 **Intelligent Chat**: Ask questions about your documents using natural language
- 🔍 **Multi-document Search**: Chat with multiple documents simultaneously
- 📊 **Source Citations**: See which parts of documents were used to generate answers
- ⚡ **Async Processing**: Documents are processed in the background for better UX
- 🎯 **Semantic Search**: Uses bge-m3 embeddings for accurate information retrieval

## Architecture

- **Backend**: FastAPI with Python
- **Frontend**: React with Vite
- **LLM**: Llama 3.1 8B (4-bit quantized) via Ollama
- **Embeddings**: bge-m3 model via sentence-transformers
- **Vector Database**: Qdrant for semantic search
- **Document Processing**: PyPDF2, python-docx, openpyxl

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.9+**
2. **Node.js 18+** and npm
3. **Ollama** - [Install from ollama.ai](https://ollama.ai)
4. **Qdrant** - Can run via Docker or install locally

## Setup Instructions

### 1. Install Ollama and Pull the Model

```bash
# Install Ollama from https://ollama.ai

# Pull the Llama 3.1 8B model (4-bit quantized)
ollama pull llama3.1:8b-instruct-q4_0

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### 2. Setup Qdrant Vector Database

**Option A: Using Docker (Recommended)**
```bash
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

**Option B: Install Locally**
Follow instructions at [Qdrant Installation](https://qdrant.tech/documentation/quick-start/)

### 3. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Or on Linux/Mac
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b-instruct-q4_0
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=tender_documents
EMBEDDING_MODEL=BAAI/bge-m3
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
MAX_FILE_SIZE_MB=100
UPLOAD_DIR=uploads

# Edit .env file if needed (default values should work for local setup)
```

### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## Running the Application

### Start Backend

```bash
# Make sure you're in the backend directory with venv activated
cd backend
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Run the FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Start Frontend

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. **Upload Documents**
   - Click or drag-and-drop PDF, Word, or Excel files
   - Wait for processing to complete (status will show "Ready")

2. **Select Documents**
   - Check the boxes next to documents you want to chat with
   - Leave all unchecked to search across all documents

3. **Ask Questions**
   - Type your question in the chat input
   - Get AI-generated answers with source citations
   - Click on "Sources" to see relevant document excerpts



## API Endpoints

### Documents
- `POST /api/documents/upload` - Upload a document
- `GET /api/documents` - List all documents
- `GET /api/documents/{doc_id}` - Get document details
- `DELETE /api/documents/{doc_id}` - Delete a document

### Chat
- `POST /api/chat` - Send a chat message
  ```json
  {
    "message": "What is the project scope?",
    "document_ids": ["uuid1", "uuid2"],
    "top_k": 5
  }
  ```

### Health
- `GET /api/health` - Check system health

## Project Structure

```
AI_tender/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Configuration
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models
│   │   ├── services/
│   │   │   ├── document_processor.py
│   │   │   ├── embeddings.py
│   │   │   ├── vector_store.py
│   │   │   ├── llm_service.py
│   │   │   └── rag_service.py
│   │   └── routers/
│   │       ├── documents.py
│   │       └── chat.py
│   ├── uploads/                 # Uploaded files
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DocumentUpload.jsx
│   │   │   ├── DocumentList.jsx
│   │   │   └── ChatInterface.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## Troubleshooting

### Ollama Connection Error
- Ensure Ollama is running: `ollama serve`
- Verify the model is pulled: `ollama list`
- Check connection: `curl http://localhost:11434/api/tags`

### Qdrant Connection Error
- Ensure Qdrant is running on port 6333
- Check Docker container: `docker ps`
- Test connection: `curl http://localhost:6333/health`

### Embedding Model Loading Issues
- First run will download the bge-m3 model (~2GB)
- Ensure sufficient disk space and internet connection
- Check Python logs for detailed error messages

### Large File Processing
- Increase `MAX_FILE_SIZE_MB` in `.env` if needed
- Processing time depends on file size and system resources
- Monitor backend logs for progress

## Performance Tips

1. **First Time Setup**: The embedding model download may take time
2. **Document Processing**: Large documents (>100 pages) may take several minutes
3. **Memory**: Ensure at least 8GB RAM for optimal performance
4. **GPU**: Ollama will use GPU if available for faster inference

## Security Notes

This is a single-user application designed for local use. For production deployment:
- Add authentication and authorization
- Implement rate limiting
- Add input validation and sanitization
- Use HTTPS
- Secure file storage
- Add user isolation

## License

MIT License

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at `http://localhost:8000/docs`
3. Check backend logs for detailed error messages

## Future Enhancements

- Multi-user support with authentication
- Conversation history persistence
- Document comparison features
- Advanced search filters
- Export chat history
- Support for more file formats
- Cloud deployment options



## Authentication & Role-Based Access Control

This application now includes a complete authentication system with role-based access control (RBAC).

### Quick Auth Setup

1. **Configure Supabase** (see detailed guide in [AUTH_SETUP_GUIDE.md](AUTH_SETUP_GUIDE.md))
   ```bash
   # Update backend/.env with your Supabase credentials
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key_here
   ```

2. **Database migrations are already applied** with roles and permissions

3. **Create dummy users** via signup page or API (see SEED_DATA.json for credentials)

4. **Assign roles** to users (requires admin - see AUTH_SETUP_GUIDE.md)

### Roles & Permissions

| Role                 | Read | Write | Approve | Admin |
|---------------------|------|-------|---------|-------|
| Project Manager     | ✓    | ✓     | ✓       | ✗     |
| Discipline Engineer | ✓    | ✓     | ✗       | ✗     |
| Review Engineer     | ✓    | ✗     | ✓       | ✗     |
| Administrator       | ✓    | ✓     | ✓       | ✓     |

### Demo Credentials

**IMPORTANT:** These are for DEVELOPMENT ONLY. Change passwords in production!

- Admin: admin@example.com / DemoPassword123!
- Project Manager: john.manager@example.com / DemoPassword123!
- Engineer: sarah.engineer@example.com / DemoPassword123!
- Reviewer: mike.reviewer@example.com / DemoPassword123!

**Note:** Users must be created via signup first, then have roles assigned by an admin.

### Auth API Endpoints

- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password with token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/assign-role` - Assign role (Admin only)

### Protected Project Endpoints

Example endpoints demonstrating permission checks:

- `GET /api/projects` - List projects (Read)
- `POST /api/projects` - Create project (Write)
- `POST /api/projects/:id/approve` - Approve project (Approve)
- `DELETE /api/projects/:id` - Delete project (Admin)

### Admin Endpoints

- `GET /api/admin/users` - List all users with roles (Admin only)

For detailed authentication setup and usage, see [AUTH_SETUP_GUIDE.md](AUTH_SETUP_GUIDE.md).

