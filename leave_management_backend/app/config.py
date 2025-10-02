from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database - defaults to SQLite for local dev, uses DATABASE_URL env var for production
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./leave_management.db")
    
    SECRET_KEY: str = "your-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM API Keys (optional)
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OLLAMA_URL: Optional[str] = "http://localhost:11434/api/generate"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
    
    def get_database_url(self) -> str:
        """
        Returns the correct database URL.
        Converts postgres:// to postgresql+psycopg2:// for SQLAlchemy compatibility
        """
        db_url = self.DATABASE_URL
        
        # Render and some other platforms use postgres:// but SQLAlchemy needs postgresql://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
        
        return db_url

settings = Settings()