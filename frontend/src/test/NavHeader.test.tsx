import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import NavHeader from '../components/NavHeader'

// Mock navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock profile context
const mockToggleTheme = vi.fn()
const mockLogout = vi.fn()

vi.mock('../contexts/ProfileContext', () => ({
  useProfile: () => ({
    profile: {
      id: 1,
      name: 'Test User',
      avatar_color: '#d97850',
      theme: 'light',
      unit_preference: 'us',
      created_at: '2024-01-01',
    },
    theme: 'light',
    toggleTheme: mockToggleTheme,
    logout: mockLogout,
  }),
}))

// Mock auth context - default to admin
const mockIsAdmin = vi.fn(() => true)
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    get isAdmin() {
      return mockIsAdmin()
    },
  }),
}))

describe('NavHeader', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockIsAdmin.mockReturnValue(true)
  })

  const renderNavHeader = () => {
    return render(
      <MemoryRouter>
        <NavHeader />
      </MemoryRouter>
    )
  }

  it('renders Cookie logo', () => {
    renderNavHeader()
    expect(screen.getByText('Cookie')).toBeInTheDocument()
  })

  it('renders all navigation icons for admin', () => {
    renderNavHeader()
    expect(screen.getByLabelText('Home')).toBeInTheDocument()
    expect(screen.getByLabelText('View favorites')).toBeInTheDocument()
    expect(screen.getByLabelText('View collections')).toBeInTheDocument()
    expect(screen.getByLabelText('Settings')).toBeInTheDocument()
  })

  it('hides settings icon for non-admin', () => {
    mockIsAdmin.mockReturnValue(false)
    renderNavHeader()
    expect(screen.getByLabelText('Home')).toBeInTheDocument()
    expect(screen.getByLabelText('View favorites')).toBeInTheDocument()
    expect(screen.getByLabelText('View collections')).toBeInTheDocument()
    expect(screen.queryByLabelText('Settings')).not.toBeInTheDocument()
  })

  it('renders theme toggle button', () => {
    renderNavHeader()
    expect(screen.getByLabelText('Switch to dark mode')).toBeInTheDocument()
  })

  it('navigates to home when Cookie logo is clicked', () => {
    renderNavHeader()
    fireEvent.click(screen.getByText('Cookie'))
    expect(mockNavigate).toHaveBeenCalledWith('/home')
  })

  it('navigates to home when home icon is clicked', () => {
    renderNavHeader()
    fireEvent.click(screen.getByLabelText('Home'))
    expect(mockNavigate).toHaveBeenCalledWith('/home')
  })

  it('navigates to favorites when favorites icon is clicked', () => {
    renderNavHeader()
    fireEvent.click(screen.getByLabelText('View favorites'))
    expect(mockNavigate).toHaveBeenCalledWith('/favorites')
  })

  it('navigates to collections when collections icon is clicked', () => {
    renderNavHeader()
    fireEvent.click(screen.getByLabelText('View collections'))
    expect(mockNavigate).toHaveBeenCalledWith('/collections')
  })

  it('navigates to settings when settings icon is clicked', () => {
    renderNavHeader()
    fireEvent.click(screen.getByLabelText('Settings'))
    expect(mockNavigate).toHaveBeenCalledWith('/settings')
  })

  it('calls toggleTheme when theme button is clicked', () => {
    renderNavHeader()
    fireEvent.click(screen.getByLabelText('Switch to dark mode'))
    expect(mockToggleTheme).toHaveBeenCalled()
  })

  it('displays profile initial in avatar', () => {
    renderNavHeader()
    expect(screen.getByText('T')).toBeInTheDocument()
  })

  it('applies profile avatar color', () => {
    renderNavHeader()
    const avatar = screen.getByText('T')
    expect(avatar).toHaveStyle({ backgroundColor: '#d97850' })
  })
})
