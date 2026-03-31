import { useState } from 'react'
import { toast } from 'sonner'
import { api, type RecipeDetail as RecipeDetailType, type ScaleResponse } from '../api/client'
import { handleQuotaError } from '../lib/utils'

interface UseServingScaleReturn {
  servings: number | null
  scaledData: ScaleResponse | null
  scalingLoading: boolean
  setServings: (s: number | null) => void
  setScaledData: (d: ScaleResponse | null) => void
  handleServingChange: (delta: number) => Promise<void>
}

/**
 * Manages serving count and AI-powered ingredient scaling.
 */
export function useServingScale(
  recipe: RecipeDetailType | null,
  profileId: number | undefined
): UseServingScaleReturn {
  const [servings, setServings] = useState<number | null>(null)
  const [scaledData, setScaledData] = useState<ScaleResponse | null>(null)
  const [scalingLoading, setScalingLoading] = useState(false)

  const handleServingChange = async (delta: number) => {
    if (!servings || !recipe || !profileId) return
    const newServings = Math.max(1, servings + delta)
    setServings(newServings)

    if (newServings === recipe.servings) {
      setScaledData(null)
      return
    }

    setScalingLoading(true)
    try {
      const result = await api.ai.scale(recipe.id, newServings, profileId)
      setScaledData(result)
      if (result.notes.length > 0) {
        toast.info(result.notes[0])
      }
    } catch (error) {
      console.error('Failed to scale recipe:', error)
      handleQuotaError(error, 'Failed to scale ingredients')
      setServings(servings)
    } finally {
      setScalingLoading(false)
    }
  }

  return { servings, scaledData, scalingLoading, setServings, setScaledData, handleServingChange }
}
