"""
Uygulama yapılandırması — tüm ortam değişkenleri buradan okunur.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Anahtarları
    groq_api_key: str
    google_api_key: str

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"

    # Uygulama parametreleri
    max_file_size_mb: int = 50
    chunk_size: int = 500
    chunk_overlap: int = 100
    top_k_results: int = 5

    # CORS
    frontend_url: str = "http://localhost:5173"

    # Sabit model adları
    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "models/text-embedding-004"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Ayarları önbelleğe alarak döndürür (uygulama boyu tek instance)."""
    return Settings()
