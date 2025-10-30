from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional, Union
import logging
import numpy as np
import torch
from app.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.settings.embedding_model}")
            self.model = SentenceTransformer(self.settings.embedding_model)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if self.model is None:
            raise RuntimeError("Embedding model not loaded")
        
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        if self.model is None:
            raise RuntimeError("Embedding model not loaded")
        
        embeddings = self.model.encode(
            texts, 
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100
        )
        return embeddings.tolist()
    
    def embed_with_context(self, query: str, context: Optional[str] = None) -> List[float]:
        """
        Generate contextually enhanced embedding for query
        
        This method enhances query embedding by incorporating context when available,
        which helps improve retrieval relevance for context-dependent queries.
        """
        if self.model is None:
            raise RuntimeError("Embedding model not loaded")
        
        if context:
            # Create a context-enhanced query
            enhanced_query = f"{query} [Context: {context}]"
            embedding = self.model.encode(enhanced_query, normalize_embeddings=True)
        else:
            embedding = self.model.encode(query, normalize_embeddings=True)
            
        return embedding.tolist()
    
    def embed_hierarchical(self, text: str, granularity_levels: List[str] = ["document", "paragraph", "sentence"]) -> Dict[str, List[float]]:
        """
        Generate hierarchical embeddings at different granularity levels
        
        This creates multiple embeddings for the same content at different granularity levels,
        which helps capture both high-level concepts and specific details.
        """
        if self.model is None:
            raise RuntimeError("Embedding model not loaded")
            
        result = {}
        
        # Document-level embedding
        if "document" in granularity_levels:
            result["document"] = self.embed_text(text)
        
        # Paragraph-level embeddings
        if "paragraph" in granularity_levels:
            paragraphs = text.split("\n\n")
            if paragraphs:
                paragraph_embeddings = self.embed_batch([p for p in paragraphs if p.strip()])
                result["paragraph"] = paragraph_embeddings
        
        # Sentence-level embeddings
        if "sentence" in granularity_levels:
            import nltk
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
                
            from nltk.tokenize import sent_tokenize
            sentences = sent_tokenize(text)
            if sentences:
                sentence_embeddings = self.embed_batch([s for s in sentences if s.strip()])
                result["sentence"] = sentence_embeddings
                
        return result
    
    def rerank_results(self, query: str, results: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rerank results using semantic similarity
        
        This method improves ranking by computing similarity between query and documents
        """
        if not results:
            return []
            
        try:
            logger.info(f"Reranking {len(results)} results")
            
            # Extract texts from results
            texts = [result["text"] for result in results]
            
            # Create embeddings for query and documents separately
            query_embedding = self.embed_text(query)
            document_embeddings = self.embed_batch(texts)
            
            # Convert to tensors
            query_tensor = torch.tensor(query_embedding)
            doc_tensors = torch.tensor(document_embeddings)
            
            # Calculate cosine similarities
            similarities = torch.nn.functional.cosine_similarity(
                query_tensor.unsqueeze(0), 
                doc_tensors, 
                dim=1
            )
            
            # Sort results by similarity scores
            reranked_indices = similarities.argsort(descending=True).tolist()
            
            # Return reranked results
            reranked_results = [results[i] for i in reranked_indices[:top_k]]
            
            # Update scores
            for i, result in enumerate(reranked_results):
                result["score"] = float(similarities[reranked_indices[i]])
                
            return reranked_results
            
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # If reranking fails, return original results (up to top_k)
            return results[:top_k]
    
    def is_loaded(self) -> bool:
        """Check if the model is loaded"""
        return self.model is not None


# Global instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service