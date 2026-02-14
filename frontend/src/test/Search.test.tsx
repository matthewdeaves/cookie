import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

// Mock navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [new URLSearchParams('q=pasta')],
  }
})

// Mock profile context
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
    toggleTheme: vi.fn(),
    logout: vi.fn(),
  }),
}))

// Mock auth context
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    isAdmin: true,
  }),
}))

// Mock API
vi.mock('../api/client', () => ({
  api: {
    recipes: {
      search: vi.fn().mockResolvedValue({
        results: [],
        total: 0,
        has_more: false,
        sites: {},
      }),
      scrape: vi.fn(),
    },
    history: {
      record: vi.fn(),
    },
  },
}))

// Mock toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

// Import after mocks
import Search from '../screens/Search'

describe('Search', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderSearch = () => {
    return render(
      <MemoryRouter initialEntries={['/search?q=pasta']}>
        <Search />
      </MemoryRouter>
    )
  }

  it('renders search bar with query value', () => {
    renderSearch()
    const searchInput = screen.getByPlaceholderText('Search recipes or paste a URL...')
    expect(searchInput).toBeInTheDocument()
    expect(searchInput).toHaveValue('pasta')
  })

  it('renders NavHeader', () => {
    renderSearch()
    expect(screen.getByText('Cookie')).toBeInTheDocument()
  })

  it('navigates on search submit with new query', () => {
    renderSearch()
    const searchInput = screen.getByPlaceholderText('Search recipes or paste a URL...')

    fireEvent.change(searchInput, { target: { value: 'chicken' } })
    fireEvent.submit(searchInput.closest('form')!)

    expect(mockNavigate).toHaveBeenCalledWith('/search?q=chicken')
  })

  it('does not navigate on submit with same query', () => {
    renderSearch()
    const searchInput = screen.getByPlaceholderText('Search recipes or paste a URL...')

    // Submit without changing the value
    fireEvent.submit(searchInput.closest('form')!)

    expect(mockNavigate).not.toHaveBeenCalledWith(expect.stringContaining('/search'))
  })

  it('does not navigate on submit with empty query', () => {
    renderSearch()
    const searchInput = screen.getByPlaceholderText('Search recipes or paste a URL...')

    fireEvent.change(searchInput, { target: { value: '   ' } })
    fireEvent.submit(searchInput.closest('form')!)

    expect(mockNavigate).not.toHaveBeenCalledWith(expect.stringContaining('/search'))
  })
})
