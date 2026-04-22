import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { api, AIStatus } from '../api/client'

interface AIStatusContextType {
  available: boolean
  configured: boolean
  valid: boolean
  error: string | null
  errorCode: string | null
  loading: boolean
  refresh: () => Promise<void>
  setFeatureQuotaExhausted: (feature: string) => void
  isFeatureAvailable: (feature: string) => boolean
}

const defaultStatus: AIStatusContextType = {
  available: false,
  configured: false,
  valid: false,
  error: null,
  errorCode: null,
  loading: true,
  refresh: async () => {},
  setFeatureQuotaExhausted: () => {},
  isFeatureAvailable: () => false,
}

const AIStatusContext = createContext<AIStatusContextType>(defaultStatus)

// eslint-disable-next-line react-refresh/only-export-components -- Hook is tightly coupled to provider
export function useAIStatus() {
  return useContext(AIStatusContext)
}

interface AIStatusProviderProps {
  children: ReactNode
}

export function AIStatusProvider({ children }: AIStatusProviderProps) {
  const [status, setStatus] = useState<Omit<AIStatusContextType, 'refresh' | 'loading' | 'setFeatureQuotaExhausted' | 'isFeatureAvailable'>>({
    available: false,
    configured: false,
    valid: false,
    error: null,
    errorCode: null,
  })
  const [loading, setLoading] = useState(true)
  const [quotaExhaustedFeatures, setQuotaExhaustedFeatures] = useState<Set<string>>(new Set())

  const setFeatureQuotaExhausted = useCallback((feature: string) => {
    setQuotaExhaustedFeatures(prev => new Set([...prev, feature]))
  }, [])

  const isFeatureAvailable = useCallback((feature: string): boolean => {
    return status.available && !quotaExhaustedFeatures.has(feature)
  }, [status.available, quotaExhaustedFeatures])

  const refresh = useCallback(async () => {
    try {
      const data: AIStatus = await api.ai.status()
      setStatus({
        available: data.available,
        configured: data.configured,
        valid: data.valid,
        error: data.error,
        errorCode: data.error_code,
      })
    } catch (error) {
      console.error('Failed to fetch AI status:', error)
      setStatus({
        available: false,
        configured: false,
        valid: false,
        error: 'Failed to check AI availability',
        errorCode: 'connection_error',
      })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    const doRefresh = async () => {
      try {
        const data: AIStatus = await api.ai.status()
        if (!cancelled) {
          setStatus({
            available: data.available,
            configured: data.configured,
            valid: data.valid,
            error: data.error,
            errorCode: data.error_code,
          })
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to fetch AI status:', error)
          setStatus({
            available: false,
            configured: false,
            valid: false,
            error: 'Failed to check AI availability',
            errorCode: 'connection_error',
          })
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    doRefresh()
    // Refresh every 5 minutes
    const interval = setInterval(doRefresh, 5 * 60 * 1000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [])

  return (
    <AIStatusContext.Provider value={{ ...status, loading, refresh, setFeatureQuotaExhausted, isFeatureAvailable }}>
      {children}
    </AIStatusContext.Provider>
  )
}
