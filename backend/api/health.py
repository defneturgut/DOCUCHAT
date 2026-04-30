"""
Sistem sağlık kontrolü endpoint'i.
  GET /api/health → tüm servislerin durumu
"""
from fastapi import APIRouter, Depends
from core.models import HealthResponse
from services.vector_store import VectorStore
from services.llm import LLMService

router = APIRouter(prefix="/api", tags=["system"])


def get_vector_store() -> VectorStore:
    from main import vector_store
    return vector_store


def get_llm_service() -> LLMService:
    from main import llm_service
    return llm_service


@router.get("/health", response_model=HealthResponse)
async def health_check(
    vs: VectorStore = Depends(get_vector_store),
    llm: LLMService = Depends(get_llm_service),
):
    """Tüm servislerin canlı olup olmadığını kontrol eder."""
    groq_ok = await llm.health_check()

    # Google embedding'i hafifçe test et
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from core.config import get_settings
        s = get_settings()
        emb = GoogleGenerativeAIEmbeddings(model=s.embedding_model, google_api_key=s.google_api_key)
        emb.embed_query("test")
        google_ok = True
    except Exception:
        google_ok = False

    return HealthResponse(
        status="ok" if (groq_ok and google_ok) else "degraded",
        groq_connected=groq_ok,
        google_connected=google_ok,
        document_count=len(vs.list_documents()),
    )
