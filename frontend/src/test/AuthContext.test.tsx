import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { AuthProvider, useAuth } from '../contexts/AuthContext'
import { api } from '../api/client'

// Mock the API
vi.mock('../api/client', () => ({
  api: {
    system: {
      authSettings: vi.fn(),
    },
    auth: {
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    },
    profiles: {
      list: vi.fn(),
    },
  },
}))

const mockAuthSettings = {
  deployment_mode: 'public' as const,
  allow_registration: true,
  instance_name: 'Test Cookie',
  env_overrides: {
    deployment_mode: false,
    allow_registration: false,
    instance_name: false,
  },
}

const mockHomeSettings = {
  deployment_mode: 'home' as const,
  allow_registration: true,
  instance_name: 'Cookie',
  env_overrides: {
    deployment_mode: false,
    allow_registration: false,
    instance_name: false,
  },
}

const mockProfile = {
  id: 1,
  name: 'TestUser',
  avatar_color: '#FF5733',
  theme: 'light',
  unit_preference: 'metric',
}

// Test component that displays auth state
function AuthStateDisplay() {
  const { settings, isPublicMode, isAuthenticated, currentUser, loading } = useAuth()

  if (loading) {
    return <div data-testid="loading">Loading...</div>
  }

  return (
    <div>
      <div data-testid="deployment-mode">{settings?.deployment_mode}</div>
      <div data-testid="is-public-mode">{isPublicMode ? 'true' : 'false'}</div>
      <div data-testid="is-authenticated">{isAuthenticated ? 'true' : 'false'}</div>
      <div data-testid="current-user">{currentUser?.name || 'none'}</div>
      <div data-testid="instance-name">{settings?.instance_name}</div>
    </div>
  )
}

// Test component that can trigger auth actions
function AuthActions() {
  const { login, logout, isAuthenticated, currentUser } = useAuth()

  return (
    <div>
      <div data-testid="is-authenticated">{isAuthenticated ? 'true' : 'false'}</div>
      <div data-testid="current-user">{currentUser?.name || 'none'}</div>
      <button
        data-testid="login-button"
        onClick={() => login('testuser', 'password123')}
      >
        Login
      </button>
      <button data-testid="logout-button" onClick={() => logout()}>
        Logout
      </button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches auth settings on mount', async () => {
    vi.mocked(api.system.authSettings).mockResolvedValue(mockAuthSettings)

    render(
      <AuthProvider>
        <AuthStateDisplay />
      </AuthProvider>
    )

    // Initially loading
    expect(screen.getByTestId('loading')).toBeInTheDocument()

    // After loading
    await waitFor(() => {
      expect(screen.getByTestId('deployment-mode')).toHaveTextContent('public')
    })

    expect(api.system.authSettings).toHaveBeenCalledTimes(1)
  })

  it('provides isPublicMode based on settings', async () => {
    vi.mocked(api.system.authSettings).mockResolvedValue(mockAuthSettings)

    render(
      <AuthProvider>
        <AuthStateDisplay />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('is-public-mode')).toHaveTextContent('true')
    })
  })

  it('provides isPublicMode=false for home mode', async () => {
    vi.mocked(api.system.authSettings).mockResolvedValue(mockHomeSettings)

    render(
      <AuthProvider>
        <AuthStateDisplay />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('is-public-mode')).toHaveTextContent('false')
    })
  })

  it('provides isAuthenticated state', async () => {
    vi.mocked(api.system.authSettings).mockResolvedValue(mockAuthSettings)

    render(
      <AuthProvider>
        <AuthStateDisplay />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
    })
  })

  it('updates state after login', async () => {
    vi.mocked(api.system.authSettings).mockResolvedValue(mockAuthSettings)
    vi.mocked(api.auth.login).mockResolvedValue(mockProfile)

    render(
      <AuthProvider>
        <AuthActions />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
    })

    // Trigger login
    await act(async () => {
      screen.getByTestId('login-button').click()
    })

    await waitFor(() => {
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
      expect(screen.getByTestId('current-user')).toHaveTextContent('TestUser')
    })
  })

  it('clears state after logout', async () => {
    vi.mocked(api.system.authSettings).mockResolvedValue(mockAuthSettings)
    vi.mocked(api.auth.login).mockResolvedValue(mockProfile)
    vi.mocked(api.auth.logout).mockResolvedValue(undefined)

    render(
      <AuthProvider>
        <AuthActions />
      </AuthProvider>
    )

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
    })

    // Login first
    await act(async () => {
      screen.getByTestId('login-button').click()
    })

    await waitFor(() => {
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
    })

    // Then logout
    await act(async () => {
      screen.getByTestId('logout-button').click()
    })

    await waitFor(() => {
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
      expect(screen.getByTestId('current-user')).toHaveTextContent('none')
    })
  })

  it('provides instance name from settings', async () => {
    vi.mocked(api.system.authSettings).mockResolvedValue(mockAuthSettings)

    render(
      <AuthProvider>
        <AuthStateDisplay />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('instance-name')).toHaveTextContent('Test Cookie')
    })
  })

  it('defaults to home mode if settings fetch fails', async () => {
    vi.mocked(api.system.authSettings).mockRejectedValue(new Error('Network error'))

    render(
      <AuthProvider>
        <AuthStateDisplay />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('deployment-mode')).toHaveTextContent('home')
      expect(screen.getByTestId('is-public-mode')).toHaveTextContent('false')
    })
  })
})
