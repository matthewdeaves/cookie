import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import ProfileSelector from '../screens/ProfileSelector'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

// Mock sonner
vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}))

// Mock utils
vi.mock('../lib/utils', () => ({
  cn: (...args: string[]) => args.filter(Boolean).join(' '),
}))

// Mock profile context
const mockSelectProfile = vi.fn()
vi.mock('../contexts/ProfileContext', () => ({
  useProfile: () => ({
    selectProfile: mockSelectProfile,
  }),
}))

// Mock API client
vi.mock('../api/client', () => ({
  api: {
    profiles: {
      list: vi.fn(() => Promise.resolve([])),
      create: vi.fn(() => Promise.resolve({ id: 3, name: 'Charlie', avatar_color: '#d97850', theme: 'light', unit_preference: 'metric' })),
    },
  },
}))

describe('ProfileSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSelectProfile.mockResolvedValue(undefined)
  })

  it('renders loading state initially', () => {
    render(<ProfileSelector />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders without crashing after loading', async () => {
    render(<ProfileSelector />)
    await waitFor(() => {
      expect(screen.getByText('Cookie')).toBeInTheDocument()
    })
  })

  it('shows "Who\'s cooking today?" subtitle', async () => {
    render(<ProfileSelector />)
    await waitFor(() => {
      expect(screen.getByText("Who's cooking today?")).toBeInTheDocument()
    })
  })

  it('shows Add Profile button when no profiles exist', async () => {
    render(<ProfileSelector />)
    await waitFor(() => {
      expect(screen.getByText('Add Profile')).toBeInTheDocument()
    })
  })

  it('renders profiles when they exist', async () => {
    const { api } = await import('../api/client')
    vi.mocked(api.profiles.list).mockResolvedValueOnce([
      { id: 1, name: 'Alice', avatar_color: '#d97850', theme: 'light', unit_preference: 'metric', created_at: '', stats: { favorites: 0, collections: 0, collection_items: 0, remixes: 0, view_history: 0, scaling_cache: 0, discover_cache: 0 } },
      { id: 2, name: 'Bob', avatar_color: '#8fae6f', theme: 'dark', unit_preference: 'us', created_at: '', stats: { favorites: 0, collections: 0, collection_items: 0, remixes: 0, view_history: 0, scaling_cache: 0, discover_cache: 0 } },
    ] as never)

    render(<ProfileSelector />)
    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument()
      expect(screen.getByText('Bob')).toBeInTheDocument()
    })
  })

  it('shows profile initials in avatar circles', async () => {
    const { api } = await import('../api/client')
    vi.mocked(api.profiles.list).mockResolvedValueOnce([
      { id: 1, name: 'Alice', avatar_color: '#d97850', theme: 'light', unit_preference: 'metric', created_at: '', stats: { favorites: 0, collections: 0, collection_items: 0, remixes: 0, view_history: 0, scaling_cache: 0, discover_cache: 0 } },
    ] as never)

    render(<ProfileSelector />)
    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument()
    })
  })

  it('navigates to /home when a profile is selected', async () => {
    const profile = { id: 1, name: 'Alice', avatar_color: '#d97850', theme: 'light', unit_preference: 'metric', created_at: '', stats: { favorites: 0, collections: 0, collection_items: 0, remixes: 0, view_history: 0, scaling_cache: 0, discover_cache: 0 } }
    const { api } = await import('../api/client')
    vi.mocked(api.profiles.list).mockResolvedValueOnce([profile] as never)

    render(<ProfileSelector />)
    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Alice'))
    await waitFor(() => {
      expect(mockSelectProfile).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/home')
    })
  })

  it('shows create profile form when Add Profile is clicked', async () => {
    render(<ProfileSelector />)
    await waitFor(() => {
      expect(screen.getByText('Add Profile')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Add Profile'))
    expect(screen.getByText('Create Profile')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Enter your name')).toBeInTheDocument()
    expect(screen.getByText('Choose a color')).toBeInTheDocument()
  })

  it('has disabled Create button when name is empty', async () => {
    render(<ProfileSelector />)
    await waitFor(() => {
      expect(screen.getByText('Add Profile')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Add Profile'))
    const createButton = screen.getByText('Create')
    expect(createButton).toBeDisabled()
  })

  it('submits create profile form', async () => {
    render(<ProfileSelector />)
    await waitFor(() => {
      expect(screen.getByText('Add Profile')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Add Profile'))
    fireEvent.change(screen.getByPlaceholderText('Enter your name'), {
      target: { value: 'Charlie' },
    })
    fireEvent.submit(screen.getByPlaceholderText('Enter your name').closest('form')!)

    await waitFor(() => {
      expect(mockSelectProfile).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/home')
    })
  })

  it('hides create form when Cancel is clicked', async () => {
    render(<ProfileSelector />)
    await waitFor(() => {
      expect(screen.getByText('Add Profile')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Add Profile'))
    expect(screen.getByText('Create Profile')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Cancel'))
    expect(screen.queryByText('Create Profile')).not.toBeInTheDocument()
  })
})
