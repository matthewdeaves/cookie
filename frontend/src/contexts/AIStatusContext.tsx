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
}

const defaultStatus: AIStatusContextType = {
  available: false,
  configured: false,
  valid: false,
  error: null,
  errorCode: null,
  loading: true,
  refresh: async () => {},
}

const AIStatusContext = createContext<AIStatusContextType>(defaultStatus)

export function useAIStatus() {
  return useContext(AIStatusContext)
}

interface AIStatusProviderProps {
  children: ReactNode
}

export function AIStatusProvider({ children }: AIStatusProviderProps) {
  const [status, setStatus] = useState<Omit<AIStatusContextType, 'refresh' | 'loading'>>({
    available: false,
    configured: false,
    valid: false,
    error: null,
    errorCode: null,
  })
  const [loading, setLoading] = useState(true)

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
    refresh()
    // Refresh every 5 minutes
    const interval = setInterval(refresh, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [refresh])

  return (
    <AIStatusContext.Provider value={{ ...status, loading, refresh }}>
      {children}
    </AIStatusContext.Provider>
  )
}
