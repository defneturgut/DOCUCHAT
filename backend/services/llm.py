"""
Groq LLM servisi.
Retrieval'dan gelen context + kullanıcı sorusu → anlamlı cevap üretir.
Streaming ve normal mod destekler.
"""
import logging
from typing import AsyncIterator

from groq import AsyncGroq

from core.config import get_settings
from core.models import ChatSource

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── Prompt Template ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sen yüklenen dokümanlar üzerinde çalışan, yardımsever bir yapay zeka asistanısın.

KURALLAR:
1. Cevaplarını YALNIZCA sağlanan "Doküman İçeriği" bölümündeki bilgilere dayandır.
2. Eğer soru dokümanlarda bulunmuyorsa, bunu açıkça söyle: "Bu bilgi yüklenen dokümanlarda bulunmuyor."
3. Cevabın sonunda hangi dokümandan bilgi aldığını belirt.
4. Türkçe sorulara Türkçe, İngilizce sorulara İngilizce cevap ver.
5. Uzun ve açıklayıcı cevaplar ver. Gerektiğinde madde madde listele.
6. Asla uydurma (hallucination) yapma."""

def _build_context(sources: list[ChatSource]) -> str:
    """Kaynak chunk'lardan LLM için context metni oluşturur."""
    if not sources:
        return "Hiçbir ilgili doküman içeriği bulunamadı."

    parts = []
    for i, src in enumerate(sources, start=1):
        parts.append(
            f"[Kaynak {i} — {src.filename} (uyum: {src.relevance_score:.0%})]\n"
            f"{src.chunk_text}"
        )

    return "\n\n---\n\n".join(parts)


def _build_user_message(question: str, sources: list[ChatSource]) -> str:
    """Kullanıcı mesajını oluşturur."""
    context = _build_context(sources)
    return (
        f"Doküman İçeriği:\n{context}\n\n"
        f"---\n\n"
        f"Soru: {question}"
    )


# ─── LLM Servisi ─────────────────────────────────────────────────────────────

class LLMService:
    """Groq API üzerinden cevap üretir."""

    def __init__(self):
        self._client = AsyncGroq(api_key=settings.groq_api_key)
        logger.info("LLMService başlatıldı. Model: %s", settings.groq_model)

    async def generate(
        self,
        question: str,
        sources: list[ChatSource],
    ) -> str:
        """
        Tek seferde tam cevap üretir.

        Returns:
            LLM'in ürettiği metin cevabı
        """
        user_message = _build_user_message(question, sources)

        response = await self._client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,      # Düşük: daha tutarlı, daha az yaratıcı
            max_tokens=2048,
        )

        answer = response.choices[0].message.content or ""
        logger.info("Cevap üretildi: %d karakter", len(answer))
        return answer

    async def generate_stream(
        self,
        question: str,
        sources: list[ChatSource],
    ) -> AsyncIterator[str]:
        """
        Streaming modda cevap üretir.
        Her token geldiğinde yield eder.

        Yields:
            Metin parçaları (token'lar)
        """
        user_message = _build_user_message(question, sources)

        stream = await self._client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=2048,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def health_check(self) -> bool:
        """Groq bağlantısını test eder."""
        try:
            response = await self._client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return bool(response.choices)
        except Exception as e:
            logger.warning("Groq health check başarısız: %s", e)
            return False
