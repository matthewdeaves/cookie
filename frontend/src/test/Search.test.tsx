import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
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

// Mock API
const mockSearch = vi.fn().mockResolvedValue({
  results: [],
  total: 0,
  has_more: false,
  sites: {},
})

vi.mock('../api/client', () => ({
  api: {
    recipes: {
      search: (...args: unknown[]) => mockSearch(...args),
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
    mockSearch.mockResolvedValue({
      results: [],
      total: 0,
      has_more: false,
      sites: {},
    })
  })

  const renderSearch = () => {
    return render(
      <MemoryRouter initialEntries={['/search?q=pasta']}>
        <Search />
      </MemoryRouter>
    )
  }

  it('renders search bar with query value', async () => {
    renderSearch()
    const searchInput = screen.getByPlaceholderText('Search recipes or paste a URL...')
    expect(searchInput).toBeInTheDocument()
    expect(searchInput).toHaveValue('pasta')
    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalled()
    })
  })

  it('renders NavHeader', async () => {
    renderSearch()
    expect(screen.getByText('Cookie')).toBeInTheDocument()
    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalled()
    })
  })

  it('navigates on search submit with new query', async () => {
    renderSearch()
    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalled()
    })

    const searchInput = screen.getByPlaceholderText('Search recipes or paste a URL...')
    fireEvent.change(searchInput, { target: { value: 'chicken' } })
    fireEvent.submit(searchInput.closest('form')!)

    expect(mockNavigate).toHaveBeenCalledWith('/search?q=chicken')
  })

  it('does not navigate on submit with same query', async () => {
    renderSearch()
    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalled()
    })

    const searchInput = screen.getByPlaceholderText('Search recipes or paste a URL...')
    fireEvent.submit(searchInput.closest('form')!)

    expect(mockNavigate).not.toHaveBeenCalledWith(expect.stringContaining('/search'))
  })

  it('does not navigate on submit with empty query', async () => {
    renderSearch()
    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalled()
    })

    const searchInput = screen.getByPlaceholderText('Search recipes or paste a URL...')
    fireEvent.change(searchInput, { target: { value: '   ' } })
    fireEvent.submit(searchInput.closest('form')!)

    expect(mockNavigate).not.toHaveBeenCalledWith(expect.stringContaining('/search'))
  })

  it('shows empty results message when no recipes found', async () => {
    renderSearch()
    await waitFor(() => {
      expect(screen.getByText(/No recipes found for/)).toBeInTheDocument()
    })
  })

  it('shows result count after loading', async () => {
    mockSearch.mockResolvedValueOnce({
      results: [
        { url: 'https://food.com/pasta', title: 'Pasta Recipe', host: 'food.com', image_url: '', cached_image_url: null, description: '', rating_count: null },
      ],
      total: 1,
      has_more: false,
      sites: { 'food.com': 1 },
    })

    renderSearch()
    await waitFor(() => {
      expect(screen.getByText('1 result found')).toBeInTheDocument()
    })
  })

  it('renders source filter chips when results have sites', async () => {
    mockSearch.mockResolvedValueOnce({
      results: [
        { url: 'https://food.com/pasta', title: 'Pasta', host: 'food.com', image_url: '', cached_image_url: null, description: '', rating_count: null },
      ],
      total: 3,
      has_more: false,
      sites: { 'food.com': 2, 'allrecipes.com': 1 },
    })

    renderSearch()
    await waitFor(() => {
      expect(screen.getByText('All Sources (3)')).toBeInTheDocument()
      expect(screen.getByText('food.com (2)')).toBeInTheDocument()
      expect(screen.getByText('allrecipes.com (1)')).toBeInTheDocument()
    })
  })

  it('shows loading spinner initially', () => {
    mockSearch.mockReturnValueOnce(new Promise(() => {}))
    renderSearch()
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toBeTruthy()
  })

  it('calls search API with query', async () => {
    renderSearch()
    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalledWith('pasta', undefined, 1, expect.any(AbortSignal))
    })
  })
})
