from pydantic_settings import BaseSettings
from functools import lru_cache


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
    
    # Document Processing Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 100
    max_file_size_mb: int = 100
    
    # API Configuration
    upload_dir: str = "uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()

