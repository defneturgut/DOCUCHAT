/**
 * DocuChat API servisi
 * Tüm backend iletişimi buradan geçer.
 */
import axios from 'axios'

const BASE = '/api'

const api = axios.create({
  baseURL: BASE,
  timeout: 60000,
})

// ─── Doküman API'leri ─────────────────────────────────────────────────────────

export const documentsApi = {
  /** Doküman yükle */
  upload: async (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
      },
    })
    return data
  },

  /** Tüm dokümanları listele */
  list: async () => {
    const { data } = await api.get('/documents')
    return data
  },

  /** Dokümanı sil */
  delete: async (docId) => {
    const { data } = await api.delete(`/documents/${docId}`)
    return data
  },
}

// ─── Chat API'leri ────────────────────────────────────────────────────────────

export const chatApi = {
  /** Normal (tam) cevap */
  send: async (question, docIds = null) => {
    const { data } = await api.post('/chat', { question, doc_ids: docIds })
    return data
  },

  /**
   * Streaming cevap — SSE (Server-Sent Events)
   * @param {string} question
   * @param {string[]|null} docIds
   * @param {(token: string) => void} onToken
   * @param {(sources: object[]) => void} onSources
   * @param {() => void} onDone
   * @param {(err: string) => void} onError
   */
  stream: async (question, docIds, onToken, onSources, onDone, onError) => {
    const response = await fetch(`${BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, doc_ids: docIds }),
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Sunucu hatası' }))
      onError(err.detail || 'Bilinmeyen hata')
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() // Tamamlanmamış satırı sakla

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const event = JSON.parse(line.slice(6))
          if (event.type === 'sources') onSources(event.data)
          else if (event.type === 'token')  onToken(event.data)
          else if (event.type === 'done')   onDone()
          else if (event.type === 'error')  onError(event.data)
        } catch {
          // Malformed JSON — atla
        }
      }
    }
  },
}

// ─── Sistem API'leri ──────────────────────────────────────────────────────────

export const systemApi = {
  health: async () => {
    const { data } = await api.get('/health')
    return data
  },
}
