import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import documents, chat
from app.models.schemas import HealthCheckResponse
from app.services.embeddings import get_embedding_service
from app.services.vector_store import get_vector_store
from app.services.llm_service import get_llm_service
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Tender Document Chatbot API",
    description="API for uploading and querying tender documents using RAG",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(chat.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Tender Document Chatbot API...")
    
    settings = get_settings()
    logger.info(f"Configuration: {settings.dict()}")
    
    # Initialize services
    try:
        logger.info("Initializing embedding service...")
        get_embedding_service()
        
        logger.info("Initializing vector store...")
        get_vector_store()
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Tender Document Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    
    # Check embedding service
    try:
        embedding_service = get_embedding_service()
        embedding_loaded = embedding_service.is_loaded()
    except:
        embedding_loaded = False
    
    # Check Qdrant
    try:
        vector_store = get_vector_store()
        qdrant_connected = vector_store.is_connected()
    except:
        qdrant_connected = False
    
    # Check Ollama
    try:
        llm_service = get_llm_service()
        ollama_connected = await llm_service.check_health()
    except:
        ollama_connected = False
    
    all_healthy = embedding_loaded and qdrant_connected and ollama_connected
    
    return HealthCheckResponse(
        status="healthy" if all_healthy else "degraded",
        ollama_connected=ollama_connected,
        qdrant_connected=qdrant_connected,
        embedding_model_loaded=embedding_loaded
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


