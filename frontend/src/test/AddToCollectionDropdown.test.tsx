import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import AddToCollectionDropdown from '../components/AddToCollectionDropdown'
import { api } from '../api/client'

// Mock the API
vi.mock('../api/client', () => ({
  api: {
    collections: {
      list: vi.fn(),
      addRecipe: vi.fn(),
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

describe('AddToCollectionDropdown', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the folder button', () => {
    render(
      <AddToCollectionDropdown recipeId={1} onCreateNew={vi.fn()} />
    )
    expect(screen.getByTitle('Add to collection')).toBeInTheDocument()
  })

  it('opens dropdown when button is clicked', async () => {
    vi.mocked(api.collections.list).mockResolvedValue([])

    render(
      <AddToCollectionDropdown recipeId={1} onCreateNew={vi.fn()} />
    )

    fireEvent.click(screen.getByTitle('Add to collection'))

    await waitFor(() => {
      expect(screen.getByText('Add to Collection')).toBeInTheDocument()
    })
  })

  it('shows loading state while fetching collections', async () => {
    vi.mocked(api.collections.list).mockImplementation(
      () => new Promise(() => {})
    )

    render(
      <AddToCollectionDropdown recipeId={1} onCreateNew={vi.fn()} />
    )

    fireEvent.click(screen.getByTitle('Add to collection'))

    await waitFor(() => {
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })
  })

  it('displays collections when loaded', async () => {
    vi.mocked(api.collections.list).mockResolvedValue([
      { id: 1, name: 'Favorites', description: '', recipe_count: 0, created_at: '', updated_at: '' },
      { id: 2, name: 'Quick Meals', description: '', recipe_count: 0, created_at: '', updated_at: '' },
    ])

    render(
      <AddToCollectionDropdown recipeId={1} onCreateNew={vi.fn()} />
    )

    fireEvent.click(screen.getByTitle('Add to collection'))

    await waitFor(() => {
      expect(screen.getByText('Favorites')).toBeInTheDocument()
      expect(screen.getByText('Quick Meals')).toBeInTheDocument()
    })
  })

  it('shows empty message when no collections exist', async () => {
    vi.mocked(api.collections.list).mockResolvedValue([])

    render(
      <AddToCollectionDropdown recipeId={1} onCreateNew={vi.fn()} />
    )

    fireEvent.click(screen.getByTitle('Add to collection'))

    await waitFor(() => {
      expect(screen.getByText('No collections yet')).toBeInTheDocument()
    })
  })

  it('shows Create New Collection option', async () => {
    vi.mocked(api.collections.list).mockResolvedValue([])

    render(
      <AddToCollectionDropdown recipeId={1} onCreateNew={vi.fn()} />
    )

    fireEvent.click(screen.getByTitle('Add to collection'))

    await waitFor(() => {
      expect(screen.getByText('Create New Collection')).toBeInTheDocument()
    })
  })

  it('calls onCreateNew when Create New Collection is clicked', async () => {
    vi.mocked(api.collections.list).mockResolvedValue([])

    const handleCreateNew = vi.fn()
    render(
      <AddToCollectionDropdown recipeId={1} onCreateNew={handleCreateNew} />
    )

    fireEvent.click(screen.getByTitle('Add to collection'))

    await waitFor(() => {
      expect(screen.getByText('Create New Collection')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Create New Collection'))

    expect(handleCreateNew).toHaveBeenCalled()
  })

  it('adds recipe to collection when collection is clicked', async () => {
    vi.mocked(api.collections.list).mockResolvedValue([
      { id: 1, name: 'Favorites', description: '', recipe_count: 0, created_at: '', updated_at: '' },
    ])
    vi.mocked(api.collections.addRecipe).mockResolvedValue({} as never)

    render(
      <AddToCollectionDropdown recipeId={42} onCreateNew={vi.fn()} />
    )

    fireEvent.click(screen.getByTitle('Add to collection'))

    await waitFor(() => {
      expect(screen.getByText('Favorites')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Favorites'))

    await waitFor(() => {
      expect(api.collections.addRecipe).toHaveBeenCalledWith(1, 42)
    })
  })

  it('closes dropdown after adding recipe', async () => {
    vi.mocked(api.collections.list).mockResolvedValue([
      { id: 1, name: 'Favorites', description: '', recipe_count: 0, created_at: '', updated_at: '' },
    ])
    vi.mocked(api.collections.addRecipe).mockResolvedValue({} as never)

    render(
      <AddToCollectionDropdown recipeId={1} onCreateNew={vi.fn()} />
    )

    fireEvent.click(screen.getByTitle('Add to collection'))

    await waitFor(() => {
      expect(screen.getByText('Favorites')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Favorites'))

    await waitFor(() => {
      expect(screen.queryByText('Favorites')).not.toBeInTheDocument()
    })
  })

  it('closes dropdown when clicking outside', async () => {
    vi.mocked(api.collections.list).mockResolvedValue([])

    render(
      <div>
        <AddToCollectionDropdown recipeId={1} onCreateNew={vi.fn()} />
        <button data-testid="outside">Outside</button>
      </div>
    )

    fireEvent.click(screen.getByTitle('Add to collection'))

    await waitFor(() => {
      expect(screen.getByText('Add to Collection')).toBeInTheDocument()
    })

    fireEvent.mouseDown(screen.getByTestId('outside'))

    await waitFor(() => {
      expect(screen.queryByText('Add to Collection')).not.toBeInTheDocument()
    })
  })

  it('shows Adding... while adding recipe', async () => {
    vi.mocked(api.collections.list).mockResolvedValue([
      { id: 1, name: 'Favorites', description: '', recipe_count: 0, created_at: '', updated_at: '' },
    ])
    vi.mocked(api.collections.addRecipe).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    )

    render(
      <AddToCollectionDropdown recipeId={1} onCreateNew={vi.fn()} />
    )

    fireEvent.click(screen.getByTitle('Add to collection'))

    await waitFor(() => {
      expect(screen.getByText('Favorites')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Favorites'))

    await waitFor(() => {
      expect(screen.getByText('Adding...')).toBeInTheDocument()
    })
  })
})
