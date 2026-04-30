import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Trash2, CheckCircle, Loader2 } from 'lucide-react'

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
  'text/plain': ['.txt'],
}

function fileIcon(type) {
  const t = (type || '').toLowerCase()
  if (t === 'pdf')  return 'pdf'
  if (t === 'docx' || t === 'doc') return 'docx'
  return 'txt'
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' })
}

export default function Sidebar({ documents, uploading, loading, selectedIds, onToggleSelect, onUpload, onDelete }) {
  const onDrop = useCallback((acceptedFiles) => {
    acceptedFiles.forEach((file) => onUpload(file))
  }, [onUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    multiple: true,
  })

  return (
    <aside className="sidebar">
      {/* Yükleme alanı */}
      <div className="sidebar-section">
        <div className="sidebar-title">Doküman Yükle</div>
        <div {...getRootProps()} className={`dropzone${isDragActive ? ' active' : ''}`}>
          <input {...getInputProps()} />
          <div className="dropzone-icon">
            <Upload size={22} />
          </div>
          <div className="dropzone-text">
            {isDragActive ? 'Bırak!' : 'Tıkla veya sürükle'}
          </div>
          <div className="dropzone-hint">PDF · DOCX · DOC · TXT</div>
        </div>

        {/* Yükleme ilerlemesi */}
        {uploading && (
          <div className="upload-item">
            <div className="upload-item-name">{uploading.name}</div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${uploading.progress}%` }} />
            </div>
          </div>
        )}
      </div>

      {/* Doküman listesi */}
      <div className="sidebar-section" style={{ paddingBottom: 8 }}>
        <div className="sidebar-title" style={{ marginBottom: 0 }}>
          Dokümanlar
          {documents.length > 0 && (
            <span style={{ marginLeft: 6, color: 'var(--accent)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              {documents.length}
            </span>
          )}
        </div>
        {documents.length > 1 && (
          <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 6 }}>
            Seçerek filtrele • boş = tümü
          </div>
        )}
      </div>

      <div className="doc-list">
        {loading ? (
          <div className="doc-empty">
            <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
          </div>
        ) : documents.length === 0 ? (
          <div className="doc-empty">
            <FileText size={28} style={{ marginBottom: 8, opacity: 0.3 }} />
            <div>Henüz doküman yok</div>
            <div style={{ marginTop: 4, fontSize: 11 }}>Dosya yükleyerek başla</div>
          </div>
        ) : (
          documents.map((doc) => {
            const iconType = fileIcon(doc.file_type)
            const isSelected = selectedIds.includes(doc.doc_id)
            return (
              <div
                key={doc.doc_id}
                className={`doc-item${isSelected ? ' selected' : ''}`}
                onClick={() => onToggleSelect(doc.doc_id)}
                title={doc.filename}
              >
                <div className={`doc-icon ${iconType}`}>{doc.file_type || 'TXT'}</div>
                <div className="doc-info">
                  <div className="doc-name">{doc.filename}</div>
                  <div className="doc-meta">
                    {doc.chunk_count} parça • {formatDate(doc.uploaded_at)}
                  </div>
                </div>
                {isSelected && <CheckCircle size={14} style={{ color: 'var(--accent)', flexShrink: 0 }} />}
                <button
                  className="doc-delete"
                  onClick={(e) => { e.stopPropagation(); onDelete(doc.doc_id) }}
                  title="Sil"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            )
          })
        )}
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </aside>
  )
}
