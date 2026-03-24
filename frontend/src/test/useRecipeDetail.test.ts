import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useRecipeDetail } from '../hooks/useRecipeDetail'
import type { RecipeDetail } from '../api/client'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useParams: () => ({ id: '42' }),
}))

// Mock sonner
vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn(), info: vi.fn() },
}))

// Mock profile context
const mockToggleFavorite = vi.fn()
vi.mock('../contexts/ProfileContext', () => ({
  useProfile: () => ({
    profile: { id: 1, name: 'Test', avatar_color: '#000', theme: 'light', unit_preference: 'metric' },
    isFavorite: (id: number) => id === 42,
    toggleFavorite: mockToggleFavorite,
  }),
}))

// Mock AI status context
vi.mock('../contexts/AIStatusContext', () => ({
  useAIStatus: () => ({
    available: true,
    configured: true,
    valid: true,
    error: null,
    errorCode: null,
    loading: false,
    refresh: vi.fn(),
  }),
}))

// Mock recipe data
const mockRecipe: RecipeDetail = {
  id: 42,
  title: 'Test Recipe',
  host: 'example.com',
  image_url: 'https://example.com/img.jpg',
  image: null,
  total_time: 30,
  rating: 4.5,
  is_remix: false,
  scraped_at: '2024-01-01T00:00:00Z',
  source_url: 'https://example.com/recipe',
  canonical_url: 'https://example.com/recipe',
  site_name: 'Example',
  author: 'Chef',
  description: 'A test recipe',
  ingredients: ['Ingredient 1', 'Ingredient 2'],
  ingredient_groups: [],
  instructions: ['Step 1', 'Step 2'],
  instructions_text: '',
  prep_time: 10,
  cook_time: 20,
  yields: '4 servings',
  servings: 4,
  category: 'Main',
  cuisine: 'Italian',
  cooking_method: 'Baking',
  keywords: [],
  dietary_restrictions: [],
  equipment: [],
  nutrition: {},
  rating_count: 50,
  language: 'en',
  links: [],
  ai_tips: ['Tip 1', 'Tip 2'],
  remix_profile_id: null,
  remixed_from_id: null,
  linked_recipes: [],
  updated_at: '2024-01-01T00:00:00Z',
}

// Mock API client
const mockGetRecipe = vi.fn(() => Promise.resolve(mockRecipe))
vi.mock('../api/client', () => ({
  api: {
    recipes: {
      get: (...args: unknown[]) => mockGetRecipe(...args),
    },
    ai: {
      scale: vi.fn(),
      tips: vi.fn(),
    },
    history: {
      record: vi.fn(),
    },
  },
}))

describe('useRecipeDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns loading state initially', () => {
    mockGetRecipe.mockReturnValueOnce(new Promise(() => {}))
    const { result } = renderHook(() => useRecipeDetail())
    expect(result.current.loading).toBe(true)
    expect(result.current.recipe).toBeNull()
  })

  it('returns recipe data after fetch', async () => {
    const { result } = renderHook(() => useRecipeDetail())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.recipe).toEqual(mockRecipe)
    expect(result.current.recipeId).toBe(42)
  })

  it('sets servings from recipe data', async () => {
    const { result } = renderHook(() => useRecipeDetail())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.servings).toBe(4)
  })

  it('sets tips from recipe data', async () => {
    const { result } = renderHook(() => useRecipeDetail())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.tips).toEqual(['Tip 1', 'Tip 2'])
  })

  it('handles API error gracefully', async () => {
    mockGetRecipe.mockRejectedValueOnce(new Error('Not found'))

    const { result } = renderHook(() => useRecipeDetail())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.recipe).toBeNull()
  })

  it('provides canShowServingAdjustment when AI is available and servings exist', async () => {
    const { result } = renderHook(() => useRecipeDetail())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.canShowServingAdjustment).toBe(true)
  })

  it('provides recipeIsFavorite from context', async () => {
    const { result } = renderHook(() => useRecipeDetail())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.recipeIsFavorite).toBe(true)
  })

  it('provides imageUrl from recipe', async () => {
    const { result } = renderHook(() => useRecipeDetail())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.imageUrl).toBe('https://example.com/img.jpg')
  })

  it('defaults activeTab to ingredients', async () => {
    const { result } = renderHook(() => useRecipeDetail())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.activeTab).toBe('ingredients')
  })

  it('handleBack navigates back', async () => {
    const { result } = renderHook(() => useRecipeDetail())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    act(() => {
      result.current.handleBack()
    })

    expect(mockNavigate).toHaveBeenCalledWith(-1)
  })

  it('handleStartCooking navigates to play mode', async () => {
    const { result } = renderHook(() => useRecipeDetail())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    act(() => {
      result.current.handleStartCooking()
    })

    expect(mockNavigate).toHaveBeenCalledWith('/recipe/42/play')
  })
})
