import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'
import {
  api,
  type RecipeDetail as RecipeDetailType,
  type ScaleResponse,
} from '../api/client'
import { useProfile } from '../contexts/ProfileContext'
import { useAIStatus } from '../contexts/AIStatusContext'

type Tab = 'ingredients' | 'instructions' | 'nutrition' | 'tips'

export function useRecipeDetail() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const recipeId = Number(id)
  const { profile, isFavorite, toggleFavorite } = useProfile()
  const aiStatus = useAIStatus()

  const [recipe, setRecipe] = useState<RecipeDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<Tab>('ingredients')
  const [metaExpanded, setMetaExpanded] = useState(true)
  const [servings, setServings] = useState<number | null>(null)
  const [showRemixModal, setShowRemixModal] = useState(false)
  const [scaledData, setScaledData] = useState<ScaleResponse | null>(null)
  const [scalingLoading, setScalingLoading] = useState(false)
  const [tips, setTips] = useState<string[]>([])
  const [tipsLoading, setTipsLoading] = useState(false)
  const [tipsPolling, setTipsPolling] = useState(false)

  useEffect(() => {
    if (recipeId) {
      loadData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- loadData is stable, only re-run when recipeId changes
  }, [recipeId])

  // Poll for tips if recipe is recently imported and has no tips yet
  useEffect(() => {
    if (!recipe) return

    const recipeAge = Date.now() - new Date(recipe.scraped_at).getTime()
    const isRecent = recipeAge < 60000 // 60 seconds

    // Only poll for recent recipes with no tips
    if (!isRecent || tips.length > 0) {
      setTipsPolling(false)
      return
    }

    setTipsPolling(true)
    const startTime = Date.now()
    const POLL_INTERVAL = 3000 // 3 seconds
    const MAX_POLL_DURATION = 30000 // 30 seconds

    const interval = setInterval(async () => {
      // Stop if we've been polling too long
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

  // Auto-generate tips when viewing Tips tab for old recipes without tips
  useEffect(() => {
    if (
      activeTab === 'tips' &&
      tips.length === 0 &&
      aiStatus.available &&
      !tipsLoading &&
      !tipsPolling &&
      recipe
    ) {
      handleGenerateTips(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentionally only trigger on tab change, other deps checked inside
  }, [activeTab])

  const loadData = async () => {
    try {
      const recipeData = await api.recipes.get(recipeId)
      setRecipe(recipeData)
      setServings(recipeData.servings)
      setTips(recipeData.ai_tips || [])
      // Reset scaled data when loading a new recipe
      setScaledData(null)
    } catch (error) {
      console.error('Failed to load recipe:', error)
      toast.error('Failed to load recipe')
    } finally {
      setLoading(false)
    }
  }

  const canShowServingAdjustment =
    aiStatus.available && recipe?.servings !== null

  const handleServingChange = async (delta: number) => {
    if (!servings || !recipe || !profile) return
    const newServings = Math.max(1, servings + delta)
    setServings(newServings)

    // If returning to original servings, clear scaled data
    if (newServings === recipe.servings) {
      setScaledData(null)
      return
    }

    // Call AI to scale ingredients
    setScalingLoading(true)
    try {
      const result = await api.ai.scale(recipe.id, newServings, profile.id)
      setScaledData(result)
      if (result.notes.length > 0) {
        toast.info(result.notes[0])
      }
    } catch (error) {
      console.error('Failed to scale recipe:', error)
      toast.error('Failed to scale ingredients')
      // Revert to previous servings on error
      setServings(servings)
    } finally {
      setScalingLoading(false)
    }
  }

  const handleGenerateTips = async (regenerate: boolean = false) => {
    if (!recipe || tipsLoading) return

    setTipsLoading(true)
    try {
      const result = await api.ai.tips(recipe.id, regenerate)
      setTips(result.tips)
      // Update the recipe object too
      setRecipe({ ...recipe, ai_tips: result.tips })
      toast.success(regenerate ? 'Tips regenerated!' : 'Tips generated!')
    } catch (error) {
      console.error('Failed to generate tips:', error)
      toast.error('Failed to generate tips')
    } finally {
      setTipsLoading(false)
    }
  }

  const handleFavoriteToggle = async () => {
    if (!recipe) return
    await toggleFavorite(recipe)
  }

  const handleStartCooking = () => {
    navigate(`/recipe/${recipeId}/play`)
  }

  const handleAddToNewCollection = () => {
    navigate(`/collections?addRecipe=${recipeId}`)
  }

  const handleRemixCreated = async (newRecipeId: number) => {
    // Record history so the remix shows in "Recently Viewed"
    try {
      await api.history.record(newRecipeId)
    } catch (error) {
      console.error('Failed to record history:', error)
    }
    navigate(`/recipe/${newRecipeId}`)
  }

  const handleBack = () => {
    navigate(-1)
  }

  const recipeIsFavorite = recipe ? isFavorite(recipe.id) : false
  const imageUrl = recipe ? (recipe.image || recipe.image_url) : null

  return {
    recipe,
    loading,
    activeTab,
    setActiveTab,
    metaExpanded,
    setMetaExpanded,
    servings,
    showRemixModal,
    setShowRemixModal,
    scaledData,
    scalingLoading,
    tips,
    tipsLoading,
    tipsPolling,
    profile,
    aiStatus,
    recipeId,
    canShowServingAdjustment,
    recipeIsFavorite,
    imageUrl,
    handleServingChange,
    handleGenerateTips,
    handleFavoriteToggle,
    handleStartCooking,
    handleAddToNewCollection,
    handleRemixCreated,
    handleBack,
  }
}

export type { Tab }
