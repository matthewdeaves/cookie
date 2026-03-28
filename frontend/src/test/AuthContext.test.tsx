import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '../contexts/AuthContext'
import { api } from '../api/client'

vi.mock('../api/client', () => ({
  api: {
    auth: {
      me: vi.fn(),
      logout: vi.fn(),
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
      user: { id: 1, is_admin: true },
      profile: { id: 1, name: 'matt', avatar_color: '#d97850', theme: 'dark', unit_preference: 'metric' },
    })

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.user?.is_admin).toBe(true)
    expect(result.current.isAdmin).toBe(true)
    expect(result.current.profile?.name).toBe('matt')
  })

  it('logout clears state', async () => {
    vi.mocked(api.auth.me).mockResolvedValue({
      user: { id: 1, is_admin: true },
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
})
