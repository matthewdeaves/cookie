import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Settings from '../screens/Settings'

// Mock sonner
vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}))

// Mock contexts
vi.mock('../contexts/ProfileContext', () => ({
  useProfile: () => ({
    profile: { id: 1, name: 'Test', avatar_color: '#000', theme: 'light', unit_preference: 'metric' },
    theme: 'light',
    favoriteRecipeIds: new Set(),
    loading: false,
    selectProfile: vi.fn(),
    logout: vi.fn(),
    toggleTheme: vi.fn(),
    toggleFavorite: vi.fn(),
    isFavorite: () => false,
  }),
}))

// PASSKEY MODE
vi.mock('../router', () => ({
  useMode: () => 'passkey',
  useVersion: () => 'dev',
}))

// Admin in passkey mode — the mode gate must still hide admin UI
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { is_admin: true },
    profile: null,
    isAdmin: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshSession: vi.fn(),
  }),
  useOptionalAuth: () => ({
    user: { is_admin: true },
    profile: null,
    isAdmin: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshSession: vi.fn(),
  }),
}))

vi.mock('../components/NavHeader', () => ({
  default: () => <div data-testid="nav-header">NavHeader</div>,
}))

vi.mock('../components/settings', () => ({
  SettingsGeneral: () => <div data-testid="settings-general">General</div>,
  SettingsPrompts: () => <div data-testid="settings-prompts">Prompts</div>,
  SettingsSources: () => <div data-testid="settings-sources">Sources</div>,
  SettingsSelectors: () => <div data-testid="settings-selectors">Selectors</div>,
  SettingsUsers: () => <div data-testid="settings-users">Users</div>,
  SettingsDanger: () => <div data-testid="settings-danger">Danger</div>,
}))

vi.mock('../components/settings/SettingsPasskeys', () => ({
  default: () => <div data-testid="settings-passkeys">Passkeys</div>,
}))

vi.mock('../components/DeviceCodeEntry', () => ({
  default: () => <div data-testid="device-code-entry">DeviceCodeEntry</div>,
}))

vi.mock('../api/client', () => ({
  api: {
    ai: {
      status: vi.fn(() => Promise.resolve({
        available: false, configured: false, valid: false,
        default_model: '', error: null, error_code: null,
      })),
      prompts: { list: vi.fn(() => Promise.resolve([])) },
      models: vi.fn(() => Promise.resolve([])),
      quotas: { get: vi.fn(() => Promise.resolve(null)) },
    },
    sources: { list: vi.fn(() => Promise.resolve([])) },
    profiles: { list: vi.fn(() => Promise.resolve([])) },
  },
}))

describe('Settings — passkey mode hides admin UI', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('does not render admin tab buttons', async () => {
    render(<MemoryRouter><Settings /></MemoryRouter>)
    // Wait for Settings to mount; the Passkeys tab indicates passkey-mode layout is rendered.
    await waitFor(() => {
      expect(screen.getByText('Passkeys')).toBeInTheDocument()
    })
    expect(screen.queryByText('AI Prompts')).toBeNull()
    expect(screen.queryByText('Sources')).toBeNull()
    expect(screen.queryByText('Selectors')).toBeNull()
    expect(screen.queryByText('Users')).toBeNull()
    expect(screen.queryByText('Danger Zone')).toBeNull()
  })

  it('does not render admin tab content components', async () => {
    render(<MemoryRouter><Settings /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText('Passkeys')).toBeInTheDocument()
    })
    expect(screen.queryByTestId('settings-prompts')).toBeNull()
    expect(screen.queryByTestId('settings-sources')).toBeNull()
    expect(screen.queryByTestId('settings-selectors')).toBeNull()
    expect(screen.queryByTestId('settings-users')).toBeNull()
    expect(screen.queryByTestId('settings-danger')).toBeNull()
  })

  it('still renders user-self-service tabs', async () => {
    render(<MemoryRouter><Settings /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText('General')).toBeInTheDocument()
    })
    expect(screen.getByText('Passkeys')).toBeInTheDocument()
    expect(screen.getByText('Pair Device')).toBeInTheDocument()
  })
})
