import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import Favorites from '../screens/Favorites'
import type { Recipe } from '../api/client'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

// Mock sonner
vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}))

// Mock child components
vi.mock('../components/NavHeader', () => ({
  default: () => <div data-testid="nav-header">NavHeader</div>,
}))

vi.mock('../components/Skeletons', () => ({
  RecipeGridSkeleton: ({ count }: { count: number }) => (
    <div data-testid="recipe-grid-skeleton">Loading {count} skeletons</div>
  ),
}))

vi.mock('../components/RecipeCard', () => ({
  default: ({ recipe }: { recipe: Recipe }) => (
    <div data-testid="recipe-card">{recipe.title}</div>
  ),
}))

// Mock API client
vi.mock('../api/client', () => ({
  api: {
    favorites: {
      list: vi.fn(() => Promise.resolve([])),
      remove: vi.fn(),
    },
    history: {
      record: vi.fn(),
    },
  },
}))

describe('Favorites', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', async () => {
    render(<Favorites />)
    await waitFor(() => {
      expect(screen.getByTestId('nav-header')).toBeInTheDocument()
    })
  })

  it('shows loading skeleton initially', () => {
    render(<Favorites />)
    expect(screen.getByTestId('recipe-grid-skeleton')).toBeInTheDocument()
  })

  it('shows page heading', () => {
    render(<Favorites />)
    expect(screen.getByText('Favorites')).toBeInTheDocument()
  })

  it('shows empty state when no favorites exist', async () => {
    render(<Favorites />)
    await waitFor(() => {
      expect(screen.getByText('No favorites yet')).toBeInTheDocument()
    })
  })

  it('shows browse prompt in empty state', async () => {
    render(<Favorites />)
    await waitFor(() => {
      expect(screen.getByText('Browse recipes to add some!')).toBeInTheDocument()
    })
  })

  it('shows Discover Recipes button in empty state', async () => {
    render(<Favorites />)
    await waitFor(() => {
      expect(screen.getByText('Discover Recipes')).toBeInTheDocument()
    })
  })

  it('renders favorite recipe cards when favorites exist', async () => {
    const mockRecipe: Recipe = {
      id: 1,
      title: 'Chocolate Cake',
      host: 'baking.com',
      image_url: 'https://example.com/cake.jpg',
      image: null,
      total_time: 60,
      rating: 4.9,
      is_remix: false,
      scraped_at: '2024-01-01T00:00:00Z',
    }

    const { api } = await import('../api/client')
    vi.mocked(api.favorites.list).mockResolvedValueOnce([
      { recipe: mockRecipe, created_at: '2024-01-01T00:00:00Z' },
    ])

    render(<Favorites />)
    await waitFor(() => {
      expect(screen.getByText('Chocolate Cake')).toBeInTheDocument()
    })
  })

  it('does not show empty state when favorites exist', async () => {
    const mockRecipe: Recipe = {
      id: 1,
      title: 'Chocolate Cake',
      host: 'baking.com',
      image_url: 'https://example.com/cake.jpg',
      image: null,
      total_time: 60,
      rating: 4.9,
      is_remix: false,
      scraped_at: '2024-01-01T00:00:00Z',
    }

    const { api } = await import('../api/client')
    vi.mocked(api.favorites.list).mockResolvedValueOnce([
      { recipe: mockRecipe, created_at: '2024-01-01T00:00:00Z' },
    ])

    render(<Favorites />)
    await waitFor(() => {
      expect(screen.queryByText('No favorites yet')).not.toBeInTheDocument()
    })
  })
})
