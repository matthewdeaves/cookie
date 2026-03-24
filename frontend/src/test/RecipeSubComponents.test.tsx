import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import RecipeHeader from '../screens/components/RecipeHeader'
import RecipeIngredients from '../screens/components/RecipeIngredients'
import RecipeInstructions from '../screens/components/RecipeInstructions'
import RecipeActions from '../screens/components/RecipeActions'
import type { RecipeDetail } from '../api/client'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

// Mock lib/utils
vi.mock('../lib/utils', () => ({
  cn: (...args: string[]) => args.filter(Boolean).join(' '),
}))

// Mock lib/formatting
vi.mock('../lib/formatting', () => ({
  formatTime: (min: number | null) => (min ? `${min} min` : null),
}))

// Mock AddToCollectionDropdown
vi.mock('../components/AddToCollectionDropdown', () => ({
  default: ({ recipeId }: { recipeId: number }) => (
    <div data-testid="add-to-collection">{recipeId}</div>
  ),
}))

const baseRecipe: RecipeDetail = {
  id: 1,
  title: 'Chocolate Cake',
  host: 'food.com',
  image_url: 'https://example.com/cake.jpg',
  image: null,
  total_time: 60,
  rating: 4.8,
  is_remix: false,
  scraped_at: '2024-01-01T00:00:00Z',
  source_url: 'https://food.com/cake',
  canonical_url: 'https://food.com/cake',
  site_name: 'Food.com',
  author: 'Baker',
  description: 'Delicious cake',
  ingredients: ['200g flour', '100g sugar', '2 eggs'],
  ingredient_groups: [],
  instructions: ['Mix ingredients', 'Bake at 350F', 'Let cool'],
  instructions_text: '',
  prep_time: 15,
  cook_time: 45,
  yields: '8 slices',
  servings: 8,
  category: 'Dessert',
  cuisine: 'American',
  cooking_method: 'Baking',
  keywords: ['cake', 'chocolate'],
  dietary_restrictions: [],
  equipment: [],
  nutrition: {},
  rating_count: 200,
  language: 'en',
  links: [],
  ai_tips: [],
  remix_profile_id: null,
  remixed_from_id: null,
  linked_recipes: [],
  updated_at: '2024-01-01T00:00:00Z',
}

describe('RecipeHeader', () => {
  const defaultProps = {
    recipe: baseRecipe,
    imageUrl: 'https://example.com/cake.jpg',
    metaExpanded: true,
    setMetaExpanded: vi.fn(),
    canShowServingAdjustment: false,
    servings: 8,
    scaledData: null,
    scalingLoading: false,
    onServingChange: vi.fn(),
  }

  it('renders recipe title', () => {
    render(<RecipeHeader {...defaultProps} />)
    expect(screen.getByText('Chocolate Cake')).toBeInTheDocument()
  })

  it('renders recipe image when imageUrl provided', () => {
    render(<RecipeHeader {...defaultProps} />)
    const img = screen.getByAltText('Chocolate Cake')
    expect(img).toBeInTheDocument()
    expect(img).toHaveAttribute('src', 'https://example.com/cake.jpg')
  })

  it('renders recipe title as placeholder when imageUrl is null', () => {
    render(<RecipeHeader {...defaultProps} imageUrl={null} />)
    // No <img> element should be rendered
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
    // Title appears in the placeholder and in the overlay
    const titles = screen.getAllByText('Chocolate Cake')
    expect(titles.length).toBeGreaterThanOrEqual(2)
  })

  it('shows recipe rating', () => {
    render(<RecipeHeader {...defaultProps} />)
    expect(screen.getByText('4.8')).toBeInTheDocument()
  })

  it('shows recipe host', () => {
    render(<RecipeHeader {...defaultProps} />)
    expect(screen.getByText('food.com')).toBeInTheDocument()
  })

  it('shows Recipe Details toggle', () => {
    render(<RecipeHeader {...defaultProps} />)
    expect(screen.getByText('Recipe Details')).toBeInTheDocument()
  })

  it('calls setMetaExpanded when toggle clicked', () => {
    const setMetaExpanded = vi.fn()
    render(<RecipeHeader {...defaultProps} setMetaExpanded={setMetaExpanded} />)
    fireEvent.click(screen.getByText('Recipe Details'))
    expect(setMetaExpanded).toHaveBeenCalledWith(false)
  })

  it('shows static servings when AI not available', () => {
    render(<RecipeHeader {...defaultProps} />)
    expect(screen.getByText('Servings:')).toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
  })

  it('hides time/servings when metaExpanded is false', () => {
    render(<RecipeHeader {...defaultProps} metaExpanded={false} />)
    expect(screen.queryByText('Servings:')).not.toBeInTheDocument()
  })

  it('renders children (action buttons overlay)', () => {
    render(
      <RecipeHeader {...defaultProps}>
        <div data-testid="overlay-child">Overlay</div>
      </RecipeHeader>
    )
    expect(screen.getByTestId('overlay-child')).toBeInTheDocument()
  })
})

describe('RecipeIngredients', () => {
  it('renders flat ingredient list', () => {
    render(<RecipeIngredients recipe={baseRecipe} scaledData={null} />)
    expect(screen.getByText('200g flour')).toBeInTheDocument()
    expect(screen.getByText('100g sugar')).toBeInTheDocument()
    expect(screen.getByText('2 eggs')).toBeInTheDocument()
  })

  it('renders numbered ingredients', () => {
    render(<RecipeIngredients recipe={baseRecipe} scaledData={null} />)
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('renders ingredient groups when present', () => {
    const recipeWithGroups = {
      ...baseRecipe,
      ingredient_groups: [
        { purpose: 'For the cake', ingredients: ['200g flour', '100g sugar'] },
        { purpose: 'For the frosting', ingredients: ['50g butter'] },
      ],
    }
    render(<RecipeIngredients recipe={recipeWithGroups} scaledData={null} />)
    expect(screen.getByText('For the cake')).toBeInTheDocument()
    expect(screen.getByText('For the frosting')).toBeInTheDocument()
    expect(screen.getByText('50g butter')).toBeInTheDocument()
  })

  it('uses scaled ingredients when scaledData provided', () => {
    const scaledData = {
      target_servings: 16,
      original_servings: 8,
      ingredients: ['400g flour', '200g sugar', '4 eggs'],
      instructions: [],
      notes: [],
      prep_time_adjusted: null,
      cook_time_adjusted: null,
      total_time_adjusted: null,
      nutrition: null,
      cached: false,
    }
    render(<RecipeIngredients recipe={baseRecipe} scaledData={scaledData} />)
    expect(screen.getByText('400g flour')).toBeInTheDocument()
    expect(screen.getByText('200g sugar')).toBeInTheDocument()
    expect(screen.getByText('4 eggs')).toBeInTheDocument()
  })

  it('handles empty ingredients', () => {
    const emptyRecipe = { ...baseRecipe, ingredients: [], ingredient_groups: [] }
    const { container } = render(<RecipeIngredients recipe={emptyRecipe} scaledData={null} />)
    const listItems = container.querySelectorAll('li')
    expect(listItems.length).toBe(0)
  })
})

describe('RecipeInstructions', () => {
  it('renders instruction steps', () => {
    render(<RecipeInstructions recipe={baseRecipe} scaledData={null} />)
    expect(screen.getByText('Mix ingredients')).toBeInTheDocument()
    expect(screen.getByText('Bake at 350F')).toBeInTheDocument()
    expect(screen.getByText('Let cool')).toBeInTheDocument()
  })

  it('renders numbered steps', () => {
    render(<RecipeInstructions recipe={baseRecipe} scaledData={null} />)
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('shows empty state when no instructions', () => {
    const noInstructions = {
      ...baseRecipe,
      instructions: [],
      instructions_text: '',
    }
    render(<RecipeInstructions recipe={noInstructions} scaledData={null} />)
    expect(screen.getByText('No instructions available for this recipe.')).toBeInTheDocument()
  })

  it('falls back to instructions_text when instructions array is empty', () => {
    const textOnly = {
      ...baseRecipe,
      instructions: [],
      instructions_text: 'Step one\nStep two',
    }
    render(<RecipeInstructions recipe={textOnly} scaledData={null} />)
    expect(screen.getByText('Step one')).toBeInTheDocument()
    expect(screen.getByText('Step two')).toBeInTheDocument()
  })

  it('uses scaled instructions when provided', () => {
    const scaledData = {
      target_servings: 16,
      original_servings: 8,
      ingredients: [],
      instructions: ['Mix double ingredients', 'Bake longer'],
      notes: [],
      prep_time_adjusted: null,
      cook_time_adjusted: null,
      total_time_adjusted: null,
      nutrition: null,
      cached: false,
    }
    render(<RecipeInstructions recipe={baseRecipe} scaledData={scaledData} />)
    expect(screen.getByText('Mix double ingredients')).toBeInTheDocument()
    expect(screen.getByText('Instructions adjusted for 16 servings')).toBeInTheDocument()
  })
})

describe('RecipeActions', () => {
  const defaultProps = {
    recipeId: 1,
    recipeIsFavorite: false,
    aiAvailable: false,
    onFavoriteToggle: vi.fn(),
    onAddToNewCollection: vi.fn(),
    onShowRemixModal: vi.fn(),
    onStartCooking: vi.fn(),
  }

  it('renders favorite button', () => {
    render(<RecipeActions {...defaultProps} />)
    expect(screen.getByTitle('Add to favorites')).toBeInTheDocument()
  })

  it('shows correct title when recipe is favorite', () => {
    render(<RecipeActions {...defaultProps} recipeIsFavorite={true} />)
    expect(screen.getByTitle('Remove from favorites')).toBeInTheDocument()
  })

  it('renders Cook button', () => {
    render(<RecipeActions {...defaultProps} />)
    expect(screen.getByText('Cook!')).toBeInTheDocument()
  })

  it('calls onStartCooking when Cook button clicked', () => {
    const onStartCooking = vi.fn()
    render(<RecipeActions {...defaultProps} onStartCooking={onStartCooking} />)
    fireEvent.click(screen.getByText('Cook!'))
    expect(onStartCooking).toHaveBeenCalled()
  })

  it('calls onFavoriteToggle when favorite button clicked', () => {
    const onFavoriteToggle = vi.fn()
    render(<RecipeActions {...defaultProps} onFavoriteToggle={onFavoriteToggle} />)
    fireEvent.click(screen.getByTitle('Add to favorites'))
    expect(onFavoriteToggle).toHaveBeenCalled()
  })

  it('hides remix button when AI not available', () => {
    render(<RecipeActions {...defaultProps} aiAvailable={false} />)
    expect(screen.queryByTitle('Remix recipe')).not.toBeInTheDocument()
  })

  it('shows remix button when AI is available', () => {
    render(<RecipeActions {...defaultProps} aiAvailable={true} />)
    expect(screen.getByTitle('Remix recipe')).toBeInTheDocument()
  })

  it('calls onShowRemixModal when remix button clicked', () => {
    const onShowRemixModal = vi.fn()
    render(<RecipeActions {...defaultProps} aiAvailable={true} onShowRemixModal={onShowRemixModal} />)
    fireEvent.click(screen.getByTitle('Remix recipe'))
    expect(onShowRemixModal).toHaveBeenCalled()
  })

  it('renders action buttons container', () => {
    render(<RecipeActions {...defaultProps} />)
    expect(screen.getByTitle('Add to favorites')).toBeInTheDocument()
  })
})
