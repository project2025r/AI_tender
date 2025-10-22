import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models.schemas import DocumentMetadata, DocumentUploadResponse, DocumentStatus
from app.services.document_processor import get_document_processor
from app.services.embeddings import get_embedding_service
from app.services.vector_store import get_vector_store
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# In-memory document registry (for single-user app)
documents_db: dict[str, DocumentMetadata] = {}

settings = get_settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)


def get_file_type(filename: str) -> str:
    """Get file extension"""
    return Path(filename).suffix.lower().lstrip('.')


def is_allowed_file(filename: str) -> bool:
    """Check if file type is allowed"""
    allowed_extensions = {'pdf', 'docx', 'doc', 'xlsx', 'xls'}
    return get_file_type(filename) in allowed_extensions


async def process_document_background(document_id: str, file_path: str, filename: str):
    """Background task to process document"""
    try:
        logger.info(f"Starting background processing for {filename}")
        
        # Update status to processing
        if document_id in documents_db:
            documents_db[document_id].status = DocumentStatus.PROCESSING
        
        # Process document
        processor = get_document_processor()
        chunks = processor.process_document(file_path, filename, document_id)
        
        # Generate embeddings
        embedding_service = get_embedding_service()
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = embedding_service.embed_batch(chunk_texts)
        
        # Store in vector database
        vector_store = get_vector_store()
        vector_store.add_chunks(chunks, embeddings)
        
        # Update document status
        if document_id in documents_db:
            documents_db[document_id].status = DocumentStatus.READY
            documents_db[document_id].total_chunks = len(chunks)
        
        logger.info(f"Successfully processed document {filename}: {len(chunks)} chunks")
        
    except Exception as e:
        logger.error(f"Error processing document {filename}: {e}")
        if document_id in documents_db:
            documents_db[document_id].status = DocumentStatus.FAILED
            documents_db[document_id].error_message = str(e)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload a document for processing"""
    
    # Validate file type
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported types: PDF, DOCX, XLSX"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    # Generate document ID
    document_id = str(uuid.uuid4())
    
    # Save file
    file_path = os.path.join(settings.upload_dir, f"{document_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Error saving file")
    
    # Create document metadata
    doc_metadata = DocumentMetadata(
        id=document_id,
        filename=file.filename,
        file_type=get_file_type(file.filename),
        upload_date=datetime.now(),
        status=DocumentStatus.PROCESSING
    )
    
    documents_db[document_id] = doc_metadata
    
    # Add background task to process document
    background_tasks.add_task(
        process_document_background,
        document_id,
        file_path,
        file.filename
    )
    
    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        status=DocumentStatus.PROCESSING,
        message="Document uploaded successfully. Processing in background."
    )


@router.get("", response_model=List[DocumentMetadata])
async def list_documents():
    """List all uploaded documents"""
    return list(documents_db.values())


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document(document_id: str):
    """Get document metadata by ID"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return documents_db[document_id]


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_metadata = documents_db[document_id]
    
    # Delete from vector store
    try:
        vector_store = get_vector_store()
        vector_store.delete_document(document_id)
    except Exception as e:
        logger.error(f"Error deleting from vector store: {e}")
    
    # Delete file
    file_pattern = f"{document_id}_*"
    upload_dir = Path(settings.upload_dir)
    for file_path in upload_dir.glob(file_pattern):
        try:
            file_path.unlink()
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
    
    # Remove from registry
    del documents_db[document_id]
    
    return {"message": f"Document {doc_metadata.filename} deleted successfully"}


