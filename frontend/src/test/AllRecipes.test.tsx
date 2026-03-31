import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import AllRecipes from '../screens/AllRecipes'
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
    recipes: {
      list: vi.fn(() => Promise.resolve([])),
    },
    history: {
      record: vi.fn(),
    },
  },
}))

describe('AllRecipes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', async () => {
    render(<AllRecipes />)
    await waitFor(() => {
      expect(screen.getByTestId('nav-header')).toBeInTheDocument()
    })
  })

  it('shows loading skeleton initially', async () => {
    render(<AllRecipes />)
    expect(screen.getByTestId('recipe-grid-skeleton')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.queryByTestId('recipe-grid-skeleton')).not.toBeInTheDocument()
    })
  })

  it('shows page heading', async () => {
    render(<AllRecipes />)
    expect(screen.getByText('My Recipes')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.queryByTestId('recipe-grid-skeleton')).not.toBeInTheDocument()
    })
  })

  it('shows empty state when no recipes exist', async () => {
    render(<AllRecipes />)
    await waitFor(() => {
      expect(screen.getByText('No recipes yet')).toBeInTheDocument()
    })
  })

  it('shows import prompt in empty state', async () => {
    render(<AllRecipes />)
    await waitFor(() => {
      expect(screen.getByText('Import recipes from the web to see them here')).toBeInTheDocument()
    })
  })

  it('renders recipe cards when recipes exist', async () => {
    const mockRecipes: Recipe[] = [
      {
        id: 1,
        title: 'Pasta Carbonara',
        host: 'cooking.com',
        image_url: 'https://example.com/pasta.jpg',
        image: null,
        total_time: 25,
        rating: 4.8,
        is_remix: false,
        scraped_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 2,
        title: 'Caesar Salad',
        host: 'recipes.com',
        image_url: 'https://example.com/salad.jpg',
        image: null,
        total_time: 15,
        rating: 4.2,
        is_remix: false,
        scraped_at: '2024-01-02T00:00:00Z',
      },
    ]

    const { api } = await import('../api/client')
    vi.mocked(api.recipes.list).mockResolvedValueOnce(mockRecipes)

    render(<AllRecipes />)
    await waitFor(() => {
      expect(screen.getByText('Pasta Carbonara')).toBeInTheDocument()
      expect(screen.getByText('Caesar Salad')).toBeInTheDocument()
    })
  })

  it('shows recipe count after loading', async () => {
    const mockRecipes: Recipe[] = [
      {
        id: 1,
        title: 'Test Recipe',
        host: 'example.com',
        image_url: '',
        image: null,
        total_time: null,
        rating: null,
        is_remix: false,
        scraped_at: '2024-01-01T00:00:00Z',
      },
    ]

    const { api } = await import('../api/client')
    vi.mocked(api.recipes.list).mockResolvedValueOnce(mockRecipes)

    render(<AllRecipes />)
    await waitFor(() => {
      expect(screen.getByText('1 recipe')).toBeInTheDocument()
    })
  })
})
