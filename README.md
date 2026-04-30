🗂️ DocuChat — Kendi Dokümanlarınla Sohbet Et
RAG (Retrieval-Augmented Generation) tabanlı doküman sohbet uygulaması.
PDF, DOCX ve TXT dosyalarını yükle — yapay zeka ile doğrudan sohbet et, kaynaklarını gör.

✨ Özellikler

📄 PDF, DOCX, DOC ve TXT dosyası yükleme
🔍 Vektör tabanlı semantik arama (ChromaDB)
⚡ Gerçek zamanlı streaming yanıtlar
📌 Her yanıtta kaynak chunk'ları gösterme
🗂️ Çoklu doküman yönetimi ve filtreleme


🛠️ Teknoloji Yığını
KatmanTeknolojiBackendFastAPI + Python 3.12LLMGroq — llama-3.3-70b-versatileEmbeddingGoogle — text-embedding-004Vektör DBChromaDB (kalıcı disk)RAGLangChainFrontendReact 18 + ViteContainerDocker + Docker Compose

🚀 Kurulum
1. Repoyu klonla
bashgit clone https://github.com/kullanici-adi/docuchat.git
cd docuchat
2. API anahtarlarını ayarla
bashcd backend
cp .env.example .env
.env dosyasını aç ve aşağıdaki değerleri doldur:
envGROQ_API_KEY=gsk_...       # https://console.groq.com (ücretsiz)
GOOGLE_API_KEY=AIza...     # https://aistudio.google.com (ücretsiz)

Her iki servis de ücretsiz kayıt ile kullanılabilir.


3a. 🐳 Docker ile Çalıştır (Önerilen)
bash# Proje kök dizininde:
docker compose up --build
ServisAdresUygulamahttp://localhost:5173Backend APIhttp://localhost:8000Swagger Docshttp://localhost:8000/docs

3b. Manuel Kurulum (Docker olmadan)
Gereksinimler: Python 3.12+, Node.js 18+
Terminal 1 — Backend:
bashcd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
Terminal 2 — Frontend:
bashcd frontend
npm install
npm run dev

📖 Kullanım

Doküman yükle — Sol panelden PDF/DOCX/TXT sürükle veya tıkla
Filtrele (opsiyonel) — Belirli dokümanları seçerek sorguyu sınırla
Soru sor — Alt kutuya soruyu yaz, Enter'a bas
Kaynakları gör — Her yanıtta hangi dokümandan alındığı gösterilir


📁 Proje Yapısı
docuchat/
├── backend/
│   ├── api/
│   │   ├── chat.py          # /api/chat, /api/chat/stream
│   │   ├── documents.py     # /api/documents (upload/list/delete)
│   │   └── health.py        # /api/health
│   ├── core/
│   │   ├── config.py        # Pydantic Settings
│   │   └── models.py        # Request/Response şemaları
│   ├── services/
│   │   ├── parser.py        # PDF/DOCX/TXT metin çıkarma
│   │   ├── vector_store.py  # ChromaDB işlemleri
│   │   └── llm.py           # Groq LLM + prompt
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/      # Sidebar, ChatMessage, ChatInput
│   │   ├── hooks/           # useDocuments, useChat
│   │   ├── services/        # Axios + SSE
│   │   └── App.jsx
│   └── package.json
└── docker-compose.yml

🔌 API Referansı
Doküman Yönetimi
POST   /api/documents/upload    Dosya yükle
GET    /api/documents           Tüm dokümanları listele
DELETE /api/documents/{doc_id}  Doküman sil
Chat
POST /api/chat          Tam JSON yanıt
POST /api/chat/stream   SSE streaming yanıt
İstek gövdesi:
json{
  "question": "Bu dokümanı özetle",
  "doc_ids": null
}

doc_ids: null → tüm dokümanlar, ["id1", "id2"] → belirli dokümanlar


⚙️ Ortam Değişkenleri
DeğişkenVarsayılanAçıklamaGROQ_API_KEY—Groq API anahtarı (zorunlu)GOOGLE_API_KEY—Google AI anahtarı (zorunlu)CHROMA_PERSIST_DIR./chroma_dbChromaDB klasörüCHUNK_SIZE500Chunk büyüklüğü (token)CHUNK_OVERLAP100Chunk örtüşme miktarıTOP_K_RESULTS5Kaç chunk getirilsinMAX_FILE_SIZE_MB50Maksimum dosya boyutu

🧠 RAG Akışı
Doküman Yükleme:
  Dosya → Metin çıkarma → Chunking (500 token, %20 overlap)
        → Google Embedding → ChromaDB

Sorgulama:
  Soru → Google Embedding → ChromaDB similarity search (top-5)
       → Prompt template → Groq LLM → Streaming yanıt + kaynaklar
