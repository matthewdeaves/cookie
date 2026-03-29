import { useState, useEffect, useRef, useCallback } from 'react'
import { createTimerTick, clearTimerInterval } from './timerUtils'

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

  useEffect(() => {
    onCompleteRef.current = onTimerComplete
  }, [onTimerComplete])

  useEffect(() => {
    const intervals = intervalsRef.current
    return () => {
      intervals.forEach((intervalId) => clearInterval(intervalId))
    }
  }, [])

  const addTimer = useCallback((label: string, duration: number, autoStart: boolean = true): string => {
    const id = crypto.randomUUID()

    setTimers((prev) => [
      ...prev,
      { id, label, duration, remaining: duration, isRunning: autoStart },
    ])

    if (autoStart) {
      const tick = createTimerTick(id, intervalsRef, onCompleteRef, setTimers)
      const intervalId = window.setInterval(tick, 1000)
      intervalsRef.current.set(id, intervalId)
    }

    return id
  }, [])

  const startTimer = useCallback((id: string) => {
    clearTimerInterval(id, intervalsRef)

    const tick = createTimerTick(id, intervalsRef, onCompleteRef, setTimers)
    const intervalId = window.setInterval(tick, 1000)
    intervalsRef.current.set(id, intervalId)

    setTimers((prev) =>
      prev.map((timer) =>
        timer.id === id ? { ...timer, isRunning: true } : timer
      )
    )
  }, [])

  const pauseTimer = useCallback((id: string) => {
    clearTimerInterval(id, intervalsRef)
    setTimers((prev) =>
      prev.map((timer) =>
        timer.id === id ? { ...timer, isRunning: false } : timer
      )
    )
  }, [])

  const resetTimer = useCallback((id: string) => {
    clearTimerInterval(id, intervalsRef)
    setTimers((prev) =>
      prev.map((timer) =>
        timer.id === id
          ? { ...timer, remaining: timer.duration, isRunning: false }
          : timer
      )
    )
  }, [])

  const deleteTimer = useCallback((id: string) => {
    clearTimerInterval(id, intervalsRef)
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

  return { timers, addTimer, startTimer, pauseTimer, resetTimer, deleteTimer, toggleTimer }
}

// Re-export utilities for consumers
export { detectTimes, formatTimerDisplay } from './timerUtils'
