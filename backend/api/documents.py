"""
Doküman yönetimi endpoint'leri:
  POST /api/documents/upload  → doküman yükle
  GET  /api/documents         → listeyi getir
  DELETE /api/documents/{id}  → sil
"""
import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from core.config import get_settings, Settings
from core.models import DeleteResponse, DocumentInfo, DocumentListResponse
from services.parser import SUPPORTED_EXTENSIONS, extract_text
from services.vector_store import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


# ─── Bağımlılıklar ────────────────────────────────────────────────────────────

def get_vector_store() -> VectorStore:
    """FastAPI dependency injection ile VectorStore örneği döndürür."""
    from main import vector_store  # main.py'de singleton oluşturulur
    return vector_store


# ─── Endpoint'ler ─────────────────────────────────────────────────────────────

@router.post("/upload", response_model=DocumentInfo, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    vs: VectorStore = Depends(get_vector_store),
):
    """
    Doküman yükle ve RAG pipeline'ını çalıştır.

    1. Dosya boyutu ve formatı kontrol edilir
    2. Metin çıkarılır (PDF/DOCX/TXT)
    3. Chunk'lara bölünür
    4. Embedding oluşturulur
    5. ChromaDB'ye kaydedilir
    """
    # Format kontrolü
    suffix = "." + (file.filename or "").rsplit(".", 1)[-1].lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Desteklenmeyen format: '{suffix}'. Kabul: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    # Dosyayı oku
    file_bytes = await file.read()

    # Boyut kontrolü
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Dosya çok büyük. Maksimum: {settings.max_file_size_mb} MB",
        )

    # Metin çıkar
    try:
        text = extract_text(file_bytes, file.filename or "unknown")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Vektör DB'ye ekle
    try:
        doc_info = vs.add_document(
            text=text,
            filename=file.filename or "unknown",
            file_type=suffix.lstrip(".").upper(),
            file_size_kb=round(len(file_bytes) / 1024, 2),
        )
    except Exception as e:
        logger.exception("Doküman eklenemedi")
        raise HTTPException(status_code=500, detail=f"Doküman işlenemedi: {str(e)}")

    logger.info("Yüklendi: %s (%d chunk)", doc_info.filename, doc_info.chunk_count)
    return doc_info


@router.get("", response_model=DocumentListResponse)
async def list_documents(vs: VectorStore = Depends(get_vector_store)):
    """Yüklü tüm dokümanları listeler."""
    docs = vs.list_documents()
    return DocumentListResponse(documents=docs, total=len(docs))


@router.delete("/{doc_id}", response_model=DeleteResponse)
async def delete_document(
    doc_id: str,
    vs: VectorStore = Depends(get_vector_store),
):
    """Belirtilen dokümanı ve tüm chunk'larını siler."""
    deleted_count = vs.delete_document(doc_id)

    if deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Doküman bulunamadı: {doc_id}",
        )

    return DeleteResponse(
        success=True,
        message=f"{deleted_count} chunk silindi.",
        doc_id=doc_id,
    )
