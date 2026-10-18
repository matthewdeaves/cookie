import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { toast } from 'sonner'
import { api } from '../api/client'
import { SESSION_LOST_EVENT } from '../api/request'
import type { AuthProfile, PasskeyUser } from '../api/types'

interface AuthContextType {
  user: PasskeyUser | null
  profile: AuthProfile | null
  isLoading: boolean
  logout: () => Promise<void>
  refreshSession: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

// eslint-disable-next-line react-refresh/only-export-components -- Hook is tightly coupled to provider
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// eslint-disable-next-line react-refresh/only-export-components -- Safe variant for mode-conditional usage
export function useOptionalAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<PasskeyUser | null>(null)
  const [profile, setProfile] = useState<AuthProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Restore session on mount
  useEffect(() => {
    api.auth
      .me()
      .then((data) => {
        setUser(data.user)
        setProfile(data.profile)
      })
      .catch(() => {
        // Not logged in
      })
      .finally(() => setIsLoading(false))
  }, [])

  // The passkey session expired mid-use: drop to the login screen instead of
  // leaving every action on the page failing with 401.
  const signedIn = user !== null
  useEffect(() => {
    if (!signedIn) return
    const onSessionLost = () => {
      toast.error('Your session expired. Please sign in again.')
      setUser(null)
      setProfile(null)
    }
    window.addEventListener(SESSION_LOST_EVENT, onSessionLost)
    return () => window.removeEventListener(SESSION_LOST_EVENT, onSessionLost)
  }, [signedIn])

  const refreshSession = useCallback(async () => {
    try {
      const data = await api.auth.me()
      setUser(data.user)
      setProfile(data.profile)
    } catch {
      setUser(null)
      setProfile(null)
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.auth.logout()
    } catch {
      // Ignore errors on logout
    }
    setUser(null)
    setProfile(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        isLoading,
        logout,
        refreshSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
