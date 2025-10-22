import logging
import time
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny
)
from app.config import get_settings
from app.services.document_processor import DocumentChunk

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.collection_name = self.settings.qdrant_collection
        self._connect()
    
    def _connect(self):
        """Connect to Qdrant"""
        try:
            self.client = QdrantClient(
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port,
                timeout=60  # Increase timeout to 60 seconds
            )
            logger.info(f"Connected to Qdrant at {self.settings.qdrant_host}:{self.settings.qdrant_port}")
            self._ensure_collection()
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                collections = self.client.get_collections().collections
                collection_names = [col.name for col in collections]
                
                if self.collection_name not in collection_names:
                    logger.info(f"Creating collection: {self.collection_name}")
                    # bge-m3 produces 1024-dimensional vectors
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                    )
                    logger.info(f"Created collection: {self.collection_name}")
                else:
                    logger.info(f"Collection {self.collection_name} already exists")
                return  # Success
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Error ensuring collection after {max_retries} attempts: {e}")
                    raise
    
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        """Add document chunks with embeddings to Qdrant"""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match")
        
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=hash(f"{chunk.metadata['document_id']}_{chunk.metadata['chunk_id']}") & 0x7FFFFFFFFFFFFFFF,
                vector=embedding,
                payload={
                    'text': chunk.text,
                    'document_id': chunk.metadata['document_id'],
                    'filename': chunk.metadata['filename'],
                    'file_type': chunk.metadata['file_type'],
                    'chunk_id': chunk.metadata['chunk_id'],
                    'page_number': chunk.metadata.get('page_number'),
                    'sheet_name': chunk.metadata.get('sheet_name'),
                }
            )
            points.append(point)
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
        
        logger.info(f"Added {len(points)} chunks to Qdrant")
    
    def search(
        self,
        query_embedding: List[float],
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        search_filter = None
        
        if document_ids:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchAny(any=document_ids)
                    )
                ]
            )
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=search_filter
        )
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                'text': result.payload['text'],
                'document_id': result.payload['document_id'],
                'filename': result.payload['filename'],
                'page_number': result.payload.get('page_number'),
                'sheet_name': result.payload.get('sheet_name'),
                'score': result.score
            })
        
        return formatted_results
    
    def delete_document(self, document_id: str):
        """Delete all chunks for a document"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
        logger.info(f"Deleted document {document_id} from Qdrant")
    
    def is_connected(self) -> bool:
        """Check if connected to Qdrant"""
        try:
            self.client.get_collections()
            return True
        except:
            return False


# Global instance
_vector_store = None


def get_vector_store() -> VectorStoreService:
    """Get or create the global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store

