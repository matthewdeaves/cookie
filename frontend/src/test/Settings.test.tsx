import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
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

// Mock router (useMode)
vi.mock('../router', () => ({
  useMode: () => 'home',
}))

// Mock auth context
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    profile: null,
    isAdmin: false,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshSession: vi.fn(),
  }),
  useOptionalAuth: () => ({
    user: null,
    profile: null,
    isAdmin: false,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshSession: vi.fn(),
  }),
}))

// Mock child components
vi.mock('../components/NavHeader', () => ({
  default: () => <div data-testid="nav-header">NavHeader</div>,
}))

vi.mock('../components/settings', () => ({
  SettingsGeneral: () => <div data-testid="settings-general">General Settings</div>,
  SettingsPrompts: () => <div data-testid="settings-prompts">AI Prompts</div>,
  SettingsSources: () => <div data-testid="settings-sources">Sources</div>,
  SettingsSelectors: () => <div data-testid="settings-selectors">Selectors</div>,
  SettingsUsers: () => <div data-testid="settings-users">Users</div>,
  SettingsDanger: () => <div data-testid="settings-danger">Danger Zone Content</div>,
}))

// Mock API client
vi.mock('../api/client', () => ({
  api: {
    ai: {
      status: vi.fn(() =>
        Promise.resolve({
          available: false,
          configured: false,
          valid: false,
          default_model: '',
          error: null,
          error_code: null,
        })
      ),
      prompts: {
        list: vi.fn(() => Promise.resolve([])),
      },
      models: vi.fn(() => Promise.resolve([])),
    },
    sources: {
      list: vi.fn(() => Promise.resolve([])),
    },
    profiles: {
      list: vi.fn(() => Promise.resolve([])),
    },
  },
}))

describe('Settings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', async () => {
    render(<MemoryRouter><Settings /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByTestId('nav-header')).toBeInTheDocument()
    })
  })

  it('shows all tab buttons', () => {
    render(<MemoryRouter><Settings /></MemoryRouter>)
    expect(screen.getByText('General')).toBeInTheDocument()
    expect(screen.getByText('AI Prompts')).toBeInTheDocument()
    expect(screen.getByText('Sources')).toBeInTheDocument()
    expect(screen.getByText('Selectors')).toBeInTheDocument()
    expect(screen.getByText('Users')).toBeInTheDocument()
    expect(screen.getByText('Danger Zone')).toBeInTheDocument()
  })

  it('shows loading spinner initially', () => {
    render(<MemoryRouter><Settings /></MemoryRouter>)
    // Loader2 renders as an svg with animate-spin class; check it is in DOM
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toBeTruthy()
  })

  it('shows General settings tab content after loading', async () => {
    render(<MemoryRouter><Settings /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByTestId('settings-general')).toBeInTheDocument()
    })
  })

  it('switches to AI Prompts tab when clicked', async () => {
    render(<MemoryRouter><Settings /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByTestId('settings-general')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('AI Prompts'))
    expect(screen.getByTestId('settings-prompts')).toBeInTheDocument()
  })

  it('switches to Sources tab when clicked', async () => {
    render(<MemoryRouter><Settings /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByTestId('settings-general')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Sources'))
    expect(screen.getByTestId('settings-sources')).toBeInTheDocument()
  })

  it('switches to Danger Zone tab when clicked', async () => {
    render(<MemoryRouter><Settings /></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByTestId('settings-general')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Danger Zone'))
    expect(screen.getByTestId('settings-danger')).toBeInTheDocument()
  })

  it('calls all API endpoints on mount', async () => {
    const { api } = await import('../api/client')

    render(<MemoryRouter><Settings /></MemoryRouter>)
    await waitFor(() => {
      expect(api.ai.status).toHaveBeenCalled()
      expect(api.ai.prompts.list).toHaveBeenCalled()
      expect(api.ai.models).toHaveBeenCalled()
      expect(api.sources.list).toHaveBeenCalled()
      expect(api.profiles.list).toHaveBeenCalled()
    })
  })
})
