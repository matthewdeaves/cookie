import type { MutableRefObject, Dispatch, SetStateAction } from 'react'
import type { Timer } from './useTimers'

/**
 * Creates a timer tick function that decrements the remaining time
 * and handles completion. Used by both addTimer and startTimer.
 */
export function createTimerTick(
  id: string,
  intervalsRef: MutableRefObject<Map<string, number>>,
  onComplete: MutableRefObject<((timer: Timer) => void) | undefined>,
  setTimers: Dispatch<SetStateAction<Timer[]>>
): () => void {
  return () => {
    setTimers((prev) =>
      prev.map((timer) => {
        if (timer.id !== id) return timer
        if (!timer.isRunning) return timer

        const newRemaining = timer.remaining - 1

        if (newRemaining <= 0) {
          clearInterval(intervalsRef.current.get(id))
          intervalsRef.current.delete(id)
          onComplete.current?.({ ...timer, remaining: 0, isRunning: false })
          return { ...timer, remaining: 0, isRunning: false }
        }

        return { ...timer, remaining: newRemaining }
      })
    )
  }
}

/**
 * Clears an interval for a timer and removes it from the map.
 */
export function clearTimerInterval(
  id: string,
  intervalsRef: MutableRefObject<Map<string, number>>
): void {
  const intervalId = intervalsRef.current.get(id)
  if (intervalId) {
    clearInterval(intervalId)
    intervalsRef.current.delete(id)
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
