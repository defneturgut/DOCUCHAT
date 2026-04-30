/**
 * Doküman yükleme ve listeleme için custom hook.
 * Upload, liste çekme, silme işlemlerini yönetir.
 */
import { useState, useEffect, useCallback } from 'react'
import { documentsApi } from '../services/api'

export function useDocuments() {
  const [documents, setDocuments] = useState([])
  const [uploading, setUploading] = useState(null) // { name, progress }
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Listeyi sunucudan çek
  const fetchDocuments = useCallback(async () => {
    try {
      const data = await documentsApi.list()
      setDocuments(data.documents)
    } catch (e) {
      setError('Dokümanlar yüklenemedi.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchDocuments() }, [fetchDocuments])

  // Dosya yükle
  const upload = useCallback(async (file) => {
    setUploading({ name: file.name, progress: 0 })
    setError(null)
    try {
      const doc = await documentsApi.upload(file, (progress) => {
        setUploading((prev) => ({ ...prev, progress }))
      })
      setDocuments((prev) => [doc, ...prev])
      return { success: true, doc }
    } catch (e) {
      const msg = e.response?.data?.detail || 'Yükleme başarısız.'
      setError(msg)
      return { success: false, error: msg }
    } finally {
      setUploading(null)
    }
  }, [])

  // Doküman sil
  const remove = useCallback(async (docId) => {
    try {
      await documentsApi.delete(docId)
      setDocuments((prev) => prev.filter((d) => d.doc_id !== docId))
      return true
    } catch (e) {
      setError('Silme başarısız.')
      return false
    }
  }, [])

  return { documents, uploading, loading, error, upload, remove, refresh: fetchDocuments }
}
