import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import RecipeCard from '../components/RecipeCard'
import type { Recipe } from '../api/client'

// Mock recipe data
const mockRecipe: Recipe = {
  id: 1,
  title: 'Chocolate Chip Cookies',
  host: 'example.com',
  image_url: 'https://example.com/cookies.jpg',
  image: null,
  total_time: 45,
  rating: 4.5,
  is_remix: false,
  scraped_at: '2024-01-01T00:00:00Z',
}

describe('RecipeCard', () => {
  it('renders recipe title', () => {
    render(<RecipeCard recipe={mockRecipe} />)
    expect(screen.getByText('Chocolate Chip Cookies')).toBeInTheDocument()
  })

  it('renders recipe host', () => {
    render(<RecipeCard recipe={mockRecipe} />)
    expect(screen.getByText('example.com')).toBeInTheDocument()
  })

  it('renders recipe image when image_url is provided', () => {
    render(<RecipeCard recipe={mockRecipe} />)
    const img = screen.getByRole('img')
    expect(img).toHaveAttribute('src', 'https://example.com/cookies.jpg')
    expect(img).toHaveAttribute('alt', 'Chocolate Chip Cookies')
  })

  it('uses image property over image_url when both are present', () => {
    const recipeWithImage: Recipe = {
      ...mockRecipe,
      image: 'https://example.com/main-image.jpg',
    }
    render(<RecipeCard recipe={recipeWithImage} />)
    const img = screen.getByRole('img')
    expect(img).toHaveAttribute('src', 'https://example.com/main-image.jpg')
  })

  it('shows "No image" text when no image is available', () => {
    const recipeNoImage: Recipe = {
      ...mockRecipe,
      image_url: '',
      image: null,
    }
    render(<RecipeCard recipe={recipeNoImage} />)
    expect(screen.getByText('No image')).toBeInTheDocument()
  })

  it('formats time correctly for minutes under 60', () => {
    render(<RecipeCard recipe={mockRecipe} />)
    expect(screen.getByText('45 min')).toBeInTheDocument()
  })

  it('formats time correctly for hours', () => {
    const recipeWithHours: Recipe = {
      ...mockRecipe,
      total_time: 90,
    }
    render(<RecipeCard recipe={recipeWithHours} />)
    expect(screen.getByText('1h 30m')).toBeInTheDocument()
  })

  it('does not show time when total_time is null', () => {
    const recipeNoTime: Recipe = {
      ...mockRecipe,
      total_time: null,
    }
    render(<RecipeCard recipe={recipeNoTime} />)
    // Check that no time element with Clock icon exists
    expect(screen.queryByText(/^\d+\s*min$/)).not.toBeInTheDocument()
    expect(screen.queryByText(/^\d+h$/)).not.toBeInTheDocument()
    expect(screen.queryByText(/^\d+h\s+\d+m$/)).not.toBeInTheDocument()
  })

  it('renders rating when present', () => {
    render(<RecipeCard recipe={mockRecipe} />)
    expect(screen.getByText('4.5')).toBeInTheDocument()
  })

  it('does not show rating when null', () => {
    const recipeNoRating: Recipe = {
      ...mockRecipe,
      rating: null,
    }
    render(<RecipeCard recipe={recipeNoRating} />)
    expect(screen.queryByText(/^\d+\.\d+$/)).not.toBeInTheDocument()
  })

  it('shows Remix badge when is_remix is true', () => {
    const remixRecipe: Recipe = {
      ...mockRecipe,
      is_remix: true,
    }
    render(<RecipeCard recipe={remixRecipe} />)
    expect(screen.getByText('Remix')).toBeInTheDocument()
  })

  it('does not show Remix badge when is_remix is false', () => {
    render(<RecipeCard recipe={mockRecipe} />)
    expect(screen.queryByText('Remix')).not.toBeInTheDocument()
  })

  it('calls onClick when card is clicked', () => {
    const handleClick = vi.fn()
    render(<RecipeCard recipe={mockRecipe} onClick={handleClick} />)
    fireEvent.click(screen.getByText('Chocolate Chip Cookies'))
    expect(handleClick).toHaveBeenCalledWith(mockRecipe)
  })

  it('shows favorite button when onFavoriteToggle is provided', () => {
    const handleFavorite = vi.fn()
    render(
      <RecipeCard
        recipe={mockRecipe}
        onFavoriteToggle={handleFavorite}
        isFavorite={false}
      />
    )
    expect(screen.getByLabelText('Add to favorites')).toBeInTheDocument()
  })

  it('calls onFavoriteToggle when favorite button is clicked', () => {
    const handleFavorite = vi.fn()
    render(
      <RecipeCard
        recipe={mockRecipe}
        onFavoriteToggle={handleFavorite}
        isFavorite={false}
      />
    )
    fireEvent.click(screen.getByLabelText('Add to favorites'))
    expect(handleFavorite).toHaveBeenCalledWith(mockRecipe)
  })

  it('shows "Remove from favorites" aria-label when isFavorite is true', () => {
    render(
      <RecipeCard
        recipe={mockRecipe}
        onFavoriteToggle={vi.fn()}
        isFavorite={true}
      />
    )
    expect(screen.getByLabelText('Remove from favorites')).toBeInTheDocument()
  })

  it('does not propagate click when favorite button is clicked', () => {
    const handleClick = vi.fn()
    const handleFavorite = vi.fn()
    render(
      <RecipeCard
        recipe={mockRecipe}
        onClick={handleClick}
        onFavoriteToggle={handleFavorite}
        isFavorite={false}
      />
    )
    fireEvent.click(screen.getByLabelText('Add to favorites'))
    expect(handleFavorite).toHaveBeenCalled()
    expect(handleClick).not.toHaveBeenCalled()
  })
})
