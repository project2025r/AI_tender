import logging
import time
from typing import List, Dict, Any, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
    Range,
    MatchText
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
    
    def _generate_point_id(self, chunk: DocumentChunk) -> int:
        """Generate a unique point ID for a chunk"""
        # Create a unique identifier based on document_id, chunk_id, and granularity
        id_str = f"{chunk.metadata['document_id']}_{chunk.metadata['chunk_id']}"
        
        # Add granularity if available
        if 'granularity' in chunk.metadata:
            id_str += f"_{chunk.metadata['granularity']}"
            
        # Hash and ensure it's positive (Qdrant requires positive integers)
        return hash(id_str) & 0x7FFFFFFFFFFFFFFF
    
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        """Add document chunks with embeddings to Qdrant"""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match")
        
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Create a comprehensive payload with all available metadata
            payload = {
                'text': chunk.text,
                'document_id': chunk.metadata['document_id'],
                'filename': chunk.metadata['filename'],
                'file_type': chunk.metadata['file_type'],
                'chunk_id': chunk.metadata['chunk_id'],
            }
            
            # Add optional metadata fields if present
            for key in ['page_number', 'sheet_name', 'section_title', 'granularity', 'token_count']:
                if key in chunk.metadata:
                    payload[key] = chunk.metadata[key]
            
            point = PointStruct(
                id=self._generate_point_id(chunk),
                vector=embedding,
                payload=payload
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
    
    def _build_search_filter(
        self,
        document_ids: Optional[List[str]] = None,
        file_types: Optional[List[str]] = None,
        section_titles: Optional[List[str]] = None,
        granularity: Optional[str] = None,
        min_token_count: Optional[int] = None,
        max_token_count: Optional[int] = None
    ) -> Optional[Filter]:
        """Build a search filter based on provided criteria"""
        filter_conditions = []
        
        # Filter by document IDs
        if document_ids:
            filter_conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchAny(any=document_ids)
                )
            )
        
        # Filter by file types
        if file_types:
            filter_conditions.append(
                FieldCondition(
                    key="file_type",
                    match=MatchAny(any=file_types)
                )
            )
        
        # Filter by section titles (partial match)
        if section_titles:
            section_conditions = []
            for title in section_titles:
                section_conditions.append(
                    FieldCondition(
                        key="section_title",
                        match=MatchText(text=title)
                    )
                )
            # Add section conditions with OR logic
            if section_conditions:
                filter_conditions.append(Filter(should=section_conditions))
        
        # Filter by granularity
        if granularity:
            filter_conditions.append(
                FieldCondition(
                    key="granularity",
                    match=MatchValue(value=granularity)
                )
            )
        
        # Filter by token count range
        if min_token_count is not None or max_token_count is not None:
            token_range = {}
            if min_token_count is not None:
                token_range["gte"] = min_token_count
            if max_token_count is not None:
                token_range["lte"] = max_token_count
                
            filter_conditions.append(
                FieldCondition(
                    key="token_count",
                    range=Range(**token_range)
                )
            )
        
        # Return the combined filter if conditions exist
        if filter_conditions:
            return Filter(must=filter_conditions)
        return None
    
    def search(
        self,
        query_embedding: List[float],
        document_ids: Optional[List[str]] = None,
        file_types: Optional[List[str]] = None,
        section_titles: Optional[List[str]] = None,
        granularity: Optional[str] = None,
        min_token_count: Optional[int] = None,
        max_token_count: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks with advanced filtering"""
        search_filter = self._build_search_filter(
            document_ids=document_ids,
            file_types=file_types,
            section_titles=section_titles,
            granularity=granularity,
            min_token_count=min_token_count,
            max_token_count=max_token_count
        )
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=search_filter
        )
        
        formatted_results = []
        for result in results:
            # Extract all payload fields into the result
            result_dict = {
                'score': result.score,
                **result.payload
            }
            formatted_results.append(result_dict)
        
        return formatted_results
    
    def hybrid_search(
        self,
        query_text: str,
        query_embedding: List[float],
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector similarity and keyword matching
        
        This method combines vector search with keyword search to improve retrieval
        for queries that have specific keywords or terms.
        """
        # Extract keywords from the query (simple approach)
        keywords = [word.lower() for word in query_text.split() if len(word) > 3]
        
        # Perform vector search
        vector_results = self.search(
            query_embedding=query_embedding,
            document_ids=document_ids,
            top_k=top_k * 2  # Get more results for hybrid reranking
        )
        
        if not vector_results:
            return []
        
        # Rerank results based on keyword presence
        for result in vector_results:
            # Initialize keyword score
            keyword_score = 0
            text_lower = result['text'].lower()
            
            # Check for keyword presence
            for keyword in keywords:
                if keyword in text_lower:
                    keyword_score += 0.1  # Boost score for each keyword found
            
            # Combine vector similarity with keyword score
            result['hybrid_score'] = result['score'] + keyword_score
        
        # Sort by hybrid score
        vector_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        # Return top_k results
        return vector_results[:top_k]
    
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