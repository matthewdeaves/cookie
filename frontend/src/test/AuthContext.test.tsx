import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '../contexts/AuthContext'
import { api } from '../api/client'

vi.mock('../api/client', () => ({
  api: {
    auth: {
      me: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
    },
  },
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('starts in loading state and resolves', async () => {
    vi.mocked(api.auth.me).mockRejectedValue(new Error('Not logged in'))

    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.user).toBeNull()
    expect(result.current.profile).toBeNull()
    expect(result.current.isAdmin).toBe(false)
  })

  it('restores session from /api/auth/me/', async () => {
    vi.mocked(api.auth.me).mockResolvedValue({
      user: { id: 1, username: 'matt', is_admin: true },
      profile: { id: 1, name: 'matt', avatar_color: '#d97850', theme: 'dark', unit_preference: 'metric' },
    })

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.user?.username).toBe('matt')
    expect(result.current.isAdmin).toBe(true)
    expect(result.current.profile?.name).toBe('matt')
  })

  it('login sets user and profile', async () => {
    vi.mocked(api.auth.me).mockRejectedValue(new Error('Not logged in'))
    vi.mocked(api.auth.login).mockResolvedValue({
      user: { id: 1, username: 'alice', is_admin: false },
      profile: { id: 2, name: 'alice', avatar_color: '#8fae6f', theme: 'light', unit_preference: 'imperial' },
    })

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(async () => {
      await result.current.login('alice', 'password123')
    })

    expect(result.current.user?.username).toBe('alice')
    expect(result.current.profile?.name).toBe('alice')
  })

  it('logout clears state', async () => {
    vi.mocked(api.auth.me).mockResolvedValue({
      user: { id: 1, username: 'matt', is_admin: true },
      profile: { id: 1, name: 'matt', avatar_color: '#d97850', theme: 'dark', unit_preference: 'metric' },
    })
    vi.mocked(api.auth.logout).mockResolvedValue({ message: 'ok' })

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => expect(result.current.user).not.toBeNull())

    await act(async () => {
      await result.current.logout()
    })

    expect(result.current.user).toBeNull()
    expect(result.current.profile).toBeNull()
  })

  it('register returns message', async () => {
    vi.mocked(api.auth.me).mockRejectedValue(new Error('Not logged in'))
    vi.mocked(api.auth.register).mockResolvedValue({ message: 'Check your email' })

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    let message: string = ''
    await act(async () => {
      message = await result.current.register({
        username: 'newuser',
        password: 'StrongPass123!',
        password_confirm: 'StrongPass123!',
        email: 'test@example.com',
        privacy_accepted: true,
      })
    })

    expect(message).toBe('Check your email')
  })
})
