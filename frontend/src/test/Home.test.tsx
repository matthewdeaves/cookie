import { describe, it, expect, vi, beforeEach } from 'vitest'
import { act, render, screen } from '@testing-library/react'
import Home from '../screens/Home'
import type { Favorite, HistoryItem, Recipe } from '../api/client'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

// Mock sonner
vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}))

// Mock child components that are not under test
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

// Mock contexts
const mockProfile = { id: 1, name: 'Test', avatar_color: '#000', theme: 'light', unit_preference: 'metric' }

vi.mock('../contexts/ProfileContext', () => ({
  useProfile: () => ({
    profile: mockProfile,
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

vi.mock('../contexts/AIStatusContext', () => ({
  useAIStatus: () => ({
    available: false,
    configured: false,
    valid: false,
    error: null,
    errorCode: null,
    loading: false,
    refresh: vi.fn(),
  }),
}))

// Mock API client
const mockFavorites: Favorite[] = []
const mockHistory: HistoryItem[] = []
const mockRecipes: Recipe[] = []

vi.mock('../api/client', () => ({
  api: {
    favorites: {
      list: vi.fn(() => Promise.resolve(mockFavorites)),
      remove: vi.fn(),
    },
    history: {
      list: vi.fn(() => Promise.resolve(mockHistory)),
      record: vi.fn(),
    },
    recipes: {
      list: vi.fn(() => Promise.resolve(mockRecipes)),
    },
    ai: {
      discover: vi.fn(),
    },
  },
}))

describe('Home', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', async () => {
    await act(async () => {
      render(<Home />)
    })
    expect(screen.getByTestId('nav-header')).toBeInTheDocument()
  })

  it('shows loading skeleton initially', async () => {
    render(<Home />)
    expect(screen.getByTestId('recipe-grid-skeleton')).toBeInTheDocument()
    // Flush async state updates from useHomeData useEffect
    await act(async () => {})
  })

  it('shows search input', async () => {
    await act(async () => {
      render(<Home />)
    })
    expect(screen.getByPlaceholderText('Search recipes...')).toBeInTheDocument()
  })

  it('shows empty state when no favorites exist', async () => {
    await act(async () => {
      render(<Home />)
    })
    expect(screen.getByText('No favorites yet')).toBeInTheDocument()
  })

  it('shows favorites section heading after loading', async () => {
    await act(async () => {
      render(<Home />)
    })
    expect(screen.getByText('My Favorite Recipes')).toBeInTheDocument()
  })

  it('renders favorite recipe cards when favorites exist', async () => {
    const mockRecipe: Recipe = {
      id: 1,
      title: 'Test Recipe',
      host: 'example.com',
      image_url: 'https://example.com/img.jpg',
      image: null,
      total_time: 30,
      rating: 4.0,
      is_remix: false,
      scraped_at: '2024-01-01T00:00:00Z',
    }

    const { api } = await import('../api/client')
    vi.mocked(api.favorites.list).mockResolvedValueOnce([
      { recipe: mockRecipe, created_at: '2024-01-01T00:00:00Z' },
    ])

    await act(async () => {
      render(<Home />)
    })
    expect(screen.getByText('Test Recipe')).toBeInTheDocument()
  })
})
