import { useState, useRef, type FormEvent, type DragEvent } from 'react'
import type { Document } from '../types'
import { uploadFile, ingestUrl } from '../api/client'

interface UploadModalProps {
  onClose: () => void
  onUploaded: (doc: Document) => void
}

type UploadTab = 'file' | 'url'

export function UploadModal({ onClose, onUploaded }: UploadModalProps) {
  const [tab, setTab] = useState<UploadTab>('file')
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  async function handleFile(file: File) {
    setIsLoading(true); setError(null)
    try { onUploaded(await uploadFile(file)); onClose() }
    catch (err) { setError(err instanceof Error ? err.message : 'Upload failed') }
    finally { setIsLoading(false) }
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault(); setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) void handleFile(file)
  }

  async function onUrlSubmit(e: FormEvent) {
    e.preventDefault()
    if (!url.trim()) return
    setIsLoading(true); setError(null)
    try { onUploaded(await ingestUrl(url.trim())); onClose() }
    catch (err) { setError(err instanceof Error ? err.message : 'URL ingestion failed') }
    finally { setIsLoading(false) }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add Document</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">×</button>
        </div>

        <div className="modal-tabs">
          <button className={`modal-tab ${tab === 'file' ? 'active' : ''}`} onClick={() => setTab('file')}>Upload File</button>
          <button className={`modal-tab ${tab === 'url' ? 'active' : ''}`} onClick={() => setTab('url')}>From URL</button>
        </div>

        {tab === 'file' ? (
          <div
            className={`drop-zone ${isDragging ? 'dragging' : ''}`}
            onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
          >
            <span className="drop-icon">📄</span>
            <p>Drop a file here or click to browse</p>
            <p className="drop-hint">PDF, DOCX, PPTX, TXT, MD — max 50 MB</p>
            <input
              ref={fileRef} type="file" className="hidden"
              accept=".pdf,.docx,.pptx,.txt,.md"
              onChange={e => { const f = e.target.files?.[0]; if (f) void handleFile(f) }}
            />
          </div>
        ) : (
          <form className="url-form" onSubmit={e => void onUrlSubmit(e)}>
            <input
              type="url" className="url-input"
              placeholder="https://example.com/article"
              value={url} onChange={e => setUrl(e.target.value)} required
            />
            <button type="submit" className="btn-primary" disabled={isLoading}>
              {isLoading ? 'Ingesting…' : 'Ingest URL'}
            </button>
          </form>
        )}

        {error && <p className="error-text">{error}</p>}
        {isLoading && <p className="loading-text">Processing…</p>}
      </div>
    </div>
  )
}