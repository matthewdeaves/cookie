import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { api } from '../api/client'
import type { AuthUser, AuthProfile } from '../api/types'

interface AuthContextType {
  user: AuthUser | null
  profile: AuthProfile | null
  isAdmin: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  register: (data: {
    username: string
    password: string
    password_confirm: string
    email: string
    privacy_accepted: boolean
  }) => Promise<string>
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
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

  const login = useCallback(async (username: string, password: string) => {
    const data = await api.auth.login({ username, password })
    setUser(data.user)
    setProfile(data.profile)
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

  const register = useCallback(
    async (data: {
      username: string
      password: string
      password_confirm: string
      email: string
      privacy_accepted: boolean
    }) => {
      const result = await api.auth.register(data)
      return result.message
    },
    []
  )

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        isAdmin: user?.is_admin ?? false,
        isLoading,
        login,
        logout,
        register,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
