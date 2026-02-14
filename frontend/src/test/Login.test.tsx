import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Login from '../screens/Login'
import { AuthProvider } from '../contexts/AuthContext'
import { ProfileProvider } from '../contexts/ProfileContext'
import { api } from '../api/client'

// Mock the API
vi.mock('../api/client', () => ({
  api: {
    system: {
      authSettings: vi.fn(),
    },
    auth: {
      login: vi.fn(),
    },
    profiles: {
      list: vi.fn(),
      select: vi.fn(),
    },
    favorites: {
      list: vi.fn(),
    },
  },
}))

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
  Toaster: () => null,
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

const mockProfile = {
  id: 1,
  name: 'TestUser',
  avatar_color: '#FF5733',
  theme: 'light',
  unit_preference: 'metric',
}

function renderLogin() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <ProfileProvider>
          <Login />
        </ProfileProvider>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.system.authSettings).mockResolvedValue(mockAuthSettings)
    vi.mocked(api.profiles.list).mockResolvedValue([])
    vi.mocked(api.favorites.list).mockResolvedValue([])
  })

  it('renders username and password fields', async () => {
    renderLogin()

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Password')).toBeInTheDocument()
    })
  })

  it('renders instance name from settings', async () => {
    renderLogin()

    await waitFor(() => {
      expect(screen.getByText('Test Cookie')).toBeInTheDocument()
    })
  })

  it('shows register link when registration enabled', async () => {
    renderLogin()

    await waitFor(() => {
      expect(screen.getByText('Register')).toBeInTheDocument()
    })
  })

  it('hides register link when registration disabled', async () => {
    vi.mocked(api.system.authSettings).mockResolvedValue({
      ...mockAuthSettings,
      allow_registration: false,
    })

    renderLogin()

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
    })

    expect(screen.queryByText('Register')).not.toBeInTheDocument()
  })

  it('displays error message on login failure', async () => {
    vi.mocked(api.auth.login).mockRejectedValue(new Error('Invalid credentials'))

    renderLogin()

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByPlaceholderText('Username'), {
      target: { value: 'testuser' },
    })
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'wrongpass' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText('Invalid username or password')).toBeInTheDocument()
    })
  })

  it('submits form and redirects on success', async () => {
    vi.mocked(api.auth.login).mockResolvedValue(mockProfile)
    vi.mocked(api.profiles.select).mockResolvedValue(mockProfile)

    renderLogin()

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByPlaceholderText('Username'), {
      target: { value: 'testuser' },
    })
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(api.auth.login).toHaveBeenCalledWith('testuser', 'password123')
    })
  })

  it('disables submit button when fields are empty', async () => {
    renderLogin()

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
    })

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    expect(submitButton).toBeDisabled()
  })

  it('enables submit button when fields are filled', async () => {
    renderLogin()

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByPlaceholderText('Username'), {
      target: { value: 'testuser' },
    })
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'password123' },
    })

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    expect(submitButton).not.toBeDisabled()
  })
})
