import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  RecipeCardSkeleton,
  RecipeGridSkeleton,
  CollectionCardSkeleton,
  CollectionGridSkeleton,
  RecipeDetailSkeleton,
  LoadingSpinner,
  LoadingState,
  SearchResultSkeleton,
  SearchGridSkeleton,
} from '../components/Skeletons'

describe('RecipeCardSkeleton', () => {
  it('renders without crashing', () => {
    const { container } = render(<RecipeCardSkeleton />)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('has animate-pulse classes for loading effect', () => {
    const { container } = render(<RecipeCardSkeleton />)
    const pulsingElements = container.querySelectorAll('.animate-pulse')
    expect(pulsingElements.length).toBeGreaterThan(0)
  })
})

describe('RecipeGridSkeleton', () => {
  it('renders default 8 skeleton cards', () => {
    const { container } = render(<RecipeGridSkeleton />)
    const cards = container.querySelectorAll('.overflow-hidden.rounded-lg')
    expect(cards).toHaveLength(8)
  })

  it('renders custom number of skeleton cards', () => {
    const { container } = render(<RecipeGridSkeleton count={4} />)
    const cards = container.querySelectorAll('.overflow-hidden.rounded-lg')
    expect(cards).toHaveLength(4)
  })
})

describe('CollectionCardSkeleton', () => {
  it('renders without crashing', () => {
    const { container } = render(<CollectionCardSkeleton />)
    expect(container.firstChild).toBeInTheDocument()
  })
})

describe('CollectionGridSkeleton', () => {
  it('renders default 8 skeleton cards', () => {
    const { container } = render(<CollectionGridSkeleton />)
    const cards = container.querySelectorAll('.overflow-hidden.rounded-lg')
    expect(cards).toHaveLength(8)
  })

  it('renders custom number of skeleton cards', () => {
    const { container } = render(<CollectionGridSkeleton count={3} />)
    const cards = container.querySelectorAll('.overflow-hidden.rounded-lg')
    expect(cards).toHaveLength(3)
  })
})

describe('RecipeDetailSkeleton', () => {
  it('renders hero section skeleton', () => {
    const { container } = render(<RecipeDetailSkeleton />)
    // Has min-h-screen class for full page skeleton
    expect(container.querySelector('.min-h-screen')).toBeInTheDocument()
  })

  it('renders back button placeholder', () => {
    const { container } = render(<RecipeDetailSkeleton />)
    // Check for the rounded-full skeleton in the back button position
    const backButton = container.querySelector('.absolute.left-4.top-4')
    expect(backButton).toBeInTheDocument()
  })

  it('renders content skeleton items', () => {
    const { container } = render(<RecipeDetailSkeleton />)
    // Check for 6 content skeleton rows
    const contentRows = container.querySelectorAll('.flex.items-start.gap-3')
    expect(contentRows).toHaveLength(6)
  })
})

describe('LoadingSpinner', () => {
  it('renders a spinning element', () => {
    const { container } = render(<LoadingSpinner />)
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('accepts custom className', () => {
    const { container } = render(<LoadingSpinner className="my-custom-class" />)
    expect(container.querySelector('.my-custom-class')).toBeInTheDocument()
  })
})

describe('LoadingState', () => {
  it('renders default loading message', () => {
    render(<LoadingState />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders custom loading message', () => {
    render(<LoadingState message="Fetching recipes..." />)
    expect(screen.getByText('Fetching recipes...')).toBeInTheDocument()
  })

  it('renders a spinning element', () => {
    const { container } = render(<LoadingState />)
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()
  })
})

describe('SearchResultSkeleton', () => {
  it('renders without crashing', () => {
    const { container } = render(<SearchResultSkeleton />)
    expect(container.firstChild).toBeInTheDocument()
  })
})

describe('SearchGridSkeleton', () => {
  it('renders default 6 skeleton cards', () => {
    const { container } = render(<SearchGridSkeleton />)
    const cards = container.querySelectorAll('.overflow-hidden.rounded-lg')
    expect(cards).toHaveLength(6)
  })

  it('renders custom number of skeleton cards', () => {
    const { container } = render(<SearchGridSkeleton count={3} />)
    const cards = container.querySelectorAll('.overflow-hidden.rounded-lg')
    expect(cards).toHaveLength(3)
  })
})
