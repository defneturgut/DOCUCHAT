"""
API request/response modelleri.
Tüm veri doğrulaması Pydantic ile yapılır.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── Doküman Modelleri ────────────────────────────────────────────────────────

class DocumentInfo(BaseModel):
    """Yüklenen doküman hakkında temel bilgi."""
    doc_id: str
    filename: str
    file_type: str
    chunk_count: int
    uploaded_at: datetime = Field(default_factory=datetime.now)
    size_kb: float


class DocumentListResponse(BaseModel):
    """Yüklenmiş dokümanların listesi."""
    documents: list[DocumentInfo]
    total: int


class DeleteResponse(BaseModel):
    """Silme işlemi sonucu."""
    success: bool
    message: str
    doc_id: str


# ─── Chat Modelleri ───────────────────────────────────────────────────────────

class ChatSource(BaseModel):
    """Cevabın dayandığı kaynak chunk bilgisi."""
    doc_id: str
    filename: str
    chunk_text: str        # İlgili metin parçası (kısaltılmış)
    relevance_score: float # 0.0 - 1.0 arası benzerlik skoru


class ChatRequest(BaseModel):
    """Kullanıcıdan gelen soru isteği."""
    question: str = Field(..., min_length=2, max_length=2000)
    doc_ids: Optional[list[str]] = None  # None = tüm dokümanlar


class ChatResponse(BaseModel):
    """LLM'den dönen cevap ve kaynaklar."""
    answer: str
    sources: list[ChatSource]
    question: str
    model_used: str


# ─── Sistem Modelleri ─────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Sistem sağlık durumu."""
    status: str
    groq_connected: bool
    google_connected: bool
    document_count: int
    version: str = "1.0.0"
