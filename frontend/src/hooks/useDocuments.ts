import { useState, useEffect, useCallback } from 'react'
import type { Document } from '../types'
import { getDocuments, deleteDocument } from '../api/client'

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      setDocuments(await getDocuments())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { void refresh() }, [refresh])

  const remove = useCallback(async (id: number) => {
    await deleteDocument(id)
    setDocuments(prev => prev.filter(d => d.id !== id))
  }, [])

  const add = useCallback((doc: Document) => {
    setDocuments(prev => [doc, ...prev])
  }, [])

  return { documents, isLoading, error, refresh, remove, add }
}