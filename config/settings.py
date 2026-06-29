import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Data directories
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    VERSIONS_DIR: str = os.path.join(DATA_DIR, "versions")
    VERSIONS_JSON: str = os.path.join(DATA_DIR, "versions.json")
    ACTIVE_VERSION_TXT: str = os.path.join(DATA_DIR, "active_version.txt")
    
    # DB settings
    DB_PATH: str = os.path.join(BASE_DIR, "database", "maintenance.db")
    SCHEMA_PATH: str = os.path.join(BASE_DIR, "database", "schema.sql")
    
    # Vector store settings
    FAISS_INDEX_PATH: str = os.path.join(BASE_DIR, "vector_store", "index.faiss")
    METADATA_DB_PATH: str = os.path.join(BASE_DIR, "vector_store", "metadata.db")
    
    # Embedding Settings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_CACHE_DIR: str = os.path.join(BASE_DIR, "embeddings", "cache")
    
    # LLM Settings
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        env_file_encoding = 'utf-8'
        extra = "ignore"

settings = Settings()
