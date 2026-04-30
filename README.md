# DocuChat — Kendi Dokümanlarınla Sohbet Et

RAG (Retrieval-Augmented Generation) tabanlı doküman sohbet uygulaması.  
PDF, DOCX, DOC ve TXT dosyalarını yükle, yapay zeka ile sohbet et.

---

## Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Backend | FastAPI + Python 3.12 |
| LLM | Groq — llama-3.3-70b-versatile |
| Embedding | Google — text-embedding-004 |
| Vektör DB | ChromaDB (kalıcı disk) |
| RAG | LangChain |
| Frontend | React 18 + Vite |
| Container | Docker + Docker Compose |

---

## Proje Yapısı

```
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
│   ├── main.py              # FastAPI uygulaması
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx       # Doküman paneli
│   │   │   ├── ChatMessage.jsx   # Mesaj + kaynak
│   │   │   └── ChatInput.jsx     # Soru girişi
│   │   ├── hooks/
│   │   │   ├── useDocuments.js   # Doküman state
│   │   │   └── useChat.js        # Chat + streaming state
│   │   ├── services/
│   │   │   └── api.js            # Axios + fetch SSE
│   │   ├── styles/
│   │   │   └── global.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

---

## Kurulum

### 1. API Anahtarları

```bash
# Backend klasörüne gir
cd backend

# .env dosyası oluştur
cp .env.example .env
```

`.env` dosyasını düzenle:

```env
GROQ_API_KEY=gsk_...        # https://console.groq.com
GOOGLE_API_KEY=AIza...      # https://aistudio.google.com
```

---

### 2a. Docker ile (Önerilen)

```bash
# Proje kök dizininde:
docker compose up --build
```

- Frontend: http://localhost:5173  
- Backend API: http://localhost:8000  
- Swagger Docs: http://localhost:8000/docs

---

### 2b. Manuel Kurulum

**Backend:**
```bash
cd backend

# Sanal ortam
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Bağımlılıklar
pip install -r requirements.txt

# Sunucuyu başlat
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend

npm install
npm run dev
```

---

## Kullanım

1. **Doküman yükle** — Sol panelden PDF/DOCX/TXT sürükle veya tıkla
2. **Filtrele** (opsiyonel) — Belirli dokümanları seçerek sorgunu sınırla
3. **Soru sor** — Alt kutuda soruyu yaz, Enter'a bas
4. **Kaynakları gör** — Her cevapta hangi dokümandan alındığı gösterilir

---

## API Referansı

### Doküman Yönetimi

```
POST   /api/documents/upload    Dosya yükle
GET    /api/documents           Tüm dokümanları listele
DELETE /api/documents/{doc_id}  Doküman sil
```

### Chat

```
POST /api/chat          Tam JSON cevap
POST /api/chat/stream   SSE streaming cevap
```

**Chat istek gövdesi:**
```json
{
  "question": "Bu dokümanı özetle",
  "doc_ids": null          // null = tüm dokümanlar, ya da ["id1", "id2"]
}
```

### Sistem

```
GET /api/health    Servis durumu
GET /docs          Swagger UI
```

---

## RAG Akışı

```
Doküman Yükleme:
  Dosya → Metin çıkarma → Chunking (500 token, %20 overlap)
        → Google Embedding → ChromaDB

Sorgulama:
  Soru → Google Embedding → ChromaDB similarity search (top-5)
       → Prompt template → Groq LLM → Streaming cevap + kaynaklar
```

---

## Ortam Değişkenleri

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `GROQ_API_KEY` | — | Groq API anahtarı (zorunlu) |
| `GOOGLE_API_KEY` | — | Google AI anahtarı (zorunlu) |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | ChromaDB klasörü |
| `CHUNK_SIZE` | `500` | Chunk büyüklüğü (token) |
| `CHUNK_OVERLAP` | `100` | Chunk örtüşme miktarı |
| `TOP_K_RESULTS` | `5` | Kaç chunk getirilsin |
| `MAX_FILE_SIZE_MB` | `50` | Maksimum dosya boyutu |

---

## Ekip Çalışması

- **Kişi 1 (Backend/RAG):** `backend/services/` — parser, vector_store, llm
- **Kişi 2 (API):** `backend/api/` — chat, documents, health endpoint'leri
- **Kişi 3 (Frontend):** `frontend/src/` — bileşenler, hooks, CSS

Her kişi kendi feature branch'inde çalışır, PR ile `dev`'e merge eder.

---

## Lisans

MIT
=======
# DOCUCHAT
