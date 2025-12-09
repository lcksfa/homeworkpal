"""
Configuration settings for Homework Pal application.
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""

    # Application
    APP_NAME: str = "Homework Pal"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    FRONTEND_HOST: str = os.getenv("FRONTEND_HOST", "0.0.0.0")
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "8000"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://homeworkpal:password@localhost:5432/homeworkpal")

    # LLM API Keys
    DASHSCOPE_API_KEY: Optional[str] = os.getenv("DASHSCOPE_API_KEY")
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # Vector Database
    VECTOR_DIMENSION: int = int(os.getenv("VECTOR_DIMENSION", "1536"))
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

    # File Upload
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    MAX_FILES: int = int(os.getenv("MAX_FILES", "5"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        case_sensitive = True


settings = Settings()