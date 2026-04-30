"""
DocuChat — Ana FastAPI Uygulaması
Kendi Dokümanlarınla Sohbet Et

Başlatmak için:
    uvicorn main:app --reload --port 8000
"""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from services.vector_store import VectorStore
from services.llm import LLMService
from api import documents, chat, health

# ─── Loglama ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("docuchat")

# ─── Singleton Servisler ──────────────────────────────────────────────────────
# Tüm endpoint'ler bu nesneleri paylaşır

vector_store: VectorStore
llm_service: LLMService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlangıç ve kapanış olayları."""
    global vector_store, llm_service

    settings = get_settings()
    logger.info("DocuChat başlatılıyor...")
    logger.info("Model: %s | Embedding: %s", settings.groq_model, settings.embedding_model)

    # Servisleri başlat
    vector_store = VectorStore()
    llm_service = LLMService()

    logger.info("Tüm servisler hazır. API dinleniyor...")
    yield

    # Kapanışta temizlik (ChromaDB otomatik kaydeder)
    logger.info("DocuChat kapatılıyor.")


# ─── FastAPI Uygulaması ───────────────────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title="DocuChat API",
    description="Dokümanlarınızla yapay zeka destekli sohbet",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — React frontend'e izin ver
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları bağla
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(health.router)


@app.get("/")
async def root():
    return {
        "app": "DocuChat API",
        "version": "1.0.0",
        "docs": "/docs",         # Swagger UI
        "redoc": "/redoc",       # ReDoc
    }
