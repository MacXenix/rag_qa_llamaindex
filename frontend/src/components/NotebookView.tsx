import { useState, useEffect, useRef, type FormEvent } from 'react'
import { ChatMessage } from './ChatMessage'
import { streamChat } from '../api/client'
import type { Document, ChatMessage as ChatMsg, RetrievalMode, Citation } from '../types'

interface NotebookViewProps {
  document: Document
}

const MODES: RetrievalMode[] = ['basic', 'hyde', 'rerank', 'hyde+rerank', 'multiquery']

export function NotebookView({ document }: NotebookViewProps) {
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [mode, setMode] = useState<RetrievalMode>('basic')
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { setMessages([]); setError(null) }, [document.id])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const question = input.trim()
    if (!question || isStreaming) return

    setInput(''); setError(null); setIsStreaming(true)

    const assistantId = crypto.randomUUID()
    setMessages(prev => [
      ...prev,
      { id: crypto.randomUUID(), role: 'user', content: question },
      { id: assistantId, role: 'assistant', content: '', isStreaming: true },
    ])

    streamChat(
      document.id, question, mode,
      token => setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: m.content + token } : m)),
      (citations: Citation[]) => setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, citations } : m)),
      () => { setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, isStreaming: false } : m)); setIsStreaming(false) },
      err => { setError(err); setIsStreaming(false); setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, isStreaming: false } : m)) }
    )
  }

  return (
    <div className="notebook">
      <div className="notebook-header">
        <span className="notebook-doc-name">{document.filename}</span>
        <div className="mode-selector">
          <label htmlFor="mode-select" className="mode-label">Retrieval:</label>
          <select id="mode-select" className="mode-select" value={mode} onChange={e => setMode(e.target.value as RetrievalMode)}>
            {MODES.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
      </div>

      <div className="chat-history">
        {messages.length === 0 && (
          <div className="chat-empty"><p>Ask a question about <strong>{document.filename}</strong></p></div>
        )}
        {messages.map(msg => <ChatMessage key={msg.id} {...msg} />)}
        <div ref={bottomRef} />
      </div>

      {error && <p className="chat-error">{error}</p>}

      <form className="chat-form" onSubmit={handleSubmit}>
        <input className="chat-input" type="text" placeholder={`Ask about ${document.filename}…`}
          value={input} onChange={e => setInput(e.target.value)} disabled={isStreaming} />
        <button type="submit" className="btn-primary chat-send" disabled={isStreaming || !input.trim()}>
          {isStreaming ? '…' : 'Send'}
        </button>
      </form>
    </div>
  )
}