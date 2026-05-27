import type { Document, Citation, RetrievalMode } from '../types'

const BASE = '/api'

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : 'Unknown error'
}

// ── Documents ──────────────────────────────────────────────────────────────

export async function getDocuments(): Promise<Document[]> {
  const res = await fetch(`${BASE}/documents`)
  if (!res.ok) throw new Error(`Failed to fetch documents: ${res.statusText}`)
  return res.json() as Promise<Document[]>
}

export async function uploadFile(file: File): Promise<Document> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/documents/upload`, { method: 'POST', body: form })
  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as { detail?: string }
    throw new Error(body.detail ?? 'Upload failed')
  }
  return res.json() as Promise<Document>
}

export async function ingestUrl(url: string): Promise<Document> {
  const res = await fetch(`${BASE}/documents/url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as { detail?: string }
    throw new Error(body.detail ?? 'URL ingestion failed')
  }
  return res.json() as Promise<Document>
}

export async function deleteDocument(id: number): Promise<void> {
  const res = await fetch(`${BASE}/documents/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Delete failed')
}

// ── SSE streaming ──────────────────────────────────────────────────────────

interface SSEChunk {
  token?: string
  citations?: Citation[]
}

async function* streamSSE(url: string, body: object): AsyncGenerator<SSEChunk | null> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok || !res.body) throw new Error(`Stream failed: ${res.statusText}`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6).trim()
        if (data === '[DONE]') { yield null; return }
        try { yield JSON.parse(data) as SSEChunk } catch { /* skip */ }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

export function streamChat(
  documentId: number,
  question: string,
  mode: RetrievalMode,
  onToken: (t: string) => void,
  onCitations: (c: Citation[]) => void,
  onDone: () => void,
  onError: (e: string) => void
): () => void {
  let cancelled = false
  void (async () => {
    try {
      for await (const chunk of streamSSE(`${BASE}/notebooks/${documentId}/chat`, { question, mode })) {
        if (cancelled) break
        if (chunk === null) { onDone(); break }
        if (chunk.token) onToken(chunk.token)
        if (chunk.citations) onCitations(chunk.citations)
      }
    } catch (err) {
      if (!cancelled) onError(errorMessage(err))
    }
  })()
  return () => { cancelled = true }
}

export function streamAgent(
  question: string,
  onToken: (t: string) => void,
  onDone: () => void,
  onError: (e: string) => void
): () => void {
  let cancelled = false
  void (async () => {
    try {
      for await (const chunk of streamSSE(`${BASE}/agent/chat`, { question })) {
        if (cancelled) break
        if (chunk === null) { onDone(); break }
        if (chunk?.token) onToken(chunk.token)
      }
    } catch (err) {
      if (!cancelled) onError(errorMessage(err))
    }
  })()
  return () => { cancelled = true }
}