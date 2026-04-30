import { useState, useEffect, useRef, useCallback } from 'react'
import { BookOpen, Trash2 } from 'lucide-react'
import Sidebar from './components/Sidebar'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import { useDocuments } from './hooks/useDocuments'
import { useChat } from './hooks/useChat'
import { systemApi } from './services/api'
import './styles/global.css'

// ── Toast yardımcısı ──────────────────────────────────────────────────────────
function Toast({ toast }) {
  if (!toast) return null
  return <div className={`toast ${toast.type}`}>{toast.msg}</div>
}

// ── Welcome ekranı ────────────────────────────────────────────────────────────
function Welcome({ hasDocuments, onHint }) {
  if (hasDocuments) return null
  return (
    <div className="welcome">
      <BookOpen size={36} style={{ color: 'var(--accent)', opacity: 0.7 }} />
      <h1 className="welcome-title">
        Dokümanlarınla <span>Sohbet Et</span>
      </h1>
      <p className="welcome-sub">
        Sol panelden PDF, DOCX veya TXT yükle.
        Yapay zeka yalnızca senin dokümanlarına dayanarak cevap üretir.
      </p>
      <div className="welcome-hints">
        {['Bu dokümanı özetle', 'Ana başlıkları listele', 'Önemli noktalar neler?'].map((h) => (
          <button key={h} className="welcome-hint" onClick={() => onHint(h)}>{h}</button>
        ))}
      </div>
    </div>
  )
}

// ── Ana uygulama ──────────────────────────────────────────────────────────────
export default function App() {
  const { documents, uploading, loading, error: docError, upload, remove } = useDocuments()
  const { messages, streaming, sendMessage, clearMessages } = useChat()

  const [selectedIds, setSelectedIds] = useState([])   // Seçili doküman filtresi
  const [health, setHealth] = useState(null)            // { ok, groq, google }
  const [toast, setToast] = useState(null)
  const messagesEndRef = useRef(null)

  // Sağlık kontrolü (her 30s)
  useEffect(() => {
    const check = async () => {
      try {
        const h = await systemApi.health()
        setHealth({ ok: h.status === 'ok', groq: h.groq_connected, google: h.google_connected })
      } catch {
        setHealth({ ok: false, groq: false, google: false })
      }
    }
    check()
    const id = setInterval(check, 30000)
    return () => clearInterval(id)
  }, [])

  // Yeni mesajda aşağı kaydır
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Toast göster
  const showToast = useCallback((msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }, [])

  // Seçili dokümanlar değişince geçersiz doc_id'leri temizle
  useEffect(() => {
    const ids = documents.map((d) => d.doc_id)
    setSelectedIds((prev) => prev.filter((id) => ids.includes(id)))
  }, [documents])

  // Doküman yükleme
  const handleUpload = async (file) => {
    const result = await upload(file)
    if (result.success) showToast(`"${result.doc.filename}" yüklendi ✓`)
    else showToast(result.error, 'error')
  }

  // Doküman silme
  const handleDelete = async (docId) => {
    const doc = documents.find((d) => d.doc_id === docId)
    const ok = await remove(docId)
    if (ok) showToast(`"${doc?.filename}" silindi`)
    else showToast('Silme başarısız', 'error')
  }

  // Doküman seçimi toggle
  const handleToggleSelect = (docId) => {
    setSelectedIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    )
  }

  // Soru gönder
  const handleSend = (question) => {
    const docIds = selectedIds.length > 0 ? selectedIds : null
    sendMessage(question, docIds)
  }

  const hasDocuments = documents.length > 0
  const activeFilter = selectedIds.length > 0
    ? documents.filter((d) => selectedIds.includes(d.doc_id)).map((d) => d.filename)
    : null

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <span className="header-logo">Docu<span>Chat</span></span>
        <span className="header-badge">RAG · v1.0</span>
        <div className="header-spacer" />
        {health && (
          <>
            <div
              className={`status-dot ${health.ok ? 'ok' : 'error'}`}
              title={health.ok ? 'Tüm servisler çalışıyor' : 'Servis sorunu var'}
            />
            <span className="status-label">{health.ok ? 'Hazır' : 'Sorun var'}</span>
          </>
        )}
        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            title="Sohbeti temizle"
            style={{
              marginLeft: 12, background: 'none', border: '1px solid var(--border)',
              color: 'var(--text3)', cursor: 'pointer', borderRadius: 6,
              padding: '4px 10px', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4,
              transition: 'all 0.18s'
            }}
          >
            <Trash2 size={12} /> Temizle
          </button>
        )}
      </header>

      {/* ── Sidebar ── */}
      <Sidebar
        documents={documents}
        uploading={uploading}
        loading={loading}
        selectedIds={selectedIds}
        onToggleSelect={handleToggleSelect}
        onUpload={handleUpload}
        onDelete={handleDelete}
      />

      {/* ── Chat Area ── */}
      <main className="chat-area">
        {/* Filtre çubuğu */}
        {hasDocuments && (
          <div className="filter-bar">
            <span className="filter-label">Filtre:</span>
            <button
              className={`filter-chip${selectedIds.length === 0 ? ' active' : ''}`}
              onClick={() => setSelectedIds([])}
            >
              Tüm dokümanlar
            </button>
            {documents.map((doc) => (
              <button
                key={doc.doc_id}
                className={`filter-chip${selectedIds.includes(doc.doc_id) ? ' active' : ''}`}
                onClick={() => handleToggleSelect(doc.doc_id)}
              >
                {doc.filename.length > 22 ? doc.filename.slice(0, 22) + '…' : doc.filename}
              </button>
            ))}
          </div>
        )}

        {/* Mesajlar */}
        <div className="messages">
          {messages.length === 0 ? (
            <Welcome hasDocuments={hasDocuments} onHint={handleSend} />
          ) : (
            messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Giriş çubuğu */}
        <ChatInput
          onSend={handleSend}
          streaming={streaming}
          hasDocuments={hasDocuments}
          onHintClick={hasDocuments ? handleSend : undefined}
        />
      </main>

      <Toast toast={toast} />
    </div>
  )
}
