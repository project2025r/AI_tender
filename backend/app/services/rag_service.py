import logging
import re
import traceback
from typing import List, Optional, Dict, Any, Tuple
from app.services.embeddings import get_embedding_service
from app.services.vector_store import get_vector_store
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.llm_service = get_llm_service()
    
    def preprocess_query(self, query: str) -> str:
        """
        Preprocess the query to improve retrieval performance
        
        This function:
        1. Removes unnecessary punctuation
        2. Normalizes whitespace
        3. Expands common abbreviations
        """
        # Remove excessive punctuation
        query = re.sub(r'[^\w\s\?]', ' ', query)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        # Expand common abbreviations in tender documents
        abbreviations = {
            r'\bRFP\b': 'Request for Proposal',
            r'\bRFQ\b': 'Request for Quotation',
            r'\bEOI\b': 'Expression of Interest',
            r'\bT&C\b': 'Terms and Conditions',
            r'\bSOW\b': 'Scope of Work',
        }
        
        for abbr, expansion in abbreviations.items():
            query = re.sub(abbr, f"{abbr} ({expansion})", query)
        
        return query
    
    def extract_query_keywords(self, query: str) -> List[str]:
        """Extract important keywords from the query"""
        # Remove stop words (simplified approach)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                     'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 
                     'about', 'like', 'through', 'over', 'before', 'after', 'between', 
                     'under', 'above', 'of', 'from', 'up', 'down', 'into', 'during', 'what',
                     'when', 'where', 'how', 'why', 'who', 'whom', 'which', 'whose'}
        
        # Tokenize and filter
        words = query.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def build_prompt(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Build a prompt with context from retrieved chunks"""
        context_parts = []
        
        for idx, chunk in enumerate(context_chunks, 1):
            source_info = f"Document: {chunk['filename']}"
            if chunk.get('page_number'):
                source_info += f", Page {chunk['page_number']}"
            elif chunk.get('sheet_name'):
                source_info += f", Sheet: {chunk['sheet_name']}"
            
            if chunk.get('section_title'):
                source_info += f", Section: {chunk['section_title']}"
                
            if chunk.get('granularity'):
                source_info += f" ({chunk['granularity']})"
            
            context_parts.append(f"[Context {idx}] ({source_info})\n{chunk['text']}")
        
        context_text = "\n\n".join(context_parts)
        
        prompt = f"""You are a helpful assistant analyzing tender documents. Answer the user's question based on the provided context from the documents.

Context from documents:
{context_text}

User question: {query}

Instructions:
- Answer the question based on the provided context
- Be specific and cite which document or page the information comes from
- If the context doesn't contain enough information to answer fully, say so
- Be concise but thorough
- If the question is about specific requirements, quote the exact text from the document
- For numerical data, ensure accuracy and cite the source section

Answer:"""
        
        return prompt
    
    async def query(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Query the RAG system with improved retrieval
        Returns: (response_text, source_chunks)
        """
        try:
            # 1. Preprocess the query
            processed_query = self.preprocess_query(query)
            logger.info(f"Processed query: {processed_query}")
            
            # 2. Extract keywords for potential query expansion
            keywords = self.extract_query_keywords(processed_query)
            logger.info(f"Extracted keywords: {keywords}")
            
            # 3. Embed the query
            query_embedding = self.embedding_service.embed_text(processed_query)
            
            # 4. Search for relevant chunks (retrieve more than needed for reranking)
            retrieval_k = min(top_k * 3, 15)  # Retrieve more chunks than needed
            logger.info(f"Searching for top {retrieval_k} relevant chunks for reranking")
            relevant_chunks = self.vector_store.search(
                query_embedding=query_embedding,
                document_ids=document_ids,
                top_k=retrieval_k
            )
            
            if not relevant_chunks:
                return "I couldn't find any relevant information in the documents to answer your question.", []
            
            # 5. Rerank results to improve relevance
            try:
                if len(relevant_chunks) > top_k:
                    logger.info(f"Reranking {len(relevant_chunks)} chunks")
                    reranked_chunks = self.embedding_service.rerank_results(
                        query=processed_query,
                        results=relevant_chunks,
                        top_k=top_k
                    )
                    if reranked_chunks:  # Only use reranked results if successful
                        relevant_chunks = reranked_chunks
                    else:
                        # If reranking returned empty results, use original but limit to top_k
                        relevant_chunks = relevant_chunks[:top_k]
                        logger.warning("Reranking returned empty results, using original chunks")
            except Exception as e:
                logger.error(f"Error during reranking, using original chunks: {e}")
                # If reranking fails, use original chunks but limit to top_k
                relevant_chunks = relevant_chunks[:top_k]
            
            # 6. Build prompt with context
            prompt = self.build_prompt(query, relevant_chunks)
            
            # 7. Generate response
            logger.info("Generating response from LLM")
            response_text = ""
            async for chunk in self.llm_service.generate(prompt, stream=False):
                response_text += chunk
            
            return response_text, relevant_chunks
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            logger.error(traceback.format_exc())
            return f"I'm sorry, but I encountered an error while processing your question. Error details: {str(e)}", []


def get_rag_service() -> RAGService:
    """Get RAG service instance"""
    return RAGService()