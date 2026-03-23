import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import PlayMode from '../screens/PlayMode'
import type { RecipeDetail } from '../api/client'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useParams: () => ({ id: '1' }),
}))

// Mock sonner
vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn(), info: vi.fn() },
}))

// Mock lib/utils
vi.mock('../lib/utils', () => ({
  cn: (...args: string[]) => args.filter(Boolean).join(' '),
}))

// Mock audio
vi.mock('../lib/audio', () => ({
  unlockAudio: vi.fn(),
  playTimerAlert: vi.fn(),
}))

// Mock hooks
vi.mock('../hooks/useTimers', () => ({
  useTimers: () => ({
    timers: [],
    addTimer: vi.fn(),
    removeTimer: vi.fn(),
    toggleTimer: vi.fn(),
  }),
}))

vi.mock('../hooks/useWakeLock', () => ({
  useWakeLock: vi.fn(),
}))

// Mock child components
vi.mock('../components/TimerPanel', () => ({
  default: () => <div data-testid="timer-panel">TimerPanel</div>,
}))

vi.mock('../components/Skeletons', () => ({
  LoadingSpinner: ({ className }: { className?: string }) => (
    <div data-testid="loading-spinner" className={className}>Loading...</div>
  ),
}))

// Recipe mock data
const mockRecipe: RecipeDetail = {
  id: 1,
  title: 'Test Pasta',
  host: 'example.com',
  image_url: 'https://example.com/img.jpg',
  image: null,
  total_time: 30,
  rating: 4.5,
  is_remix: false,
  scraped_at: '2024-01-01T00:00:00Z',
  source_url: 'https://example.com/pasta',
  canonical_url: 'https://example.com/pasta',
  site_name: 'Example',
  author: 'Chef Test',
  description: 'A test recipe',
  ingredients: ['200g pasta', '100g sauce'],
  ingredient_groups: [],
  instructions: ['Boil water', 'Cook pasta', 'Add sauce'],
  instructions_text: '',
  prep_time: 10,
  cook_time: 20,
  yields: '4 servings',
  servings: 4,
  category: 'Main',
  cuisine: 'Italian',
  cooking_method: 'Boiling',
  keywords: ['pasta'],
  dietary_restrictions: [],
  equipment: [],
  nutrition: {},
  rating_count: 100,
  language: 'en',
  links: [],
  ai_tips: [],
  remix_profile_id: null,
  remixed_from_id: null,
  linked_recipes: [],
  updated_at: '2024-01-01T00:00:00Z',
}

// Mock API client
vi.mock('../api/client', () => ({
  api: {
    recipes: {
      get: vi.fn(() => Promise.resolve(mockRecipe)),
    },
    ai: {
      status: vi.fn(() =>
        Promise.resolve({
          available: false,
          configured: false,
          valid: false,
          default_model: '',
          error: null,
          error_code: null,
        })
      ),
    },
  },
}))

describe('PlayMode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    render(<PlayMode />)
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('renders recipe title after loading', async () => {
    render(<PlayMode />)
    await waitFor(() => {
      expect(screen.getByText('Test Pasta')).toBeInTheDocument()
    })
  })

  it('shows step counter', async () => {
    render(<PlayMode />)
    await waitFor(() => {
      expect(screen.getByText('Step 1 of 3')).toBeInTheDocument()
    })
  })

  it('shows first instruction step', async () => {
    render(<PlayMode />)
    await waitFor(() => {
      expect(screen.getByText('Boil water')).toBeInTheDocument()
    })
  })

  it('has Previous and Next navigation buttons', async () => {
    render(<PlayMode />)
    await waitFor(() => {
      expect(screen.getByText('Previous')).toBeInTheDocument()
      expect(screen.getByText('Next')).toBeInTheDocument()
    })
  })

  it('Previous button is disabled on first step', async () => {
    render(<PlayMode />)
    await waitFor(() => {
      const prevButton = screen.getByText('Previous').closest('button')
      expect(prevButton).toBeDisabled()
    })
  })

  it('navigates to next step when Next is clicked', async () => {
    render(<PlayMode />)
    await waitFor(() => {
      expect(screen.getByText('Boil water')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Next'))
    expect(screen.getByText('Cook pasta')).toBeInTheDocument()
    expect(screen.getByText('Step 2 of 3')).toBeInTheDocument()
  })

  it('has an exit button with aria-label', async () => {
    render(<PlayMode />)
    await waitFor(() => {
      expect(screen.getByLabelText('Exit play mode')).toBeInTheDocument()
    })
  })

  it('navigates back when exit button is clicked', async () => {
    render(<PlayMode />)
    await waitFor(() => {
      expect(screen.getByLabelText('Exit play mode')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByLabelText('Exit play mode'))
    expect(mockNavigate).toHaveBeenCalledWith(-1)
  })

  it('renders timer panel', async () => {
    render(<PlayMode />)
    await waitFor(() => {
      expect(screen.getByTestId('timer-panel')).toBeInTheDocument()
    })
  })

  it('shows no instructions message when recipe has no steps', async () => {
    const { api } = await import('../api/client')
    vi.mocked(api.recipes.get).mockResolvedValueOnce({
      ...mockRecipe,
      instructions: [],
      instructions_text: '',
    })

    render(<PlayMode />)
    await waitFor(() => {
      expect(screen.getByText('No instructions available for this recipe.')).toBeInTheDocument()
    })
  })
})
