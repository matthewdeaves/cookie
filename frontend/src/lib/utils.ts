import { type ClassValue, clsx } from 'clsx'
import { toast } from 'sonner'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Handle API errors with quota-aware messaging.
 * Returns true if the error was a quota error (handled), false otherwise.
 */
export function handleQuotaError(error: unknown, fallbackMessage: string): boolean {
  const err = error as { status?: number; body?: { error?: string; resets_at?: string } }
  if (err?.status === 429 && err?.body?.error === 'quota_exceeded') {
    const resetsAt = err.body.resets_at
    const resetTime = resetsAt
      ? new Date(resetsAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : 'midnight'
    toast.error(`Daily limit reached. Resets at ${resetTime}.`)
    return true
  }
  toast.error(fallbackMessage)
  return false
}

/**
 * Extract the resets_at ISO string from a quota_exceeded 429 error.
 * Returns undefined if the error is not a quota error or has no reset time.
 */
export function extractQuotaResetsAt(error: unknown): string | undefined {
  const err = error as { status?: number; body?: { error?: string; resets_at?: string } }
  if (err?.status === 429 && err?.body?.error === 'quota_exceeded') {
    return err.body?.resets_at
  }
  return undefined
}

/**
 * Format nutrition key into human readable label.
 * Converts camelCase keys like 'carbohydrateContent' to 'Carbohydrate'.
 * Also handles snake_case like 'saturated_fat' to 'Saturated Fat'.
 */
export function formatNutritionKey(key: string): string {
  if (!key) return ''

  // Remove "Content" suffix
  let formatted = key.replace(/Content$/, '')

  // Handle snake_case
  if (formatted.includes('_')) {
    return formatted
      .split('_')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ')
  }

  // Handle camelCase - insert space before capitals
  formatted = formatted.replace(/([a-z])([A-Z])/g, '$1 $2')

  // Capitalize first letter
  return formatted.charAt(0).toUpperCase() + formatted.slice(1)
}
