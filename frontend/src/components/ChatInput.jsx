import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'

const HINTS = [
  'Bu dokümanı özetle',
  'Ana başlıkları listele',
  'En önemli noktalar neler?',
  'Sonuç bölümünü açıkla',
]

export default function ChatInput({ onSend, streaming, hasDocuments, onHintClick }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  // Textarea otomatik yükseklik
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [value])

  const handleSend = () => {
    const q = value.trim()
    if (!q || streaming || !hasDocuments) return
    onSend(q)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="input-bar">
      <div className="input-wrap">
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKey}
          placeholder={
            hasDocuments
              ? 'Dokümanlar hakkında bir şey sor… (Enter = gönder, Shift+Enter = yeni satır)'
              : 'Önce sol panelden doküman yükleyin'
          }
          disabled={!hasDocuments || streaming}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={!value.trim() || streaming || !hasDocuments}
          title="Gönder"
        >
          <Send size={15} />
        </button>
      </div>

      {/* Hint butonları — boş ekranda göster */}
      {hasDocuments && onHintClick && (
        <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginTop: 8, flexWrap: 'wrap' }}>
          {HINTS.map((hint) => (
            <button
              key={hint}
              className="welcome-hint"
              style={{ fontSize: 12, padding: '5px 12px' }}
              onClick={() => onHintClick(hint)}
              disabled={streaming}
            >
              {hint}
            </button>
          ))}
        </div>
      )}

      <div className="input-hint">
        Groq llama-3.3-70b · Google text-embedding-004 · ChromaDB
      </div>
    </div>
  )
}
