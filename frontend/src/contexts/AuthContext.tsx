import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { api, type AuthSettings, type Profile } from '../api/client'

interface AuthContextType {
  settings: AuthSettings | null
  isPublicMode: boolean
  isAuthenticated: boolean
  isAdmin: boolean
  currentUser: Profile | null
  loading: boolean
  login: (username: string, password: string) => Promise<Profile>
  register: (username: string, password: string, passwordConfirm: string, avatarColor: string) => Promise<Profile>
  logout: () => Promise<void>
  setCurrentUser: (user: Profile | null) => void
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

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [settings, setSettings] = useState<AuthSettings | null>(null)
  const [currentUser, setCurrentUser] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)

  // Fetch auth settings on mount
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const authSettings = await api.system.authSettings()
        setSettings(authSettings)
      } catch (error) {
        console.error('Failed to fetch auth settings:', error)
        // Default to home mode if settings fetch fails (home mode = everyone is admin)
        setSettings({
          deployment_mode: 'home',
          allow_registration: true,
          instance_name: 'Cookie',
          is_admin: true,
          env_overrides: {
            deployment_mode: false,
            allow_registration: false,
            instance_name: false,
          },
        })
      } finally {
        setLoading(false)
      }
    }
    fetchSettings()
  }, [])

  const isPublicMode = settings?.deployment_mode === 'public'
  const isAuthenticated = currentUser !== null
  const isAdmin = settings?.is_admin ?? false

  const login = useCallback(async (username: string, password: string): Promise<Profile> => {
    const profile = await api.auth.login(username, password)
    if (profile) {
      setCurrentUser(profile)
      return profile
    }
    throw new Error('Login failed')
  }, [])

  const register = useCallback(
    async (username: string, password: string, passwordConfirm: string, avatarColor: string): Promise<Profile> => {
      const profile = await api.auth.register(username, password, passwordConfirm, avatarColor)
      if (profile) {
        setCurrentUser(profile)
        return profile
      }
      throw new Error('Registration failed')
    },
    []
  )

  const logout = useCallback(async () => {
    await api.auth.logout()
    setCurrentUser(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        settings,
        isPublicMode,
        isAuthenticated,
        isAdmin,
        currentUser,
        loading,
        login,
        register,
        logout,
        setCurrentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
