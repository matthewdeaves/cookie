import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ProfileSelector from '../screens/ProfileSelector'
import Search from '../screens/Search'
import { api } from '../api/client'
import type { ProfileStats } from '../api/client'

// Mock the API client
vi.mock('../api/client', () => ({
  api: {
    profiles: {
      list: vi.fn(),
      create: vi.fn(),
      select: vi.fn(),
    },
    recipes: {
      search: vi.fn(),
      scrape: vi.fn(),
    },
    favorites: {
      list: vi.fn(),
    },
    history: {
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

// Shared test fixtures
const mockStats: ProfileStats = {
  favorites: 0,
  collections: 0,
  collection_items: 0,
  remixes: 0,
  view_history: 0,
  scaling_cache: 0,
  discover_cache: 0,
}

describe('ProfileSelector', () => {
  const mockOnProfileSelect = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  it('shows loading state initially', () => {
    vi.mocked(api.profiles.list).mockImplementation(() => new Promise(() => {}))

    render(<ProfileSelector onProfileSelect={mockOnProfileSelect} />)

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders profiles after loading', async () => {
    vi.mocked(api.profiles.list).mockResolvedValueOnce([
      { id: 1, name: 'Alice', avatar_color: '#d97850', theme: 'light', unit_preference: 'us', created_at: '2024-01-01', stats: mockStats },
      { id: 2, name: 'Bob', avatar_color: '#8fae6f', theme: 'dark', unit_preference: 'metric', created_at: '2024-01-01', stats: mockStats },
    ])

    render(<ProfileSelector onProfileSelect={mockOnProfileSelect} />)

    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument()
      expect(screen.getByText('Bob')).toBeInTheDocument()
    })

    expect(screen.getByText("Who's cooking today?")).toBeInTheDocument()
  })

  it('calls onProfileSelect when profile is clicked', async () => {
    const profiles = [
      { id: 1, name: 'Alice', avatar_color: '#d97850', theme: 'light', unit_preference: 'us', created_at: '2024-01-01', stats: mockStats },
    ]
    vi.mocked(api.profiles.list).mockResolvedValueOnce(profiles)

    render(<ProfileSelector onProfileSelect={mockOnProfileSelect} />)

    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Alice'))

    expect(mockOnProfileSelect).toHaveBeenCalledWith(profiles[0])
  })

  it('shows create profile form when add button is clicked', async () => {
    vi.mocked(api.profiles.list).mockResolvedValueOnce([])

    render(<ProfileSelector onProfileSelect={mockOnProfileSelect} />)

    await waitFor(() => {
      expect(screen.getByText('Add Profile')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Add Profile'))

    expect(screen.getByText('Create Profile')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Enter your name')).toBeInTheDocument()
  })

  it('creates a new profile when form is submitted', async () => {
    vi.mocked(api.profiles.list).mockResolvedValueOnce([])
    vi.mocked(api.profiles.create).mockResolvedValueOnce({
      id: 1,
      name: 'Charlie',
      avatar_color: '#d97850',
      theme: 'light',
      unit_preference: 'metric',
    })

    render(<ProfileSelector onProfileSelect={mockOnProfileSelect} />)

    await waitFor(() => {
      expect(screen.getByText('Add Profile')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Add Profile'))

    const input = screen.getByPlaceholderText('Enter your name')
    fireEvent.change(input, { target: { value: 'Charlie' } })
    fireEvent.click(screen.getByText('Create'))

    await waitFor(() => {
      expect(api.profiles.create).toHaveBeenCalledWith({
        name: 'Charlie',
        avatar_color: '#d97850',
        theme: 'light',
        unit_preference: 'metric',
      })
    })
  })

  it('displays profile initials', async () => {
    vi.mocked(api.profiles.list).mockResolvedValueOnce([
      { id: 1, name: 'Alice', avatar_color: '#d97850', theme: 'light', unit_preference: 'us', created_at: '2024-01-01', stats: mockStats },
    ])

    render(<ProfileSelector onProfileSelect={mockOnProfileSelect} />)

    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument()
    })
  })
})

describe('Search', () => {
  const mockOnBack = vi.fn()
  const mockOnImport = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  it('shows search results', async () => {
    vi.mocked(api.recipes.search).mockResolvedValueOnce({
      results: [
        { url: 'https://example.com/recipe1', title: 'Chocolate Cookies', host: 'example.com', image_url: '', cached_image_url: null, description: 'Delicious', rating_count: null },
        { url: 'https://example.com/recipe2', title: 'Sugar Cookies', host: 'example.com', image_url: '', cached_image_url: null, description: 'Sweet', rating_count: null },
      ],
      total: 2,
      page: 1,
      has_more: false,
      sites: { 'example.com': 2 },
    })

    render(<Search query="cookies" onBack={mockOnBack} onImport={mockOnImport} />)

    await waitFor(() => {
      expect(screen.getByText('Chocolate Cookies')).toBeInTheDocument()
      expect(screen.getByText('Sugar Cookies')).toBeInTheDocument()
    })
  })

  it('displays result count', async () => {
    vi.mocked(api.recipes.search).mockResolvedValueOnce({
      results: [{ url: 'https://example.com/recipe', title: 'Test Recipe', host: 'example.com', image_url: '', cached_image_url: null, description: '', rating_count: null }],
      total: 1,
      page: 1,
      has_more: false,
      sites: { 'example.com': 1 },
    })

    render(<Search query="cookies" onBack={mockOnBack} onImport={mockOnImport} />)

    await waitFor(() => {
      expect(screen.getByText('1 result found')).toBeInTheDocument()
    })
  })

  it('displays source filter chips', async () => {
    vi.mocked(api.recipes.search).mockResolvedValueOnce({
      results: [],
      total: 10,
      page: 1,
      has_more: false,
      sites: { 'allrecipes.com': 5, 'foodnetwork.com': 5 },
    })

    render(<Search query="pasta" onBack={mockOnBack} onImport={mockOnImport} />)

    await waitFor(() => {
      expect(screen.getByText('All Sources (10)')).toBeInTheDocument()
      expect(screen.getByText('allrecipes.com (5)')).toBeInTheDocument()
      expect(screen.getByText('foodnetwork.com (5)')).toBeInTheDocument()
    })
  })

  it('filters by source when chip is clicked', async () => {
    vi.mocked(api.recipes.search)
      .mockResolvedValueOnce({
        results: [],
        total: 10,
        page: 1,
        has_more: false,
        sites: { 'allrecipes.com': 5, 'foodnetwork.com': 5 },
      })
      .mockResolvedValueOnce({
        results: [],
        total: 5,
        page: 1,
        has_more: false,
        sites: { 'allrecipes.com': 5 },
      })

    render(<Search query="pasta" onBack={mockOnBack} onImport={mockOnImport} />)

    await waitFor(() => {
      expect(screen.getByText('allrecipes.com (5)')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('allrecipes.com (5)'))

    await waitFor(() => {
      expect(api.recipes.search).toHaveBeenCalledWith('pasta', 'allrecipes.com', 1)
    })
  })

  it('shows load more button when has_more is true', async () => {
    vi.mocked(api.recipes.search).mockResolvedValueOnce({
      results: [{ url: 'https://example.com/recipe', title: 'Recipe', host: 'example.com', image_url: '', cached_image_url: null, description: '', rating_count: null }],
      total: 50,
      page: 1,
      has_more: true,
      sites: {},
    })

    render(<Search query="cookies" onBack={mockOnBack} onImport={mockOnImport} />)

    await waitFor(() => {
      expect(screen.getByText('Load More')).toBeInTheDocument()
    })
  })

  it('shows end of results when has_more is false', async () => {
    vi.mocked(api.recipes.search).mockResolvedValueOnce({
      results: [{ url: 'https://example.com/recipe', title: 'Recipe', host: 'example.com', image_url: '', cached_image_url: null, description: '', rating_count: null }],
      total: 1,
      page: 1,
      has_more: false,
      sites: {},
    })

    render(<Search query="cookies" onBack={mockOnBack} onImport={mockOnImport} />)

    await waitFor(() => {
      expect(screen.getByText('End of results')).toBeInTheDocument()
    })
  })

  it('shows URL import card when query is a URL', async () => {
    vi.mocked(api.recipes.search).mockResolvedValueOnce({
      results: [],
      total: 0,
      page: 1,
      has_more: false,
      sites: {},
    })

    render(<Search query="https://example.com/my-recipe" onBack={mockOnBack} onImport={mockOnImport} />)

    await waitFor(() => {
      expect(screen.getByText('Import Recipe from URL')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Import Recipe' })).toBeInTheDocument()
    })
  })

  it('calls onImport when import button is clicked', async () => {
    vi.mocked(api.recipes.search).mockResolvedValueOnce({
      results: [],
      total: 0,
      page: 1,
      has_more: false,
      sites: {},
    })
    mockOnImport.mockResolvedValueOnce(undefined)

    render(<Search query="https://example.com/recipe" onBack={mockOnBack} onImport={mockOnImport} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Import Recipe' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Import Recipe' }))

    await waitFor(() => {
      expect(mockOnImport).toHaveBeenCalledWith('https://example.com/recipe')
    })
  })

  it('calls onBack when back button is clicked', async () => {
    vi.mocked(api.recipes.search).mockResolvedValueOnce({
      results: [],
      total: 0,
      page: 1,
      has_more: false,
      sites: {},
    })

    render(<Search query="cookies" onBack={mockOnBack} onImport={mockOnImport} />)

    await waitFor(() => {
      expect(screen.getByText('Back to Home')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Back to Home'))

    expect(mockOnBack).toHaveBeenCalled()
  })

  it('shows empty state when no results', async () => {
    vi.mocked(api.recipes.search).mockResolvedValueOnce({
      results: [],
      total: 0,
      page: 1,
      has_more: false,
      sites: {},
    })

    render(<Search query="zzzzzzz" onBack={mockOnBack} onImport={mockOnImport} />)

    await waitFor(() => {
      expect(screen.getByText('No recipes found for "zzzzzzz"')).toBeInTheDocument()
    })
  })
})
