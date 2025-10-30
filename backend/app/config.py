from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.1:8b-instruct-q4_0"
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "tender_documents"
    
    # Embedding Configuration
    embedding_model: str = "BAAI/bge-m3"
    embedding_batch_size: int = 32
    
    # Document Processing Configuration
    chunk_size: int = 1000  # Maximum tokens per chunk
    chunk_overlap: int = 200  # Increased overlap for better context preservation
    max_file_size_mb: int = 100
    
    # Semantic Chunking Configuration
    enable_semantic_chunking: bool = True
    enable_hierarchical_chunking: bool = True
    min_chunk_size: int = 100  # Minimum tokens per chunk
    
    # RAG Configuration
    retrieval_top_k: int = 5  # Number of chunks to retrieve
    reranking_enabled: bool = True
    reranking_factor: int = 3  # Retrieve reranking_factor * top_k chunks for reranking
    
    # API Configuration
    upload_dir: str = "uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()