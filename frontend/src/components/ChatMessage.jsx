import ReactMarkdown from 'react-markdown'
import { Bot, User } from 'lucide-react'

function scoreClass(score) {
  if (score >= 0.75) return 'high'
  if (score >= 0.5)  return 'mid'
  return 'low'
}

function SourceList({ sources }) {
  if (!sources || sources.length === 0) return null
  return (
    <div className="sources">
      <div className="sources-label">Kaynaklar</div>
      {sources.map((src, i) => (
        <div key={i} className="source-chip">
          <span className={`source-score ${scoreClass(src.relevance_score)}`}>
            {Math.round(src.relevance_score * 100)}%
          </span>
          <div>
            <div className="source-file">{src.filename}</div>
            <div className="source-text">{src.chunk_text}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function ThinkingDots() {
  return (
    <div className="thinking">
      <div className="thinking-dots">
        <span /><span /><span />
      </div>
      <span>Yanıt üretiliyor</span>
    </div>
  )
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const isEmpty = !message.content && message.streaming

  return (
    <div className={`message ${message.role}`}>
      <div className={`avatar ${message.role}`}>
        {isUser ? <User size={15} /> : <Bot size={15} />}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className={`bubble${message.isError ? ' error-bubble' : ''}`}>
          {isEmpty ? (
            <ThinkingDots />
          ) : (
            <>
              <ReactMarkdown>{message.content}</ReactMarkdown>
              {message.streaming && <span className="cursor" />}
            </>
          )}
        </div>
        {/* Kaynakları sadece AI mesajında ve streaming bitince göster */}
        {!isUser && !message.streaming && message.sources?.length > 0 && (
          <SourceList sources={message.sources} />
        )}
      </div>

      <style>{`
        .error-bubble { border-color: rgba(248,113,113,0.3) !important; }
      `}</style>
    </div>
  )
}
