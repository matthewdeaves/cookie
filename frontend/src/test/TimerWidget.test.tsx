import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TimerWidget from '../components/TimerWidget'
import type { Timer } from '../hooks/useTimers'

const createMockTimer = (overrides: Partial<Timer> = {}): Timer => ({
  id: 'timer-1',
  label: 'Bake cookies',
  duration: 600,
  remaining: 300,
  isRunning: false,
  ...overrides,
})

describe('TimerWidget', () => {
  it('renders timer label', () => {
    const timer = createMockTimer()
    render(
      <TimerWidget
        timer={timer}
        onToggle={vi.fn()}
        onReset={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    expect(screen.getByText('Bake cookies')).toBeInTheDocument()
  })

  it('displays remaining time in mm:ss format', () => {
    const timer = createMockTimer({ remaining: 300 })
    render(
      <TimerWidget
        timer={timer}
        onToggle={vi.fn()}
        onReset={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    expect(screen.getByText('5:00')).toBeInTheDocument()
  })

  it('displays remaining time in h:mm:ss format for long timers', () => {
    const timer = createMockTimer({ remaining: 3661 }) // 1 hour, 1 min, 1 sec
    render(
      <TimerWidget
        timer={timer}
        onToggle={vi.fn()}
        onReset={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    expect(screen.getByText('1:01:01')).toBeInTheDocument()
  })

  it('shows Play button when timer is not running', () => {
    const timer = createMockTimer({ isRunning: false })
    render(
      <TimerWidget
        timer={timer}
        onToggle={vi.fn()}
        onReset={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    expect(screen.getByLabelText('Play')).toBeInTheDocument()
  })

  it('shows Pause button when timer is running', () => {
    const timer = createMockTimer({ isRunning: true })
    render(
      <TimerWidget
        timer={timer}
        onToggle={vi.fn()}
        onReset={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    expect(screen.getByLabelText('Pause')).toBeInTheDocument()
  })

  it('calls onToggle when play/pause button is clicked', () => {
    const handleToggle = vi.fn()
    const timer = createMockTimer()
    render(
      <TimerWidget
        timer={timer}
        onToggle={handleToggle}
        onReset={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    fireEvent.click(screen.getByLabelText('Play'))
    expect(handleToggle).toHaveBeenCalled()
  })

  it('calls onReset when reset button is clicked', () => {
    const handleReset = vi.fn()
    const timer = createMockTimer()
    render(
      <TimerWidget
        timer={timer}
        onToggle={vi.fn()}
        onReset={handleReset}
        onDelete={vi.fn()}
      />
    )
    fireEvent.click(screen.getByLabelText('Reset'))
    expect(handleReset).toHaveBeenCalled()
  })

  it('calls onDelete when delete button is clicked', () => {
    const handleDelete = vi.fn()
    const timer = createMockTimer()
    render(
      <TimerWidget
        timer={timer}
        onToggle={vi.fn()}
        onReset={vi.fn()}
        onDelete={handleDelete}
      />
    )
    fireEvent.click(screen.getByLabelText('Delete'))
    expect(handleDelete).toHaveBeenCalled()
  })

  it('hides play/pause and reset buttons when timer is complete', () => {
    const timer = createMockTimer({ remaining: 0 })
    render(
      <TimerWidget
        timer={timer}
        onToggle={vi.fn()}
        onReset={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    expect(screen.queryByLabelText('Play')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Pause')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Reset')).not.toBeInTheDocument()
    // Delete button should still be visible
    expect(screen.getByLabelText('Delete')).toBeInTheDocument()
  })

  it('shows 0:00 when timer is complete', () => {
    const timer = createMockTimer({ remaining: 0 })
    render(
      <TimerWidget
        timer={timer}
        onToggle={vi.fn()}
        onReset={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    expect(screen.getByText('0:00')).toBeInTheDocument()
  })
})
