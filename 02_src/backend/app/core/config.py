from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # LLM — GPT-4o-mini (primary)
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"

    # LLM Fallbacks
    GROQ_API_KEY: str = ""           # Fallback 1: Groq Llama 3.3 70b
    DEEPSEEK_API_KEY: str = ""       # Fallback 2: DeepSeek Chat

    # Embeddings
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # App
    APP_SECRET_KEY: str = "wasel-dev-secret"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # RAG
    URL_QDRANT: str = ""
    API_KEY_QDRANT: str = ""
    TOP_K_JOBS: int = 3
    TOP_K_RESOURCES: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
