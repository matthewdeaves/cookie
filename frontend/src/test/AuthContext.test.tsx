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
  })

  it('restores session from /api/auth/me/', async () => {
    // Spec 014-remove-is-staff: /auth/me no longer exposes is_admin.
    vi.mocked(api.auth.me).mockResolvedValue({
      user: { id: 1 },
      profile: { id: 1, name: 'matt', avatar_color: '#d97850', theme: 'dark', unit_preference: 'metric' },
    })

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.user?.id).toBe(1)
    expect(result.current.profile?.name).toBe('matt')
  })

  it('logout clears state', async () => {
    vi.mocked(api.auth.me).mockResolvedValue({
      user: { id: 1 },
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
