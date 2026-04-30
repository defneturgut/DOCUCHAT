"""
ChromaDB vektör veritabanı servisi.
Doküman chunk'larını saklar, siler ve benzerlik araması yapar.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from core.config import get_settings
from core.models import DocumentInfo, ChatSource

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStore:
    """
    ChromaDB üzerinde RAG işlemleri:
    - add_document: metni chunk'la, embed et, kaydet
    - search: soruya en benzer chunk'ları bul
    - delete_document: tüm chunk'ları sil
    - list_documents: yüklü doküman listesi
    """

    def __init__(self):
        # ChromaDB istemcisi (kalıcı disk depolama)
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Google Embedding modeli
        self._embedder = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.google_api_key,
        )

        # Tek bir koleksiyon — tüm dokümanlar burada
        self._collection = self._client.get_or_create_collection(
            name="docuchat",
            metadata={"hnsw:space": "cosine"},  # Cosine similarity
        )

        # Metin bölücü
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        logger.info("VectorStore başlatıldı. Mevcut chunk sayısı: %d", self._collection.count())

    # ─── Doküman Ekleme ───────────────────────────────────────────────────────

    def add_document(
        self,
        text: str,
        filename: str,
        file_type: str,
        file_size_kb: float,
    ) -> DocumentInfo:
        """
        Metni chunk'lara böler, vektöre çevirir ve ChromaDB'ye kaydeder.

        Returns:
            Oluşturulan doküman bilgisi
        """
        doc_id = str(uuid.uuid4())
        chunks = self._splitter.split_text(text)

        if not chunks:
            raise ValueError("Metin bölünemedi, chunk oluşturulamadı.")

        logger.info("'%s' için %d chunk oluşturuldu.", filename, len(chunks))

        # Vektörleri oluştur
        embeddings = self._embedder.embed_documents(chunks)

        # ChromaDB'ye toplu ekle
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "doc_id": doc_id,
                "filename": filename,
                "file_type": file_type,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "uploaded_at": datetime.now().isoformat(),
            }
            for i in range(len(chunks))
        ]

        self._collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

        logger.info("Doküman '%s' (id=%s) başarıyla eklendi.", filename, doc_id)

        return DocumentInfo(
            doc_id=doc_id,
            filename=filename,
            file_type=file_type,
            chunk_count=len(chunks),
            size_kb=file_size_kb,
        )

    # ─── Benzerlik Araması ────────────────────────────────────────────────────

    def search(
        self,
        question: str,
        doc_ids: Optional[list[str]] = None,
        top_k: Optional[int] = None,
    ) -> list[ChatSource]:
        """
        Soruya en benzer chunk'ları bulur.

        Args:
            question: Kullanıcının sorusu
            doc_ids:  Belirli dokümanlar (None = tümü)
            top_k:    Kaç sonuç dönsün

        Returns:
            ChatSource listesi (benzerlik skoruyla)
        """
        k = top_k or settings.top_k_results
        total = self._collection.count()

        if total == 0:
            return []

        k = min(k, total)

        # Soru vektörü
        question_embedding = self._embedder.embed_query(question)

        # Belirli dokümanlarla filtrele
        where_filter = None
        if doc_ids:
            where_filter = {"doc_id": {"$in": doc_ids}}

        results = self._collection.query(
            query_embeddings=[question_embedding],
            n_results=k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        sources: list[ChatSource] = []
        for doc_text, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # Cosine distance → similarity score (0-1)
            score = max(0.0, 1.0 - distance)
            sources.append(
                ChatSource(
                    doc_id=meta["doc_id"],
                    filename=meta["filename"],
                    chunk_text=doc_text[:400] + ("..." if len(doc_text) > 400 else ""),
                    relevance_score=round(score, 3),
                )
            )

        return sources

    # ─── Doküman Silme ────────────────────────────────────────────────────────

    def delete_document(self, doc_id: str) -> int:
        """
        Bir dokümana ait tüm chunk'ları siler.

        Returns:
            Silinen chunk sayısı
        """
        results = self._collection.get(where={"doc_id": doc_id})
        chunk_ids = results["ids"]

        if not chunk_ids:
            return 0

        self._collection.delete(ids=chunk_ids)
        logger.info("Doküman %s silindi (%d chunk).", doc_id, len(chunk_ids))
        return len(chunk_ids)

    # ─── Doküman Listeleme ────────────────────────────────────────────────────

    def list_documents(self) -> list[DocumentInfo]:
        """
        Yüklü tüm dokümanları metadata'dan derler.
        Her doküman yalnızca bir kez listelenir (ilk chunk'tan).
        """
        if self._collection.count() == 0:
            return []

        all_meta = self._collection.get(include=["metadatas"])["metadatas"]
        seen: dict[str, DocumentInfo] = {}

        for meta in all_meta:
            doc_id = meta["doc_id"]
            if doc_id not in seen:
                seen[doc_id] = DocumentInfo(
                    doc_id=doc_id,
                    filename=meta["filename"],
                    file_type=meta["file_type"],
                    chunk_count=meta["total_chunks"],
                    uploaded_at=datetime.fromisoformat(meta["uploaded_at"]),
                    size_kb=0.0,  # Metadata'da saklanmıyor, görüntü amaçlı
                )

        return list(seen.values())

    def total_chunks(self) -> int:
        return self._collection.count()
