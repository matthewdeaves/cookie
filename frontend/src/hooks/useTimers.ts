import { useState, useEffect, useRef, useCallback } from 'react'

export interface Timer {
  id: string
  label: string
  duration: number // seconds
  remaining: number // seconds
  isRunning: boolean
}

export interface UseTimersReturn {
  timers: Timer[]
  addTimer: (label: string, duration: number, autoStart?: boolean) => string
  startTimer: (id: string) => void
  pauseTimer: (id: string) => void
  resetTimer: (id: string) => void
  deleteTimer: (id: string) => void
  toggleTimer: (id: string) => void
}

export function useTimers(onTimerComplete?: (timer: Timer) => void): UseTimersReturn {
  const [timers, setTimers] = useState<Timer[]>([])
  const intervalsRef = useRef<Map<string, number>>(new Map())
  const onCompleteRef = useRef(onTimerComplete)

  // Keep callback ref up to date
  useEffect(() => {
    onCompleteRef.current = onTimerComplete
  }, [onTimerComplete])

  // Cleanup intervals on unmount
  useEffect(() => {
    return () => {
      intervalsRef.current.forEach((intervalId) => {
        clearInterval(intervalId)
      })
    }
  }, [])

  const addTimer = useCallback((label: string, duration: number, autoStart: boolean = true): string => {
    const id = crypto.randomUUID()

    // If autoStart, set up the interval immediately (before setTimers completes)
    if (autoStart) {
      const intervalId = window.setInterval(() => {
        setTimers((prev) =>
          prev.map((timer) => {
            if (timer.id !== id) return timer
            if (!timer.isRunning) return timer

            const newRemaining = timer.remaining - 1

            if (newRemaining <= 0) {
              // Timer completed
              clearInterval(intervalsRef.current.get(id))
              intervalsRef.current.delete(id)
              onCompleteRef.current?.({ ...timer, remaining: 0, isRunning: false })
              return { ...timer, remaining: 0, isRunning: false }
            }

            return { ...timer, remaining: newRemaining }
          })
        )
      }, 1000)

      intervalsRef.current.set(id, intervalId)
    }

    setTimers((prev) => [
      ...prev,
      {
        id,
        label,
        duration,
        remaining: duration,
        isRunning: autoStart,
      },
    ])

    return id
  }, [])

  const startTimer = useCallback((id: string) => {
    // Clear any existing interval for this timer
    const existingInterval = intervalsRef.current.get(id)
    if (existingInterval) {
      clearInterval(existingInterval)
    }

    // Start new interval
    const intervalId = window.setInterval(() => {
      setTimers((prev) =>
        prev.map((timer) => {
          if (timer.id !== id) return timer
          if (!timer.isRunning) return timer

          const newRemaining = timer.remaining - 1

          if (newRemaining <= 0) {
            // Timer completed
            clearInterval(intervalsRef.current.get(id))
            intervalsRef.current.delete(id)
            onCompleteRef.current?.({ ...timer, remaining: 0, isRunning: false })
            return { ...timer, remaining: 0, isRunning: false }
          }

          return { ...timer, remaining: newRemaining }
        })
      )
    }, 1000)

    intervalsRef.current.set(id, intervalId)

    setTimers((prev) =>
      prev.map((timer) =>
        timer.id === id ? { ...timer, isRunning: true } : timer
      )
    )
  }, [])

  const pauseTimer = useCallback((id: string) => {
    // Clear interval
    const intervalId = intervalsRef.current.get(id)
    if (intervalId) {
      clearInterval(intervalId)
      intervalsRef.current.delete(id)
    }

    setTimers((prev) =>
      prev.map((timer) =>
        timer.id === id ? { ...timer, isRunning: false } : timer
      )
    )
  }, [])

  const resetTimer = useCallback((id: string) => {
    // Clear interval
    const intervalId = intervalsRef.current.get(id)
    if (intervalId) {
      clearInterval(intervalId)
      intervalsRef.current.delete(id)
    }

    setTimers((prev) =>
      prev.map((timer) =>
        timer.id === id
          ? { ...timer, remaining: timer.duration, isRunning: false }
          : timer
      )
    )
  }, [])

  const deleteTimer = useCallback((id: string) => {
    // Clear interval
    const intervalId = intervalsRef.current.get(id)
    if (intervalId) {
      clearInterval(intervalId)
      intervalsRef.current.delete(id)
    }

    setTimers((prev) => prev.filter((timer) => timer.id !== id))
  }, [])

  const toggleTimer = useCallback(
    (id: string) => {
      const timer = timers.find((t) => t.id === id)
      if (!timer) return

      if (timer.isRunning) {
        pauseTimer(id)
      } else {
        startTimer(id)
      }
    },
    [timers, pauseTimer, startTimer]
  )

  return {
    timers,
    addTimer,
    startTimer,
    pauseTimer,
    resetTimer,
    deleteTimer,
    toggleTimer,
  }
}

/**
 * Detects time mentions in text and returns durations in seconds.
 *
 * Supports patterns like:
 * - "15 minutes", "15 min", "15m"
 * - "2 hours", "2 hr", "2h"
 * - "30 seconds", "30 sec", "30s"
 */
export function detectTimes(text: string): number[] {
  const times: number[] = []
  const seen = new Set<string>()

  // Patterns for different time units
  const patterns = [
    { regex: /(\d+)\s*(?:hours?|hrs?|h)\b/gi, multiplier: 3600 },
    { regex: /(\d+)\s*(?:minutes?|mins?|m)\b/gi, multiplier: 60 },
    { regex: /(\d+)\s*(?:seconds?|secs?|s)\b/gi, multiplier: 1 },
  ]

  for (const { regex, multiplier } of patterns) {
    let match
    while ((match = regex.exec(text)) !== null) {
      const value = parseInt(match[1], 10)
      const seconds = value * multiplier
      const key = `${match.index}-${value}-${multiplier}`
      if (!seen.has(key) && seconds > 0) {
        seen.add(key)
        times.push(seconds)
      }
    }
  }

  // Sort by appearance in text (earlier matches first)
  return times
}

/**
 * Formats seconds as a human-readable time string.
 * e.g., 90 -> "1:30", 3661 -> "1:01:01"
 */
export function formatTimerDisplay(seconds: number): string {
  const hrs = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
