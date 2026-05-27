export interface Document {
  id: number
  filename: string
  file_type: string
  source: string
  chroma_collection: string
  created_at: string
}

export interface Citation {
  text: string
  score: number
  source: string
  page: string | null
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  isStreaming?: boolean
}

export type RetrievalMode = 'basic' | 'hyde' | 'rerank' | 'hyde+rerank'
export type AppTab = 'notebook' | 'agent'