import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useTimers, detectTimes, formatTimerDisplay } from '../hooks/useTimers'

// Mock crypto.randomUUID
vi.stubGlobal('crypto', {
  randomUUID: () => 'test-uuid-' + Math.random().toString(36).slice(2, 11),
})

describe('detectTimes', () => {
  it('detects minutes', () => {
    expect(detectTimes('bake for 15 minutes')).toContain(900)
  })

  it('detects minute variations', () => {
    expect(detectTimes('cook 5 min')).toContain(300)
    expect(detectTimes('cook 5min')).toContain(300)
    expect(detectTimes('cook 5 mins')).toContain(300)
    expect(detectTimes('wait 10 m')).toContain(600)
  })

  it('detects hours', () => {
    expect(detectTimes('bake for 2 hours')).toContain(7200)
    expect(detectTimes('cook 1 hr')).toContain(3600)
    expect(detectTimes('simmer 3h')).toContain(10800)
  })

  it('detects seconds', () => {
    expect(detectTimes('microwave 30 seconds')).toContain(30)
    expect(detectTimes('wait 45 sec')).toContain(45)
    expect(detectTimes('blend 10s')).toContain(10)
  })

  it('detects multiple times', () => {
    const times = detectTimes('cook 5 min then bake 30 minutes')
    expect(times).toContain(300)
    expect(times).toContain(1800)
    expect(times).toHaveLength(2)
  })

  it('returns empty array for no times', () => {
    expect(detectTimes('mix until smooth')).toEqual([])
    expect(detectTimes('add flour and sugar')).toEqual([])
  })

  it('handles complex instruction text', () => {
    const times = detectTimes(
      'Preheat oven to 350F. Bake for 25 minutes, then let rest 10 minutes before serving.'
    )
    expect(times).toContain(1500) // 25 minutes
    expect(times).toContain(600) // 10 minutes
  })

  it('ignores zero values', () => {
    expect(detectTimes('0 minutes')).toEqual([])
  })
})

describe('formatTimerDisplay', () => {
  it('formats seconds only', () => {
    expect(formatTimerDisplay(45)).toBe('0:45')
  })

  it('formats minutes and seconds', () => {
    expect(formatTimerDisplay(90)).toBe('1:30')
    expect(formatTimerDisplay(300)).toBe('5:00')
  })

  it('formats hours, minutes, and seconds', () => {
    expect(formatTimerDisplay(3661)).toBe('1:01:01')
    expect(formatTimerDisplay(7200)).toBe('2:00:00')
  })

  it('pads with zeros correctly', () => {
    expect(formatTimerDisplay(65)).toBe('1:05')
    expect(formatTimerDisplay(3605)).toBe('1:00:05')
  })
})

describe('useTimers', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('adds timer with correct initial state', () => {
    const { result } = renderHook(() => useTimers())

    act(() => {
      result.current.addTimer('Test Timer', 300)
    })

    expect(result.current.timers).toHaveLength(1)
    expect(result.current.timers[0].label).toBe('Test Timer')
    expect(result.current.timers[0].duration).toBe(300)
    expect(result.current.timers[0].remaining).toBe(300)
    expect(result.current.timers[0].isRunning).toBe(false)
  })

  it('starts and pauses timer', () => {
    const { result } = renderHook(() => useTimers())

    act(() => {
      result.current.addTimer('Test', 300)
    })

    const timerId = result.current.timers[0].id

    act(() => {
      result.current.startTimer(timerId)
    })

    expect(result.current.timers[0].isRunning).toBe(true)

    act(() => {
      result.current.pauseTimer(timerId)
    })

    expect(result.current.timers[0].isRunning).toBe(false)
  })

  it('toggles timer state', () => {
    const { result } = renderHook(() => useTimers())

    act(() => {
      result.current.addTimer('Test', 300)
    })

    const timerId = result.current.timers[0].id

    // Toggle on
    act(() => {
      result.current.toggleTimer(timerId)
    })
    expect(result.current.timers[0].isRunning).toBe(true)

    // Toggle off
    act(() => {
      result.current.toggleTimer(timerId)
    })
    expect(result.current.timers[0].isRunning).toBe(false)
  })

  it('resets timer to initial duration', () => {
    const { result } = renderHook(() => useTimers())

    act(() => {
      result.current.addTimer('Test', 300)
    })

    const timerId = result.current.timers[0].id

    // Start and advance time
    act(() => {
      result.current.startTimer(timerId)
    })

    act(() => {
      vi.advanceTimersByTime(5000)
    })

    expect(result.current.timers[0].remaining).toBe(295)

    // Reset
    act(() => {
      result.current.resetTimer(timerId)
    })

    expect(result.current.timers[0].remaining).toBe(300)
    expect(result.current.timers[0].isRunning).toBe(false)
  })

  it('deletes timer', () => {
    const { result } = renderHook(() => useTimers())

    act(() => {
      result.current.addTimer('Timer 1', 300)
      result.current.addTimer('Timer 2', 600)
    })

    expect(result.current.timers).toHaveLength(2)

    const timerId = result.current.timers[0].id

    act(() => {
      result.current.deleteTimer(timerId)
    })

    expect(result.current.timers).toHaveLength(1)
    expect(result.current.timers[0].label).toBe('Timer 2')
  })

  it('decrements remaining time when running', () => {
    const { result } = renderHook(() => useTimers())

    act(() => {
      result.current.addTimer('Test', 10)
    })

    const timerId = result.current.timers[0].id

    act(() => {
      result.current.startTimer(timerId)
    })

    // Advance 5 seconds
    act(() => {
      vi.advanceTimersByTime(5000)
    })

    expect(result.current.timers[0].remaining).toBe(5)
  })

  it('calls onComplete when timer finishes', () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() => useTimers(onComplete))

    act(() => {
      result.current.addTimer('Test', 3)
    })

    const timerId = result.current.timers[0].id

    act(() => {
      result.current.startTimer(timerId)
    })

    // Advance past completion
    act(() => {
      vi.advanceTimersByTime(4000)
    })

    expect(onComplete).toHaveBeenCalledTimes(1)
    expect(onComplete).toHaveBeenCalledWith(
      expect.objectContaining({
        label: 'Test',
        remaining: 0,
        isRunning: false,
      })
    )
  })

  it('stops timer at zero', () => {
    const { result } = renderHook(() => useTimers())

    act(() => {
      result.current.addTimer('Test', 2)
    })

    const timerId = result.current.timers[0].id

    act(() => {
      result.current.startTimer(timerId)
    })

    act(() => {
      vi.advanceTimersByTime(5000)
    })

    expect(result.current.timers[0].remaining).toBe(0)
    expect(result.current.timers[0].isRunning).toBe(false)
  })

  it('supports multiple simultaneous timers', () => {
    const { result } = renderHook(() => useTimers())

    act(() => {
      result.current.addTimer('Timer 1', 100)
      result.current.addTimer('Timer 2', 200)
    })

    const timer1Id = result.current.timers[0].id
    const timer2Id = result.current.timers[1].id

    act(() => {
      result.current.startTimer(timer1Id)
      result.current.startTimer(timer2Id)
    })

    expect(result.current.timers[0].isRunning).toBe(true)
    expect(result.current.timers[1].isRunning).toBe(true)

    act(() => {
      vi.advanceTimersByTime(10000)
    })

    expect(result.current.timers[0].remaining).toBe(90)
    expect(result.current.timers[1].remaining).toBe(190)
  })
})
