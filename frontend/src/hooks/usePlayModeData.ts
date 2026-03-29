import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { api, type RecipeDetail } from '../api/client'
import { playTimerAlert } from '../lib/audio'

export function usePlayModeData(recipeId: number) {
  const navigate = useNavigate()
  const [recipe, setRecipe] = useState<RecipeDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [aiAvailable, setAiAvailable] = useState(false)

  useEffect(() => {
    if (!recipeId) return
    const load = async () => {
      try {
        const [recipeData, aiStatus] = await Promise.all([
          api.recipes.get(recipeId),
          api.ai.status(),
        ])
        setRecipe(recipeData)
        setAiAvailable(aiStatus.available)
      } catch (error) {
        console.error('Failed to load recipe:', error)
        toast.error('Failed to load recipe')
        navigate(-1)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [recipeId, navigate])

  return { recipe, loading, aiAvailable }
}

export function useTimerComplete() {
  return useCallback((timer: { label: string }) => {
    playTimerAlert()
    toast.success(`Timer complete: ${timer.label}`, { duration: 10000 })
    try {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Timer Complete!', {
          body: timer.label,
          icon: '/favicon.ico',
        })
      }
    } catch {
      // Notification not supported or blocked
    }
  }, [])
}

export function getInstructions(recipe: RecipeDetail | null): string[] {
  if (!recipe) return []
  if (recipe.instructions.length > 0) return recipe.instructions
  if (recipe.instructions_text) {
    return recipe.instructions_text.split('\n').filter((s) => s.trim())
  }
  return []
}
