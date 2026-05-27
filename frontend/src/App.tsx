import { useState } from 'react'
import { DocumentSidebar } from './components/DocumentSidebar'
import { UploadModal } from './components/UploadModal'
import { NotebookView } from './components/NotebookView'
import { AgentView } from './components/AgentView'
import { useDocuments } from './hooks/useDocuments'
import type { Document, AppTab } from './types'
import './App.css'

export default function App() {
  const { documents, isLoading, remove, add } = useDocuments()
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null)
  const [activeTab, setActiveTab] = useState<AppTab>('notebook')
  const [showUpload, setShowUpload] = useState(false)

  async function handleDelete(id: number) {
    await remove(id)
    if (selectedDoc?.id === id) setSelectedDoc(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-logo">
          <span>🧠</span>
          <span className="logo-text">RAG-QA</span>
        </div>
        <nav className="app-tabs">
          <button className={`tab-btn ${activeTab === 'notebook' ? 'active' : ''}`} onClick={() => setActiveTab('notebook')}>Notebook</button>
          <button className={`tab-btn ${activeTab === 'agent' ? 'active' : ''}`} onClick={() => setActiveTab('agent')}>Agent</button>
        </nav>
      </header>

      <div className="app-body">
        <DocumentSidebar
          documents={documents} selectedId={selectedDoc?.id ?? null}
          isLoading={isLoading} onSelect={setSelectedDoc}
          onDelete={id => void handleDelete(id)}
          onUploadClick={() => setShowUpload(true)}
        />

        <main className="main">
          {activeTab === 'notebook' ? (
            selectedDoc
              ? <NotebookView document={selectedDoc} />
              : (
                <div className="empty-state">
                  <span className="empty-icon">📂</span>
                  <p>Select a document from the sidebar to start chatting</p>
                  <button className="btn-primary" onClick={() => setShowUpload(true)}>Upload your first document</button>
                </div>
              )
          ) : (
            <AgentView />
          )}
        </main>
      </div>

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onUploaded={doc => { add(doc); setSelectedDoc(doc); setActiveTab('notebook') }}
        />
      )}
    </div>
  )
}