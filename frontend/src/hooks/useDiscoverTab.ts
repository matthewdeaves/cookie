import { useState, useRef, useEffect, useCallback } from 'react'
import { api, type DiscoverSuggestion } from '../api/client'
import { handleQuotaError, extractQuotaResetsAt } from '../lib/utils'
import { useAIStatus } from '../contexts/AIStatusContext'

interface UseDiscoverTabOptions {
  profileId: number | undefined
  aiAvailable: boolean
}

interface UseDiscoverTabResult {
  suggestions: DiscoverSuggestion[]
  loading: boolean
  error: boolean
  load: (refresh?: boolean) => void
  loadIfEmpty: () => void
}

export function useDiscoverTab({ profileId, aiAvailable }: UseDiscoverTabOptions): UseDiscoverTabResult {
  const { setFeatureQuotaExhausted } = useAIStatus()
  const [suggestions, setSuggestions] = useState<DiscoverSuggestion[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  const load = useCallback(async (refresh = false) => {
    if (!profileId) return
    setLoading(true)
    setError(false)
    try {
      const result = await api.ai.discover(profileId, refresh)
      if (!mountedRef.current) return
      setSuggestions(result.suggestions)
    } catch (err) {
      if (!mountedRef.current) return
      const isAbort =
        err instanceof Error &&
        (err.name === 'AbortError' || err.message.includes('abort'))
      if (isAbort) {
        console.debug('Discover fetch aborted:', err)
      } else if (handleQuotaError(err, 'Failed to load discover suggestions')) {
        setFeatureQuotaExhausted('discover', extractQuotaResetsAt(err))
      } else {
        setError(true)
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false)
      }
    }
  }, [profileId, setFeatureQuotaExhausted])

  const loadIfEmpty = useCallback(() => {
    if (suggestions.length === 0 && !loading && !error && aiAvailable) {
      load()
    }
  }, [suggestions.length, loading, error, aiAvailable, load])

  return { suggestions, loading, error, load, loadIfEmpty }
}
