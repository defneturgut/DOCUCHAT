"""
Chat endpoint'leri:
  POST /api/chat          → tam cevap (JSON)
  POST /api/chat/stream   → streaming cevap (SSE)
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from core.models import ChatRequest, ChatResponse
from services.llm import LLMService
from services.vector_store import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


# ─── Bağımlılıklar ────────────────────────────────────────────────────────────

def get_vector_store() -> VectorStore:
    from main import vector_store
    return vector_store


def get_llm_service() -> LLMService:
    from main import llm_service
    return llm_service


# ─── Normal Chat ──────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    vs: VectorStore = Depends(get_vector_store),
    llm: LLMService = Depends(get_llm_service),
):
    """
    Kullanıcı sorusunu alır, ilgili chunk'ları bulur, LLM cevabı üretir.

    RAG akışı:
    1. Soruyu vektöre çevir
    2. ChromaDB'de benzer chunk'ları bul (top-k)
    3. Chunk'ları + soruyu prompt'a ekle
    4. Groq LLM ile cevap üret
    5. Cevap + kaynak bilgisiyle döndür
    """
    if vs.total_chunks() == 0:
        raise HTTPException(
            status_code=400,
            detail="Henüz hiç doküman yüklenmedi. Önce doküman yükleyin.",
        )

    # 1-2: Benzer chunk'ları bul
    sources = vs.search(question=request.question, doc_ids=request.doc_ids)

    if not sources:
        raise HTTPException(
            status_code=404,
            detail="Soruyla ilgili içerik bulunamadı.",
        )

    # 3-4: Cevap üret
    try:
        answer = await llm.generate(question=request.question, sources=sources)
    except Exception as e:
        logger.exception("LLM cevap üretimi başarısız")
        raise HTTPException(status_code=502, detail=f"LLM hatası: {str(e)}")

    from core.config import get_settings
    return ChatResponse(
        answer=answer,
        sources=sources,
        question=request.question,
        model_used=get_settings().groq_model,
    )


# ─── Streaming Chat ───────────────────────────────────────────────────────────

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    vs: VectorStore = Depends(get_vector_store),
    llm: LLMService = Depends(get_llm_service),
):
    """
    Server-Sent Events (SSE) ile streaming cevap döndürür.
    
    Frontend şu event tiplerini alır:
      data: {"type": "sources", "data": [...]}   → kaynaklar (başta)
      data: {"type": "token",   "data": "..."}   → cevap token'ları
      data: {"type": "done",    "data": ""}       → tamamlandı
      data: {"type": "error",   "data": "..."}   → hata
    """
    if vs.total_chunks() == 0:
        raise HTTPException(status_code=400, detail="Doküman yüklenmedi.")

    sources = vs.search(question=request.question, doc_ids=request.doc_ids)

    async def event_generator():
        # 1. Önce kaynak bilgilerini gönder
        sources_payload = [s.model_dump() for s in sources]
        yield f"data: {json.dumps({'type': 'sources', 'data': sources_payload})}\n\n"

        if not sources:
            yield f"data: {json.dumps({'type': 'error', 'data': 'İlgili içerik bulunamadı.'})}\n\n"
            return

        # 2. Token'ları akış olarak gönder
        try:
            async for token in llm.generate_stream(
                question=request.question,
                sources=sources,
            ):
                yield f"data: {json.dumps({'type': 'token', 'data': token})}\n\n"
        except Exception as e:
            logger.exception("Streaming sırasında hata")
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
            return

        # 3. Bittiğini bildir
        yield f"data: {json.dumps({'type': 'done', 'data': ''})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Nginx için buffer devre dışı
        },
    )
