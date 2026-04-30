/**
 * Chat state yönetimi.
 * Mesajları, streaming durumunu ve kaynak bilgilerini yönetir.
 */
import { useState, useCallback, useRef } from 'react'
import { chatApi } from '../services/api'

export function useChat() {
  const [messages, setMessages] = useState([])
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(false)

  const sendMessage = useCallback(async (question, docIds = null) => {
    if (!question.trim() || streaming) return

    setError(null)
    abortRef.current = false

    // Kullanıcı mesajını ekle
    const userMsg = { id: Date.now(), role: 'user', content: question }
    setMessages((prev) => [...prev, userMsg])

    // Boş AI mesajı — streaming ile doldurulacak
    const aiId = Date.now() + 1
    setMessages((prev) => [
      ...prev,
      { id: aiId, role: 'ai', content: '', sources: [], streaming: true },
    ])

    setStreaming(true)

    await chatApi.stream(
      question,
      docIds,
      // onToken: her token geldiğinde bubble'a ekle
      (token) => {
        if (abortRef.current) return
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiId ? { ...m, content: m.content + token } : m
          )
        )
      },
      // onSources: kaynaklar geldiğinde kaydet
      (sources) => {
        setMessages((prev) =>
          prev.map((m) => (m.id === aiId ? { ...m, sources } : m))
        )
      },
      // onDone: streaming bitti
      () => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiId ? { ...m, streaming: false } : m
          )
        )
        setStreaming(false)
      },
      // onError: hata
      (errMsg) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiId
              ? { ...m, content: `Hata: ${errMsg}`, streaming: false, isError: true }
              : m
          )
        )
        setStreaming(false)
        setError(errMsg)
      }
    )
  }, [streaming])

  const clearMessages = useCallback(() => {
    abortRef.current = true
    setMessages([])
    setStreaming(false)
    setError(null)
  }, [])

  return { messages, streaming, error, sendMessage, clearMessages }
}
