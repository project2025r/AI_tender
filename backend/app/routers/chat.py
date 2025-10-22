import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, SourceReference
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with documents using RAG"""
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        # Get RAG service
        rag_service = get_rag_service()
        
        # Query the system
        response_text, source_chunks = await rag_service.query(
            query=request.message,
            document_ids=request.document_ids,
            top_k=request.top_k
        )
        
        # Format sources
        sources = [
            SourceReference(
                document_id=chunk['document_id'],
                document_name=chunk['filename'],
                chunk_text=chunk['text'][:300] + "..." if len(chunk['text']) > 300 else chunk['text'],
                page_number=chunk.get('page_number'),
                sheet_name=chunk.get('sheet_name'),
                score=chunk['score']
            )
            for chunk in source_chunks
        ]
        
        return ChatResponse(
            response=response_text,
            sources=sources
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


