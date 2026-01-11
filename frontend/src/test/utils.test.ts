import { describe, it, expect } from 'vitest'
import { formatNutritionKey } from '../lib/utils'

describe('formatNutritionKey', () => {
  describe('camelCase with Content suffix', () => {
    it('formats carbohydrateContent', () => {
      expect(formatNutritionKey('carbohydrateContent')).toBe('Carbohydrate')
    })

    it('formats cholesterolContent', () => {
      expect(formatNutritionKey('cholesterolContent')).toBe('Cholesterol')
    })

    it('formats proteinContent', () => {
      expect(formatNutritionKey('proteinContent')).toBe('Protein')
    })

    it('formats fatContent', () => {
      expect(formatNutritionKey('fatContent')).toBe('Fat')
    })

    it('formats saturatedFatContent', () => {
      expect(formatNutritionKey('saturatedFatContent')).toBe('Saturated Fat')
    })

    it('formats sodiumContent', () => {
      expect(formatNutritionKey('sodiumContent')).toBe('Sodium')
    })

    it('formats fiberContent', () => {
      expect(formatNutritionKey('fiberContent')).toBe('Fiber')
    })

    it('formats sugarContent', () => {
      expect(formatNutritionKey('sugarContent')).toBe('Sugar')
    })
  })

  describe('simple camelCase without suffix', () => {
    it('formats calories', () => {
      expect(formatNutritionKey('calories')).toBe('Calories')
    })

    it('formats servingSize', () => {
      expect(formatNutritionKey('servingSize')).toBe('Serving Size')
    })
  })

  describe('snake_case', () => {
    it('formats saturated_fat', () => {
      expect(formatNutritionKey('saturated_fat')).toBe('Saturated Fat')
    })

    it('formats total_carbs', () => {
      expect(formatNutritionKey('total_carbs')).toBe('Total Carbs')
    })

    it('formats dietary_fiber', () => {
      expect(formatNutritionKey('dietary_fiber')).toBe('Dietary Fiber')
    })
  })

  describe('edge cases', () => {
    it('handles empty string', () => {
      expect(formatNutritionKey('')).toBe('')
    })

    it('handles single word', () => {
      expect(formatNutritionKey('protein')).toBe('Protein')
    })

    it('handles already capitalized', () => {
      expect(formatNutritionKey('Calories')).toBe('Calories')
    })
  })
})
