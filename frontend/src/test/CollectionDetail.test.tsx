import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import CollectionDetail from '../screens/CollectionDetail'
import type { CollectionDetail as CollectionDetailType, Recipe } from '../api/client'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useParams: () => ({ id: '1' }),
}))

// Mock sonner
vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}))

// Mock lib/utils
vi.mock('../lib/utils', () => ({
  cn: (...args: string[]) => args.filter(Boolean).join(' '),
}))

// Mock child components
vi.mock('../components/NavHeader', () => ({
  default: () => <div data-testid="nav-header">NavHeader</div>,
}))

vi.mock('../components/RecipeCard', () => ({
  default: ({ recipe, onClick }: { recipe: Recipe; onClick?: () => void }) => (
    <div data-testid="recipe-card" onClick={onClick}>{recipe.title}</div>
  ),
}))

vi.mock('../components/Skeletons', () => ({
  LoadingSpinner: ({ className }: { className?: string }) => (
    <div data-testid="loading-spinner" className={className}>Loading...</div>
  ),
}))

// Test data
const mockRecipe: Recipe = {
  id: 10,
  title: 'Spaghetti Bolognese',
  host: 'allrecipes.com',
  image_url: 'https://example.com/img.jpg',
  image: null,
  total_time: 45,
  rating: 4.5,
  is_remix: false,
  scraped_at: '2024-01-01T00:00:00Z',
}

const mockCollectionWithRecipes: CollectionDetailType = {
  id: 1,
  name: 'Weeknight Dinners',
  description: 'Quick and easy meals',
  recipes: [
    { recipe: mockRecipe, order: 0, added_at: '2024-01-01T00:00:00Z' },
  ],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const mockEmptyCollection: CollectionDetailType = {
  id: 2,
  name: 'Empty Collection',
  description: '',
  recipes: [],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

// Mock API client
vi.mock('../api/client', () => ({
  api: {
    collections: {
      get: vi.fn(() => Promise.resolve(mockCollectionWithRecipes)),
      delete: vi.fn(() => Promise.resolve(null)),
      removeRecipe: vi.fn(() => Promise.resolve(null)),
    },
    history: {
      record: vi.fn(() => Promise.resolve(null)),
    },
  },
}))

describe('CollectionDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    render(<CollectionDetail />)
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('renders collection name after loading', async () => {
    render(<CollectionDetail />)
    await waitFor(() => {
      expect(screen.getByText('Weeknight Dinners')).toBeInTheDocument()
    })
  })

  it('shows recipe count', async () => {
    render(<CollectionDetail />)
    await waitFor(() => {
      expect(screen.getByText('1 recipe')).toBeInTheDocument()
    })
  })

  it('renders recipe cards', async () => {
    render(<CollectionDetail />)
    await waitFor(() => {
      expect(screen.getByText('Spaghetti Bolognese')).toBeInTheDocument()
    })
  })

  it('shows nav header', async () => {
    render(<CollectionDetail />)
    await waitFor(() => {
      expect(screen.getByTestId('nav-header')).toBeInTheDocument()
    })
  })

  it('shows empty state for collection with no recipes', async () => {
    const { api } = await import('../api/client')
    vi.mocked(api.collections.get).mockResolvedValueOnce(mockEmptyCollection)

    render(<CollectionDetail />)
    await waitFor(() => {
      expect(screen.getByText('This collection is empty')).toBeInTheDocument()
      expect(screen.getByText('Add recipes from their detail pages.')).toBeInTheDocument()
    })
  })

  it('shows delete confirmation when delete button clicked', async () => {
    render(<CollectionDetail />)
    await waitFor(() => {
      expect(screen.getByText('Weeknight Dinners')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTitle('Delete collection'))
    expect(screen.getByText(/Delete "Weeknight Dinners"\?/)).toBeInTheDocument()
    expect(screen.getByText('Cancel')).toBeInTheDocument()
    expect(screen.getByText('Delete')).toBeInTheDocument()
  })

  it('navigates to /collections after deleting', async () => {
    render(<CollectionDetail />)
    await waitFor(() => {
      expect(screen.getByText('Weeknight Dinners')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTitle('Delete collection'))
    fireEvent.click(screen.getByText('Delete'))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/collections')
    })
  })

  it('shows collection not found when API returns error', async () => {
    const { api } = await import('../api/client')
    vi.mocked(api.collections.get).mockRejectedValueOnce(new Error('Not found'))

    render(<CollectionDetail />)
    await waitFor(() => {
      expect(screen.getByText('Collection not found')).toBeInTheDocument()
      expect(screen.getByText('Go Back')).toBeInTheDocument()
    })
  })

  it('navigates to /collections when Go Back is clicked from not found', async () => {
    const { api } = await import('../api/client')
    vi.mocked(api.collections.get).mockRejectedValueOnce(new Error('Not found'))

    render(<CollectionDetail />)
    await waitFor(() => {
      expect(screen.getByText('Go Back')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Go Back'))
    expect(mockNavigate).toHaveBeenCalledWith('/collections')
  })
})
