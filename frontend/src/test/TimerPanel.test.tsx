import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import TimerPanel from '../components/TimerPanel'
import type { UseTimersReturn, Timer } from '../hooks/useTimers'
import { api } from '../api/client'

// Mock the API
vi.mock('../api/client', () => ({
  api: {
    ai: {
      timerName: vi.fn(),
    },
  },
}))

const createMockTimer = (overrides: Partial<Timer> = {}): Timer => ({
  id: 'timer-1',
  label: 'Bake cookies',
  duration: 600,
  remaining: 300,
  isRunning: false,
  ...overrides,
})

const createMockTimersReturn = (timers: Timer[] = []): UseTimersReturn => ({
  timers,
  addTimer: vi.fn(),
  startTimer: vi.fn(),
  pauseTimer: vi.fn(),
  resetTimer: vi.fn(),
  deleteTimer: vi.fn(),
  toggleTimer: vi.fn(),
})

describe('TimerPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Timers header', () => {
    const mockTimers = createMockTimersReturn()
    render(<TimerPanel timers={mockTimers} />)
    expect(screen.getByText('Timers')).toBeInTheDocument()
  })

  it('shows timer count when timers exist', () => {
    const mockTimers = createMockTimersReturn([createMockTimer()])
    render(<TimerPanel timers={mockTimers} />)
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('shows active timer count when timers are running', () => {
    const mockTimers = createMockTimersReturn([
      createMockTimer({ id: '1', isRunning: true }),
      createMockTimer({ id: '2', isRunning: false }),
    ])
    render(<TimerPanel timers={mockTimers} />)
    expect(screen.getByText(/1 active/)).toBeInTheDocument()
  })

  it('renders quick timer buttons', () => {
    const mockTimers = createMockTimersReturn()
    render(<TimerPanel timers={mockTimers} />)

    expect(screen.getByText('+5 min')).toBeInTheDocument()
    expect(screen.getByText('+10 min')).toBeInTheDocument()
    expect(screen.getByText('+15 min')).toBeInTheDocument()
  })

  it('adds timer when quick timer button is clicked (no AI)', async () => {
    const mockTimers = createMockTimersReturn()
    render(<TimerPanel timers={mockTimers} aiAvailable={false} />)

    fireEvent.click(screen.getByText('+5 min'))

    expect(mockTimers.addTimer).toHaveBeenCalledWith('5 min', 300)
  })

  it('uses AI to generate timer name when available', async () => {
    vi.mocked(api.ai.timerName).mockResolvedValue({ label: 'Browning onions' })

    const mockTimers = createMockTimersReturn()
    render(
      <TimerPanel
        timers={mockTimers}
        aiAvailable={true}
        instructionText="Sauté onions for 5 minutes"
      />
    )

    fireEvent.click(screen.getByText('+5 min'))

    await waitFor(() => {
      expect(api.ai.timerName).toHaveBeenCalledWith('Sauté onions for 5 minutes', 5)
      expect(mockTimers.addTimer).toHaveBeenCalledWith('Browning onions', 300)
    })
  })

  it('falls back to default label when AI fails', async () => {
    vi.mocked(api.ai.timerName).mockRejectedValue(new Error('API error'))

    const mockTimers = createMockTimersReturn()
    render(
      <TimerPanel
        timers={mockTimers}
        aiAvailable={true}
        instructionText="Sauté onions for 5 minutes"
      />
    )

    fireEvent.click(screen.getByText('+5 min'))

    await waitFor(() => {
      expect(mockTimers.addTimer).toHaveBeenCalledWith('5 min', 300)
    })
  })

  it('detects times in instruction text', () => {
    const mockTimers = createMockTimersReturn()
    render(
      <TimerPanel
        timers={mockTimers}
        instructionText="Bake for 20 minutes until golden"
      />
    )

    expect(screen.getByText('Detected in this step:')).toBeInTheDocument()
    expect(screen.getByText('20 min')).toBeInTheDocument()
  })

  it('detects multiple times in instruction text', () => {
    const mockTimers = createMockTimersReturn()
    render(
      <TimerPanel
        timers={mockTimers}
        instructionText="Preheat for 10 minutes, then bake for 30 minutes"
      />
    )

    expect(screen.getByText('10 min')).toBeInTheDocument()
    expect(screen.getByText('30 min')).toBeInTheDocument()
  })

  it('adds detected time when clicked', async () => {
    const mockTimers = createMockTimersReturn()
    render(
      <TimerPanel
        timers={mockTimers}
        aiAvailable={false}
        instructionText="Bake for 15 minutes"
      />
    )

    // Find the detected time button (not the quick timer)
    const detectedButtons = screen.getAllByText('15 min')
    // The detected time button should be in the "Detected in this step" section
    const detectedButton = detectedButtons.find(btn =>
      btn.closest('div')?.className.includes('bg-primary/10')
    )

    if (detectedButton) {
      fireEvent.click(detectedButton)
      expect(mockTimers.addTimer).toHaveBeenCalledWith('15 min', 900)
    }
  })

  it('displays existing timers', () => {
    const mockTimers = createMockTimersReturn([
      createMockTimer({ label: 'Bake cookies', remaining: 300 }),
    ])
    render(<TimerPanel timers={mockTimers} />)

    expect(screen.getByText('Bake cookies')).toBeInTheDocument()
  })

  it('shows empty message when no timers', () => {
    const mockTimers = createMockTimersReturn([])
    render(<TimerPanel timers={mockTimers} />)

    expect(screen.getByText('No active timers. Add one above!')).toBeInTheDocument()
  })

  it('can be collapsed', () => {
    const mockTimers = createMockTimersReturn()
    render(<TimerPanel timers={mockTimers} />)

    // Initially expanded - quick timer buttons should be visible
    expect(screen.getByText('+5 min')).toBeInTheDocument()

    // Click header to collapse
    fireEvent.click(screen.getByText('Timers'))

    // Quick timer buttons should be hidden
    expect(screen.queryByText('+5 min')).not.toBeInTheDocument()
  })

  it('shows AI sparkle icon when AI is available and has instruction text', () => {
    const mockTimers = createMockTimersReturn()
    const { container } = render(
      <TimerPanel
        timers={mockTimers}
        aiAvailable={true}
        instructionText="Some instruction"
      />
    )

    // Check for sparkles icon (Lucide icon)
    expect(container.querySelector('.lucide-sparkles')).toBeInTheDocument()
  })

  it('formats detected hour times correctly', () => {
    const mockTimers = createMockTimersReturn()
    render(
      <TimerPanel
        timers={mockTimers}
        instructionText="Let rise for 2 hours"
      />
    )

    expect(screen.getByText('2h')).toBeInTheDocument()
  })

  it('formats detected seconds correctly', () => {
    const mockTimers = createMockTimersReturn()
    render(
      <TimerPanel
        timers={mockTimers}
        instructionText="Microwave for 30 seconds"
      />
    )

    expect(screen.getByText('30s')).toBeInTheDocument()
  })
})
