import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Register from '../screens/Register'
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
      register: vi.fn(),
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
  name: 'NewUser',
  avatar_color: '#6366f1',
  theme: 'light',
  unit_preference: 'metric',
}

function renderRegister() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <ProfileProvider>
          <Register />
        </ProfileProvider>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('Register', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.system.authSettings).mockResolvedValue(mockAuthSettings)
    vi.mocked(api.profiles.list).mockResolvedValue([])
    vi.mocked(api.favorites.list).mockResolvedValue([])
  })

  it('renders username, password, confirm, and color picker', async () => {
    renderRegister()

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/password \(8\+/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/confirm password/i)).toBeInTheDocument()
      expect(screen.getByText(/choose an avatar color/i)).toBeInTheDocument()
    })
  })

  it('renders instance name from settings', async () => {
    renderRegister()

    await waitFor(() => {
      expect(screen.getByText('Test Cookie')).toBeInTheDocument()
    })
  })

  it('shows login link', async () => {
    renderRegister()

    await waitFor(() => {
      expect(screen.getByText('Sign in')).toBeInTheDocument()
    })
  })

  it('validates password confirmation matches', async () => {
    renderRegister()

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument()
    })

    fireEvent.change(screen.getByPlaceholderText(/username/i), {
      target: { value: 'newuser' },
    })
    fireEvent.change(screen.getByPlaceholderText(/password \(8\+/i), {
      target: { value: 'password123' },
    })
    fireEvent.change(screen.getByPlaceholderText(/confirm password/i), {
      target: { value: 'different123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
    })
  })

  it('validates username format (alphanumeric + underscore)', async () => {
    renderRegister()

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument()
    })

    const usernameInput = screen.getByPlaceholderText(/username/i)

    // Check that the input has the pattern attribute for HTML5 validation
    expect(usernameInput).toHaveAttribute('pattern', '[a-zA-Z0-9_]+')

    // Set invalid value and submit
    fireEvent.change(usernameInput, {
      target: { value: 'ab' }, // Too short (< 3 chars) to trigger our JS validation
    })
    fireEvent.change(screen.getByPlaceholderText(/password \(8\+/i), {
      target: { value: 'password123' },
    })
    fireEvent.change(screen.getByPlaceholderText(/confirm password/i), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    // Our JS validation should catch the too-short username
    await waitFor(() => {
      expect(screen.getByText(/username must be 3-30 characters/i)).toBeInTheDocument()
    })
  })

  it('validates minimum password length', async () => {
    renderRegister()

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument()
    })

    fireEvent.change(screen.getByPlaceholderText(/username/i), {
      target: { value: 'newuser' },
    })
    fireEvent.change(screen.getByPlaceholderText(/password \(8\+/i), {
      target: { value: 'short' },
    })
    fireEvent.change(screen.getByPlaceholderText(/confirm password/i), {
      target: { value: 'short' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument()
    })
  })

  it('submits and redirects on success', async () => {
    vi.mocked(api.auth.register).mockResolvedValue(mockProfile)
    vi.mocked(api.profiles.select).mockResolvedValue(mockProfile)

    renderRegister()

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument()
    })

    fireEvent.change(screen.getByPlaceholderText(/username/i), {
      target: { value: 'newuser' },
    })
    fireEvent.change(screen.getByPlaceholderText(/password \(8\+/i), {
      target: { value: 'password123' },
    })
    fireEvent.change(screen.getByPlaceholderText(/confirm password/i), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(api.auth.register).toHaveBeenCalledWith(
        'newuser',
        'password123',
        'password123',
        '#6366f1' // Default color
      )
    })
  })

  it('displays error for duplicate username', async () => {
    vi.mocked(api.auth.register).mockRejectedValue(new Error('Username already taken'))

    renderRegister()

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument()
    })

    fireEvent.change(screen.getByPlaceholderText(/username/i), {
      target: { value: 'existinguser' },
    })
    fireEvent.change(screen.getByPlaceholderText(/password \(8\+/i), {
      target: { value: 'password123' },
    })
    fireEvent.change(screen.getByPlaceholderText(/confirm password/i), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText('Username already taken')).toBeInTheDocument()
    })
  })

  it('allows color selection', async () => {
    renderRegister()

    await waitFor(() => {
      expect(screen.getByText(/choose an avatar color/i)).toBeInTheDocument()
    })

    // Color picker should have multiple color buttons
    const colorButtons = screen.getAllByRole('button').filter(
      (btn) => btn.style.backgroundColor !== ''
    )
    expect(colorButtons.length).toBeGreaterThan(0)
  })
})
