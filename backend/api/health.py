"""
Sistem sağlık kontrolü endpoint'i.
  GET /api/health → tüm servislerin durumu
"""
from fastapi import APIRouter, Depends
from core.models import HealthResponse
from services.vector_store import VectorStore

router = APIRouter(prefix="/api", tags=["system"])


def get_vector_store() -> VectorStore:
    from main import vector_store
    return vector_store


@router.get("/health", response_model=HealthResponse)
async def health_check(vs: VectorStore = Depends(get_vector_store)):
    """Tüm servislerin durumunu kontrol eder."""

    # Groq kontrolü — sadece API key var mı diye bak, istek atma
    from core.config import get_settings
    import os
    s = get_settings()
    groq_ok = bool(s.groq_api_key and s.groq_api_key.startswith("gsk_"))

    # Google kontrolü — küçük bir embed isteği at
    try:
        import google.generativeai as genai
        genai.configure(api_key=s.google_api_key)
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content="test",
            task_type="retrieval_query",
        )
        google_ok = bool(result.get("embedding"))
    except Exception as e:
        google_ok = False

    return HealthResponse(
        status="ok" if (groq_ok and google_ok) else "degraded",
        groq_connected=groq_ok,
        google_connected=google_ok,
        document_count=len(vs.list_documents()),
    )
