import type { Document } from '../types'

interface DocumentSidebarProps {
  documents: Document[]
  selectedId: number | null
  isLoading: boolean
  onSelect: (doc: Document) => void
  onDelete: (id: number) => void
  onUploadClick: () => void
}

const FILE_ICONS: Record<string, string> = {
  pdf: '📄', docx: '📝', pptx: '📊', txt: '📃', md: '📋', url: '🔗',
}

export function DocumentSidebar({ documents, selectedId, isLoading, onSelect, onDelete, onUploadClick }: DocumentSidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Documents</h2>
        <button className="btn-icon" onClick={onUploadClick} title="Add document">+</button>
      </div>

      {isLoading && <p className="sidebar-empty">Loading…</p>}
      {!isLoading && documents.length === 0 && (
        <p className="sidebar-empty">No documents yet.</p>
      )}

      <ul className="doc-list">
        {documents.map(doc => (
          <li
            key={doc.id}
            className={`doc-item ${selectedId === doc.id ? 'selected' : ''}`}
            onClick={() => onSelect(doc)}
          >
            <span className="doc-icon">{FILE_ICONS[doc.file_type.toLowerCase()] ?? '📄'}</span>
            <span className="doc-name">{doc.filename}</span>
            <button
              className="doc-delete"
              onClick={e => { e.stopPropagation(); onDelete(doc.id) }}
              title="Delete" aria-label={`Delete ${doc.filename}`}
            >×</button>
          </li>
        ))}
      </ul>

      <button className="sidebar-upload-btn" onClick={onUploadClick}>+ Add Document</button>
    </aside>
  )
}