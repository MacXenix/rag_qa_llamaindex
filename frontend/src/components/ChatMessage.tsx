import { useState } from 'react'
import type { Citation } from '../types'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  isStreaming?: boolean
}

export function ChatMessage({ role, content, citations, isStreaming }: ChatMessageProps) {
  const [showCitations, setShowCitations] = useState(false)

  return (
    <div className={`message message-${role}`}>
      <div className="message-bubble">
        <p className="message-content">
          {content}
          {isStreaming && <span className="cursor" aria-hidden="true" />}
        </p>
      </div>

      {citations && citations.length > 0 && (
        <div className="citations">
          <button className="citations-toggle" onClick={() => setShowCitations(v => !v)}>
            {showCitations ? '▾' : '▸'} {citations.length} source{citations.length > 1 ? 's' : ''}
          </button>
          {showCitations && (
            <ul className="citations-list">
              {citations.map((c, i) => (
                <li key={i} className="citation">
                  <div className="citation-meta">
                    <span className="citation-source">{c.source}{c.page ? ` · p.${c.page}` : ''}</span>
                    <span className="citation-score">{(c.score * 100).toFixed(0)}%</span>
                  </div>
                  <p className="citation-text">{c.text}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}