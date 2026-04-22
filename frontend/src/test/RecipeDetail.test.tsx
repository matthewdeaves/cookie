import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import RecipeDetail from '../screens/RecipeDetail'

// Mock the custom hook that drives RecipeDetail
const mockUseRecipeDetail = vi.fn()
vi.mock('../hooks/useRecipeDetail', () => ({
  useRecipeDetail: () => mockUseRecipeDetail(),
}))

// Mock sonner
vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}))

// Mock contexts
vi.mock('../contexts/ProfileContext', () => ({
  useProfile: () => ({
    profile: { id: 1, name: 'Test', avatar_color: '#000', theme: 'light', unit_preference: 'metric' },
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

// Mock child components
vi.mock('../components/NavHeader', () => ({
  default: () => <div data-testid="nav-header">NavHeader</div>,
}))

vi.mock('../components/Skeletons', () => ({
  RecipeDetailSkeleton: () => <div data-testid="recipe-detail-skeleton">Loading recipe...</div>,
}))

vi.mock('../components/RemixModal', () => ({
  default: () => null,
}))

vi.mock('../screens/components/RecipeHeader', () => ({
  default: ({ recipe }: { recipe: { title: string } }) => (
    <div data-testid="recipe-header">{recipe.title}</div>
  ),
}))

vi.mock('../screens/components/RecipeIngredients', () => ({
  default: () => <div data-testid="recipe-ingredients">Ingredients</div>,
}))

vi.mock('../screens/components/RecipeInstructions', () => ({
  default: () => <div data-testid="recipe-instructions">Instructions</div>,
}))

vi.mock('../screens/components/RecipeActions', () => ({
  default: () => <div data-testid="recipe-actions">Actions</div>,
}))

const mockRecipe = {
  id: 1,
  title: 'Chocolate Chip Cookies',
  host: 'example.com',
  image_url: 'https://example.com/cookies.jpg',
  image: null,
  total_time: 45,
  rating: 4.5,
  is_remix: false,
  scraped_at: '2024-01-01T00:00:00Z',
  source_url: 'https://example.com/cookies',
  canonical_url: 'https://example.com/cookies',
  site_name: 'Example',
  author: 'Chef Test',
  description: 'Delicious cookies',
  ingredients: ['2 cups flour', '1 cup sugar'],
  ingredient_groups: [],
  instructions: ['Mix ingredients', 'Bake at 350F'],
  instructions_text: 'Mix ingredients. Bake at 350F.',
  prep_time: 15,
  cook_time: 30,
  yields: '24 cookies',
  servings: 12,
  category: 'Dessert',
  cuisine: 'American',
  cooking_method: 'Baking',
  keywords: ['cookies', 'baking'],
  dietary_restrictions: [],
  equipment: ['mixing bowl', 'oven'],
  nutrition: { calories: '150', fat: '7g' },
  rating_count: 42,
  language: 'en',
  links: [],
  ai_tips: [],
  remix_profile_id: null,
  remixed_from_id: null,
  linked_recipes: [],
  updated_at: '2024-01-01T00:00:00Z',
}

const defaultHookReturn = {
  recipe: mockRecipe,
  loading: false,
  activeTab: 'ingredients' as const,
  setActiveTab: vi.fn(),
  metaExpanded: true,
  setMetaExpanded: vi.fn(),
  servings: 12,
  showRemixModal: false,
  setShowRemixModal: vi.fn(),
  scaledData: null,
  scalingLoading: false,
  tips: [],
  tipsLoading: false,
  tipsPolling: false,
  profile: { id: 1, name: 'Test', avatar_color: '#000', theme: 'light', unit_preference: 'metric' },
  aiStatus: { available: false, configured: false, valid: false, error: null, errorCode: null, loading: false, refresh: vi.fn(), setFeatureQuotaExhausted: vi.fn(), isFeatureAvailable: vi.fn(() => false) },
  recipeId: 1,
  canShowServingAdjustment: false,
  tipsAvailable: false,
  remixAvailable: false,
  recipeIsFavorite: false,
  imageUrl: 'https://example.com/cookies.jpg',
  handleServingChange: vi.fn(),
  handleGenerateTips: vi.fn(),
  handleFavoriteToggle: vi.fn(),
  handleStartCooking: vi.fn(),
  handleAddToNewCollection: vi.fn(),
  handleRemixCreated: vi.fn(),
  handleBack: vi.fn(),
}

describe('RecipeDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseRecipeDetail.mockReturnValue(defaultHookReturn)
  })

  it('renders without crashing', () => {
    render(<RecipeDetail />)
    expect(screen.getByTestId('nav-header')).toBeInTheDocument()
  })

  it('shows loading skeleton when loading', () => {
    mockUseRecipeDetail.mockReturnValue({
      ...defaultHookReturn,
      loading: true,
    })
    render(<RecipeDetail />)
    expect(screen.getByTestId('recipe-detail-skeleton')).toBeInTheDocument()
  })

  it('shows recipe not found when recipe is null', () => {
    mockUseRecipeDetail.mockReturnValue({
      ...defaultHookReturn,
      recipe: null,
      loading: false,
    })
    render(<RecipeDetail />)
    expect(screen.getByText('Recipe not found')).toBeInTheDocument()
  })

  it('shows recipe not found when profile is null', () => {
    mockUseRecipeDetail.mockReturnValue({
      ...defaultHookReturn,
      profile: null,
      loading: false,
    })
    render(<RecipeDetail />)
    expect(screen.getByText('Recipe not found')).toBeInTheDocument()
  })

  it('renders recipe header with title', () => {
    render(<RecipeDetail />)
    expect(screen.getByText('Chocolate Chip Cookies')).toBeInTheDocument()
  })

  it('shows Ingredients, Instructions, and Nutrition tabs', () => {
    render(<RecipeDetail />)
    // "Ingredients" appears both as tab and content, so use getAllByText
    expect(screen.getAllByText('Ingredients').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Instructions')).toBeInTheDocument()
    expect(screen.getByText('Nutrition')).toBeInTheDocument()
  })

  it('does not show Tips tab when AI is unavailable', () => {
    render(<RecipeDetail />)
    expect(screen.queryByText('Tips')).not.toBeInTheDocument()
  })

  it('shows Tips tab when AI is available', () => {
    mockUseRecipeDetail.mockReturnValue({
      ...defaultHookReturn,
      tipsAvailable: true,
    })
    render(<RecipeDetail />)
    expect(screen.getByText('Tips')).toBeInTheDocument()
  })

  it('shows Go Back button when recipe not found', () => {
    mockUseRecipeDetail.mockReturnValue({
      ...defaultHookReturn,
      recipe: null,
      loading: false,
    })
    render(<RecipeDetail />)
    expect(screen.getByText('Go Back')).toBeInTheDocument()
  })
})
