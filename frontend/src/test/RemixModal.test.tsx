import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import RemixModal from '../components/RemixModal'
import { api } from '../api/client'
import type { RecipeDetail } from '../api/client'

// Mock the API
vi.mock('../api/client', () => ({
  api: {
    ai: {
      remix: {
        getSuggestions: vi.fn(),
        create: vi.fn(),
      },
    },
  },
}))

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}))

const mockRecipe: RecipeDetail = {
  id: 1,
  title: 'Chocolate Chip Cookies',
  host: 'example.com',
  source_url: 'https://example.com/recipe',
  canonical_url: 'https://example.com/recipe',
  site_name: 'Example',
  author: 'Chef Test',
  description: 'Delicious cookies',
  image: 'https://example.com/image.jpg',
  image_url: 'https://example.com/image.jpg',
  ingredients: ['flour', 'sugar', 'chocolate chips'],
  ingredient_groups: [],
  instructions: ['Mix ingredients', 'Bake at 350F'],
  instructions_text: '',
  nutrition: {},
  servings: 24,
  prep_time: 15,
  cook_time: 12,
  total_time: 27,
  yields: '24 cookies',
  rating: 4.5,
  rating_count: 100,
  ai_tips: [],
  scraped_at: '2024-01-01T00:00:00Z',
  is_remix: false,
  category: 'Dessert',
  cuisine: 'American',
  cooking_method: 'Baking',
  keywords: ['cookies', 'chocolate'],
  dietary_restrictions: [],
  equipment: ['oven', 'mixing bowl'],
  language: 'en',
  links: [],
  remix_profile_id: null,
  updated_at: '2024-01-01T00:00:00Z',
}

describe('RemixModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('does not render when isOpen is false', () => {
    render(
      <RemixModal
        recipe={mockRecipe}
        profileId={1}
        isOpen={false}
        onClose={vi.fn()}
        onRemixCreated={vi.fn()}
      />
    )
    expect(screen.queryByText('Remix This Recipe')).not.toBeInTheDocument()
  })

  it('renders modal when isOpen is true', async () => {
    vi.mocked(api.ai.remix.getSuggestions).mockResolvedValue({
      suggestions: ['Make it vegan', 'Make it spicy'],
    })

    render(
      <RemixModal
        recipe={mockRecipe}
        profileId={1}
        isOpen={true}
        onClose={vi.fn()}
        onRemixCreated={vi.fn()}
      />
    )

    expect(screen.getByText('Remix This Recipe')).toBeInTheDocument()
    expect(screen.getByText(/Chocolate Chip Cookies/)).toBeInTheDocument()
  })

  it('shows loading state while fetching suggestions', async () => {
    vi.mocked(api.ai.remix.getSuggestions).mockImplementation(
      () => new Promise(() => {})
    )

    render(
      <RemixModal
        recipe={mockRecipe}
        profileId={1}
        isOpen={true}
        onClose={vi.fn()}
        onRemixCreated={vi.fn()}
      />
    )

    expect(screen.getByText('Generating suggestions...')).toBeInTheDocument()
  })

  it('displays suggestions when loaded', async () => {
    vi.mocked(api.ai.remix.getSuggestions).mockResolvedValue({
      suggestions: ['Make it vegan', 'Make it gluten-free'],
    })

    render(
      <RemixModal
        recipe={mockRecipe}
        profileId={1}
        isOpen={true}
        onClose={vi.fn()}
        onRemixCreated={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Make it vegan')).toBeInTheDocument()
      expect(screen.getByText('Make it gluten-free')).toBeInTheDocument()
    })
  })

  it('allows selecting a suggestion', async () => {
    vi.mocked(api.ai.remix.getSuggestions).mockResolvedValue({
      suggestions: ['Make it vegan'],
    })

    render(
      <RemixModal
        recipe={mockRecipe}
        profileId={1}
        isOpen={true}
        onClose={vi.fn()}
        onRemixCreated={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Make it vegan')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Make it vegan'))

    // The button should now be selected (has primary background)
    const button = screen.getByText('Make it vegan')
    expect(button).toHaveClass('bg-primary')
  })

  it('deselects suggestion when clicked again', async () => {
    vi.mocked(api.ai.remix.getSuggestions).mockResolvedValue({
      suggestions: ['Make it vegan'],
    })

    render(
      <RemixModal
        recipe={mockRecipe}
        profileId={1}
        isOpen={true}
        onClose={vi.fn()}
        onRemixCreated={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Make it vegan')).toBeInTheDocument()
    })

    const suggestionBtn = screen.getByText('Make it vegan')
    fireEvent.click(suggestionBtn)
    fireEvent.click(suggestionBtn)

    expect(suggestionBtn).toHaveClass('bg-muted')
  })

  it('allows entering custom input', async () => {
    vi.mocked(api.ai.remix.getSuggestions).mockResolvedValue({
      suggestions: [],
    })

    render(
      <RemixModal
        recipe={mockRecipe}
        profileId={1}
        isOpen={true}
        onClose={vi.fn()}
        onRemixCreated={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(screen.getByPlaceholderText('e.g., Make it gluten-free')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByPlaceholderText('e.g., Make it gluten-free'), {
      target: { value: 'Add more chocolate' },
    })

    expect(screen.getByDisplayValue('Add more chocolate')).toBeInTheDocument()
  })

  it('clears suggestion selection when custom input is entered', async () => {
    vi.mocked(api.ai.remix.getSuggestions).mockResolvedValue({
      suggestions: ['Make it vegan'],
    })

    render(
      <RemixModal
        recipe={mockRecipe}
        profileId={1}
        isOpen={true}
        onClose={vi.fn()}
        onRemixCreated={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Make it vegan')).toBeInTheDocument()
    })

    // Select suggestion first
    fireEvent.click(screen.getByText('Make it vegan'))
    expect(screen.getByText('Make it vegan')).toHaveClass('bg-primary')

    // Enter custom input
    fireEvent.change(screen.getByPlaceholderText('e.g., Make it gluten-free'), {
      target: { value: 'Custom modification' },
    })

    // Suggestion should be deselected
    expect(screen.getByText('Make it vegan')).toHaveClass('bg-muted')
  })

  it('disables Create button when no selection or input', async () => {
    vi.mocked(api.ai.remix.getSuggestions).mockResolvedValue({
      suggestions: [],
    })

    render(
      <RemixModal
        recipe={mockRecipe}
        profileId={1}
        isOpen={true}
        onClose={vi.fn()}
        onRemixCreated={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Create Remix')).toBeInTheDocument()
    })

    expect(screen.getByText('Create Remix').closest('button')).toBeDisabled()
  })

  it('enables Create button when suggestion is selected', async () => {
    vi.mocked(api.ai.remix.getSuggestions).mockResolvedValue({
      suggestions: ['Make it vegan'],
    })

    render(
      <RemixModal
        recipe={mockRecipe}
        profileId={1}
        isOpen={true}
        onClose={vi.fn()}
        onRemixCreated={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Make it vegan')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Make it vegan'))

    expect(screen.getByText('Create Remix').closest('button')).not.toBeDisabled()
  })

  it('calls onClose when close button is clicked', async () => {
    vi.mocked(api.ai.remix.getSuggestions).mockResolvedValue({
      suggestions: [],
    })

    const handleClose = vi.fn()
    render(
      <RemixModal
        recipe={mockRecipe}
        profileId={1}
        isOpen={true}
        onClose={handleClose}
        onRemixCreated={vi.fn()}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Remix This Recipe')).toBeInTheDocument()
    })

    // Find close button (X button in header)
    const closeButtons = screen.getAllByRole('button')
    const closeButton = closeButtons.find(btn =>
      btn.querySelector('svg.lucide-x') !== null
    )

    if (closeButton) {
      fireEvent.click(closeButton)
      expect(handleClose).toHaveBeenCalled()
    }
  })

  it('creates remix and calls onRemixCreated on success', async () => {
    vi.mocked(api.ai.remix.getSuggestions).mockResolvedValue({
      suggestions: ['Make it vegan'],
    })
    vi.mocked(api.ai.remix.create).mockResolvedValue({
      id: 2,
      title: 'Vegan Chocolate Chip Cookies',
      description: '',
      ingredients: [],
      instructions: [],
      host: 'cookie-remix',
      site_name: 'Cookie Remix',
      is_remix: true,
      prep_time: 15,
      cook_time: 12,
      total_time: 27,
      yields: '24 cookies',
      servings: 24,
    })

    const handleRemixCreated = vi.fn()
    const handleClose = vi.fn()

    render(
      <RemixModal
        recipe={mockRecipe}
        profileId={1}
        isOpen={true}
        onClose={handleClose}
        onRemixCreated={handleRemixCreated}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Make it vegan')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Make it vegan'))
    fireEvent.click(screen.getByText('Create Remix'))

    await waitFor(() => {
      expect(api.ai.remix.create).toHaveBeenCalledWith(1, 'Make it vegan', 1)
      expect(handleRemixCreated).toHaveBeenCalledWith(2)
      expect(handleClose).toHaveBeenCalled()
    })
  })
})
