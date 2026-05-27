import { useState, useEffect, useRef, type FormEvent } from 'react'
import { ChatMessage } from './ChatMessage'
import { streamAgent } from '../api/client'
import type { ChatMessage as ChatMsg } from '../types'

export function AgentView() {
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

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

    streamAgent(
      question,
      token => setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: m.content + token } : m)),
      () => { setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, isStreaming: false } : m)); setIsStreaming(false) },
      err => { setError(err); setIsStreaming(false); setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, isStreaming: false } : m)) }
    )
  }

  return (
    <div className="notebook">
      <div className="notebook-header">
        <div className="notebook-title">
          <span className="notebook-doc-name">Agent</span>
          <span className="agent-badge">ReAct</span>
        </div>
        <p className="agent-hint">Uses RAG, calculator, and web search tools.</p>
      </div>

      <div className="chat-history">
        {messages.length === 0 && (
          <div className="chat-empty"><p>Ask the agent anything — it can search documents, calculate, and look things up.</p></div>
        )}
        {messages.map(msg => <ChatMessage key={msg.id} {...msg} />)}
        <div ref={bottomRef} />
      </div>

      {error && <p className="chat-error">{error}</p>}

      <form className="chat-form" onSubmit={handleSubmit}>
        <input className="chat-input" type="text" placeholder="Ask the agent…"
          value={input} onChange={e => setInput(e.target.value)} disabled={isStreaming} />
        <button type="submit" className="btn-primary chat-send" disabled={isStreaming || !input.trim()}>
          {isStreaming ? '…' : 'Send'}
        </button>
      </form>
    </div>
  )
}