import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import Collections from '../screens/Collections'
import type { Collection } from '../api/client'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useSearchParams: () => [new URLSearchParams()],
}))

// Mock sonner
vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn(), info: vi.fn() },
}))

// Mock child components
vi.mock('../components/NavHeader', () => ({
  default: () => <div data-testid="nav-header">NavHeader</div>,
}))

vi.mock('../components/Skeletons', () => ({
  CollectionGridSkeleton: ({ count }: { count: number }) => (
    <div data-testid="collection-grid-skeleton">Loading {count} skeletons</div>
  ),
}))

// Mock API client
vi.mock('../api/client', () => ({
  api: {
    collections: {
      list: vi.fn(() => Promise.resolve([])),
      create: vi.fn(),
      addRecipe: vi.fn(),
    },
  },
}))

describe('Collections', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', async () => {
    render(<Collections />)
    await waitFor(() => {
      expect(screen.getByTestId('nav-header')).toBeInTheDocument()
    })
  })

  it('shows loading skeleton initially', () => {
    render(<Collections />)
    expect(screen.getByTestId('collection-grid-skeleton')).toBeInTheDocument()
  })

  it('shows page heading', () => {
    render(<Collections />)
    expect(screen.getByText('Collections')).toBeInTheDocument()
  })

  it('shows New button', () => {
    render(<Collections />)
    expect(screen.getByText('New')).toBeInTheDocument()
  })

  it('shows empty state when no collections exist', async () => {
    render(<Collections />)
    await waitFor(() => {
      expect(screen.getByText('No collections yet')).toBeInTheDocument()
    })
  })

  it('shows create prompt in empty state', async () => {
    render(<Collections />)
    await waitFor(() => {
      expect(screen.getByText('Create one to organize your recipes!')).toBeInTheDocument()
    })
  })

  it('shows Create Collection button in empty state', async () => {
    render(<Collections />)
    await waitFor(() => {
      expect(screen.getByText('Create Collection')).toBeInTheDocument()
    })
  })

  it('renders collection cards when collections exist', async () => {
    const mockCollections: Collection[] = [
      {
        id: 1,
        name: 'Weeknight Dinners',
        description: '',
        recipe_count: 5,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 2,
        name: 'Holiday Baking',
        description: '',
        recipe_count: 3,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
    ]

    const { api } = await import('../api/client')
    vi.mocked(api.collections.list).mockResolvedValueOnce(mockCollections)

    render(<Collections />)
    await waitFor(() => {
      expect(screen.getByText('Weeknight Dinners')).toBeInTheDocument()
      expect(screen.getByText('Holiday Baking')).toBeInTheDocument()
    })
  })

  it('shows recipe count for each collection', async () => {
    const mockCollections: Collection[] = [
      {
        id: 1,
        name: 'Quick Meals',
        description: '',
        recipe_count: 7,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    const { api } = await import('../api/client')
    vi.mocked(api.collections.list).mockResolvedValueOnce(mockCollections)

    render(<Collections />)
    await waitFor(() => {
      expect(screen.getByText('7 recipes')).toBeInTheDocument()
    })
  })

  it('shows create form when New button is clicked', async () => {
    render(<Collections />)
    await waitFor(() => {
      expect(screen.queryByTestId('collection-grid-skeleton')).not.toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('New'))
    expect(screen.getByPlaceholderText('Collection name')).toBeInTheDocument()
  })
})
