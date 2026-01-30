/**
 * Format a duration in minutes to a human-readable string.
 * Examples:
 *   - 30 -> "30 min"
 *   - 60 -> "1h"
 *   - 90 -> "1h 30m"
 *
 * @param minutes - Duration in minutes, or null/undefined
 * @returns Formatted string, or null if input is falsy
 */
export function formatTime(minutes: number | null | undefined): string | null {
  if (!minutes) return null
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
}
