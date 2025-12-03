"""
Configuration management for HiRA
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "HiRA"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://hira-frontend.vercel.app",  # Production frontend
        "https://hira-frontend-git-main-moosas-projects-fcab463d.vercel.app",  # Main branch deployment
    ]

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Recall.ai (Zoom Bot Integration)
    RECALL_API_KEY: str = ""
    WEBHOOK_URL: str = "http://localhost:8000"

    # Zoom Bot (Legacy - for reference)
    ZOOM_CLIENT_ID: str = ""
    ZOOM_CLIENT_SECRET: str = ""
    ZOOM_VERIFICATION_TOKEN: str = ""
    ZOOM_BOT_JID: str = ""

    # Speech Services
    DEEPGRAM_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""

    # OpenAI / Anthropic
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # LLM Settings
    LLM_PROVIDER: str = "anthropic"  # or "openai"
    LLM_MODEL: str = "claude-3-5-sonnet-20241022"  # or "gpt-4-turbo"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000

    # Embedding Settings
    EMBEDDING_PROVIDER: str = "openai"  # or "sentence-transformers"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSION: int = 3072

    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 5
    SIMILARITY_THRESHOLD: float = 0.5

    # Vector Database
    VECTOR_DB_TYPE: str = "chroma"  # or "faiss", "pinecone"
    CHROMA_PERSIST_DIRECTORY: str = "./data/vectorstore"
    CHROMA_COLLECTION_NAME: str = "hira_documents"

    # File Upload
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md"]

    # Database (for future use with PostgreSQL)
    DATABASE_URL: str = "sqlite:///./data/hira.db"

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
