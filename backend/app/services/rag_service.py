import logging
from typing import List, Optional, Dict, Any
from app.services.embeddings import get_embedding_service
from app.services.vector_store import get_vector_store
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.llm_service = get_llm_service()
    
    def build_prompt(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Build a prompt with context from retrieved chunks"""
        context_parts = []
        
        for idx, chunk in enumerate(context_chunks, 1):
            source_info = f"Document: {chunk['filename']}"
            if chunk.get('page_number'):
                source_info += f", Page {chunk['page_number']}"
            elif chunk.get('sheet_name'):
                source_info += f", Sheet: {chunk['sheet_name']}"
            
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

Answer:"""
        
        return prompt
    
    async def query(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Query the RAG system
        Returns: (response_text, source_chunks)
        """
        # 1. Embed the query
        logger.info(f"Embedding query: {query[:100]}...")
        query_embedding = self.embedding_service.embed_text(query)
        
        # 2. Search for relevant chunks
        logger.info(f"Searching for top {top_k} relevant chunks")
        relevant_chunks = self.vector_store.search(
            query_embedding=query_embedding,
            document_ids=document_ids,
            top_k=top_k
        )
        
        if not relevant_chunks:
            return "I couldn't find any relevant information in the documents to answer your question.", []
        
        # 3. Build prompt with context
        prompt = self.build_prompt(query, relevant_chunks)
        
        # 4. Generate response
        logger.info("Generating response from LLM")
        response_text = ""
        async for chunk in self.llm_service.generate(prompt, stream=False):
            response_text += chunk
        
        return response_text, relevant_chunks


def get_rag_service() -> RAGService:
    """Get RAG service instance"""
    return RAGService()


