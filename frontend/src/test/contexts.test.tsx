import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { renderHook } from '@testing-library/react'
import { ProfileProvider, useProfile } from '../contexts/ProfileContext'
import { AIStatusProvider, useAIStatus } from '../contexts/AIStatusContext'

// Mock sonner
vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}))

// Mock API client
const mockApiProfilesList = vi.fn(() => Promise.resolve([]))
const mockApiFavoritesList = vi.fn(() => Promise.resolve([]))
const mockApiProfilesSelect = vi.fn(() =>
  Promise.resolve({ id: 1, name: 'Test', avatar_color: '#000', theme: 'light', unit_preference: 'metric' })
)
const mockApiProfilesUpdate = vi.fn(() =>
  Promise.resolve({ id: 1, name: 'Test', avatar_color: '#000', theme: 'dark', unit_preference: 'metric' })
)
const mockApiFavoritesAdd = vi.fn(() => Promise.resolve({ recipe: { id: 1 }, created_at: '' }))
const mockApiFavoritesRemove = vi.fn(() => Promise.resolve(null))
const mockApiAiStatus = vi.fn(() =>
  Promise.resolve({
    available: true,
    configured: true,
    valid: true,
    default_model: 'test-model',
    error: null,
    error_code: null,
  })
)

vi.mock('../api/client', () => ({
  api: {
    profiles: {
      list: (...args: unknown[]) => mockApiProfilesList(...args),
      select: (...args: unknown[]) => mockApiProfilesSelect(...args),
      update: (...args: unknown[]) => mockApiProfilesUpdate(...args),
    },
    favorites: {
      list: (...args: unknown[]) => mockApiFavoritesList(...args),
      add: (...args: unknown[]) => mockApiFavoritesAdd(...args),
      remove: (...args: unknown[]) => mockApiFavoritesRemove(...args),
    },
    ai: {
      status: (...args: unknown[]) => mockApiAiStatus(...args),
    },
  },
}))

describe('ProfileContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('ProfileProvider renders children', async () => {
    render(
      <ProfileProvider>
        <div>Child Content</div>
      </ProfileProvider>
    )
    await waitFor(() => {
      expect(screen.getByText('Child Content')).toBeInTheDocument()
    })
  })

  it('useProfile throws when used outside provider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => {
      renderHook(() => useProfile())
    }).toThrow('useProfile must be used within a ProfileProvider')
    spy.mockRestore()
  })

  it('provides default values (null profile, light theme)', async () => {
    function TestConsumer() {
      const { profile, theme, loading } = useProfile()
      return (
        <div>
          <span data-testid="profile">{profile ? profile.name : 'none'}</span>
          <span data-testid="theme">{theme}</span>
          <span data-testid="loading">{String(loading)}</span>
        </div>
      )
    }

    render(
      <ProfileProvider>
        <TestConsumer />
      </ProfileProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false')
    })
    expect(screen.getByTestId('profile').textContent).toBe('none')
    expect(screen.getByTestId('theme').textContent).toBe('light')
  })

  it('selectProfile updates profile and calls API', async () => {
    function TestConsumer() {
      const { profile, selectProfile } = useProfile()
      return (
        <div>
          <span data-testid="profile">{profile ? profile.name : 'none'}</span>
          <button onClick={() => selectProfile({ id: 1, name: 'Alice', avatar_color: '#000', theme: 'dark', unit_preference: 'metric' })}>
            Select
          </button>
        </div>
      )
    }

    render(
      <ProfileProvider>
        <TestConsumer />
      </ProfileProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('profile').textContent).toBe('none')
    })

    await act(async () => {
      screen.getByText('Select').click()
    })

    await waitFor(() => {
      expect(screen.getByTestId('profile').textContent).toBe('Alice')
      expect(mockApiProfilesSelect).toHaveBeenCalledWith(1)
    })
  })

  it('logout clears profile', async () => {
    function TestConsumer() {
      const { profile, selectProfile, logout } = useProfile()
      return (
        <div>
          <span data-testid="profile">{profile ? profile.name : 'none'}</span>
          <button onClick={() => selectProfile({ id: 1, name: 'Alice', avatar_color: '#000', theme: 'light', unit_preference: 'metric' })}>
            Select
          </button>
          <button onClick={logout}>Logout</button>
        </div>
      )
    }

    render(
      <ProfileProvider>
        <TestConsumer />
      </ProfileProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('profile').textContent).toBe('none')
    })

    await act(async () => {
      screen.getByText('Select').click()
    })

    await waitFor(() => {
      expect(screen.getByTestId('profile').textContent).toBe('Alice')
    })

    await act(async () => {
      screen.getByText('Logout').click()
    })

    expect(screen.getByTestId('profile').textContent).toBe('none')
  })

  it('handles API error during session check gracefully', async () => {
    mockApiProfilesList.mockRejectedValueOnce(new Error('Network error'))

    function TestConsumer() {
      const { loading } = useProfile()
      return <span data-testid="loading">{String(loading)}</span>
    }

    render(
      <ProfileProvider>
        <TestConsumer />
      </ProfileProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false')
    })
  })
})

describe('AIStatusContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('AIStatusProvider renders children', async () => {
    render(
      <AIStatusProvider>
        <div>AI Child</div>
      </AIStatusProvider>
    )
    await waitFor(() => {
      expect(screen.getByText('AI Child')).toBeInTheDocument()
    })
  })

  it('provides default values before API response', () => {
    mockApiAiStatus.mockReturnValueOnce(new Promise(() => {}))

    function TestConsumer() {
      const { available, loading } = useAIStatus()
      return (
        <div>
          <span data-testid="available">{String(available)}</span>
          <span data-testid="loading">{String(loading)}</span>
        </div>
      )
    }

    render(
      <AIStatusProvider>
        <TestConsumer />
      </AIStatusProvider>
    )

    expect(screen.getByTestId('available').textContent).toBe('false')
    expect(screen.getByTestId('loading').textContent).toBe('true')
  })

  it('updates status after API response', async () => {
    function TestConsumer() {
      const { available, configured, valid, loading } = useAIStatus()
      return (
        <div>
          <span data-testid="available">{String(available)}</span>
          <span data-testid="configured">{String(configured)}</span>
          <span data-testid="valid">{String(valid)}</span>
          <span data-testid="loading">{String(loading)}</span>
        </div>
      )
    }

    render(
      <AIStatusProvider>
        <TestConsumer />
      </AIStatusProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false')
    })

    expect(screen.getByTestId('available').textContent).toBe('true')
    expect(screen.getByTestId('configured').textContent).toBe('true')
    expect(screen.getByTestId('valid').textContent).toBe('true')
  })

  it('handles API error by setting error state', async () => {
    mockApiAiStatus.mockRejectedValueOnce(new Error('Connection failed'))

    function TestConsumer() {
      const { available, error, errorCode, loading } = useAIStatus()
      return (
        <div>
          <span data-testid="available">{String(available)}</span>
          <span data-testid="error">{error || 'none'}</span>
          <span data-testid="errorCode">{errorCode || 'none'}</span>
          <span data-testid="loading">{String(loading)}</span>
        </div>
      )
    }

    render(
      <AIStatusProvider>
        <TestConsumer />
      </AIStatusProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false')
    })

    expect(screen.getByTestId('available').textContent).toBe('false')
    expect(screen.getByTestId('error').textContent).toBe('Failed to check AI availability')
    expect(screen.getByTestId('errorCode').textContent).toBe('connection_error')
  })

  it('useAIStatus works outside provider with defaults', () => {
    function TestConsumer() {
      const { available, loading } = useAIStatus()
      return (
        <div>
          <span data-testid="available">{String(available)}</span>
          <span data-testid="loading">{String(loading)}</span>
        </div>
      )
    }

    render(<TestConsumer />)
    expect(screen.getByTestId('available').textContent).toBe('false')
    expect(screen.getByTestId('loading').textContent).toBe('true')
  })
})
