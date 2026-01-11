import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
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
