import { useState, useEffect, type Dispatch, type SetStateAction } from 'react'
import { toast } from 'sonner'
import { api, type RecipeDetail as RecipeDetailType } from '../api/client'

const POLL_INTERVAL = 3000 // 3 seconds
const MAX_POLL_DURATION = 30000 // 30 seconds
const RECENT_THRESHOLD = 60000 // 60 seconds

interface UseTipsPollingOptions {
  recipe: RecipeDetailType | null
  aiAvailable: boolean
  activeTab: string
  setRecipe: Dispatch<SetStateAction<RecipeDetailType | null>>
}

interface UseTipsPollingReturn {
  tips: string[]
  tipsLoading: boolean
  tipsPolling: boolean
  handleGenerateTips: (regenerate?: boolean) => Promise<void>
}

export function useTipsPolling({
  recipe,
  aiAvailable,
  activeTab,
  setRecipe,
}: UseTipsPollingOptions): UseTipsPollingReturn {
  const [tips, setTips] = useState<string[]>([])
  const [tipsLoading, setTipsLoading] = useState(false)
  const [tipsPolling, setTipsPolling] = useState(false)

  // Initialize tips when recipe loads
  useEffect(() => {
    if (recipe) {
      setTips(recipe.ai_tips || [])
    }
  }, [recipe?.id]) // eslint-disable-line react-hooks/exhaustive-deps -- only reset on new recipe

  // Poll for tips if recipe is recently imported and has no tips yet
  useEffect(() => {
    if (!recipe) return

    const recipeAge = Date.now() - new Date(recipe.scraped_at).getTime()
    const isRecent = recipeAge < RECENT_THRESHOLD

    if (!isRecent || tips.length > 0) {
      setTipsPolling(false)
      return
    }

    setTipsPolling(true)
    const startTime = Date.now()

    const interval = setInterval(async () => {
      if (Date.now() - startTime > MAX_POLL_DURATION) {
        clearInterval(interval)
        setTipsPolling(false)
        return
      }

      try {
        const updated = await api.recipes.get(recipe.id)
        if (updated.ai_tips && updated.ai_tips.length > 0) {
          setTips(updated.ai_tips)
          setRecipe((prev) => prev ? { ...prev, ai_tips: updated.ai_tips } : prev)
          clearInterval(interval)
          setTipsPolling(false)
        }
      } catch {
        // Ignore polling errors, will retry on next interval
      }
    }, POLL_INTERVAL)

    return () => {
      clearInterval(interval)
      setTipsPolling(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- recipe object changes on fetch, only care about id/scraped_at/tips changes
  }, [recipe?.id, recipe?.scraped_at, tips.length])

  const handleGenerateTips = async (regenerate: boolean = false) => {
    if (!recipe || tipsLoading) return

    setTipsLoading(true)
    try {
      const result = await api.ai.tips(recipe.id, regenerate)
      setTips(result.tips)
      setRecipe((prev) => prev ? { ...prev, ai_tips: result.tips } : prev)
      toast.success(regenerate ? 'Tips regenerated!' : 'Tips generated!')
    } catch (error) {
      console.error('Failed to generate tips:', error)
      toast.error('Failed to generate tips')
    } finally {
      setTipsLoading(false)
    }
  }

  // Auto-generate tips when viewing Tips tab for old recipes without tips
  useEffect(() => {
    if (
      activeTab === 'tips' &&
      tips.length === 0 &&
      aiAvailable &&
      !tipsLoading &&
      !tipsPolling &&
      recipe
    ) {
      handleGenerateTips(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentionally only trigger on tab change, other deps checked inside
  }, [activeTab])

  return { tips, tipsLoading, tipsPolling, handleGenerateTips }
}
