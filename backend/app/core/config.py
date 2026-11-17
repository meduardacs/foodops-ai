from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'FoodOps AI'
    database_url: str = 'sqlite:///./foodops.db'
    openai_api_key: str = ''
    openai_model: str = 'gpt-4o-mini'
    rag_embeddings: str = 'tfidf'  # optional: pgvector (requires PostgreSQL and OpenAI key)
    frontend_origin: str = 'http://localhost:5173,http://localhost:3000'
    demo_seed: bool = True
    max_upload_mb: int = 5
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')


@lru_cache
def get_settings() -> Settings:
    return Settings()
