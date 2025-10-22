from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    file_type: str
    upload_date: datetime
    status: DocumentStatus
    total_chunks: int = 0
    error_message: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    message: str


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    message: str
    document_ids: Optional[List[str]] = Field(
        default=None, 
        description="List of document IDs to search. If None, search all documents."
    )
    top_k: int = Field(default=5, description="Number of relevant chunks to retrieve")


class SourceReference(BaseModel):
    document_id: str
    document_name: str
    chunk_text: str
    page_number: Optional[int] = None
    sheet_name: Optional[str] = None
    score: float


class ChatResponse(BaseModel):
    response: str
    sources: List[SourceReference]


class HealthCheckResponse(BaseModel):
    status: str
    ollama_connected: bool
    qdrant_connected: bool
    embedding_model_loaded: bool


