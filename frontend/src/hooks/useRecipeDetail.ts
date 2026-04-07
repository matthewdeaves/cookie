import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'
import { api, type RecipeDetail as RecipeDetailType } from '../api/client'
import { useProfile } from '../contexts/ProfileContext'
import { useAIStatus } from '../contexts/AIStatusContext'
import { useTipsPolling } from './useTipsPolling'
import { useServingScale } from './useServingScale'

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
  const [showRemixModal, setShowRemixModal] = useState(false)

  const { servings, scaledData, scalingLoading, setServings, setScaledData, handleServingChange } =
    useServingScale(recipe, profile?.id)

  const { tips, tipsLoading, tipsPolling, handleGenerateTips } = useTipsPolling({
    recipe,
    aiAvailable: aiStatus.available,
    activeTab,
    setRecipe,
  })

  useEffect(() => {
    if (!recipeId) return
    let cancelled = false
    ;(async () => {
      try {
        const recipeData = await api.recipes.get(recipeId)
        if (!cancelled) {
          setRecipe(recipeData)
          setServings(recipeData.servings)
          setScaledData(null)
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load recipe:', error)
          toast.error('Failed to load recipe')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only re-run when recipeId changes
  }, [recipeId])

  const canShowServingAdjustment = aiStatus.available && recipe?.servings !== null

  const handleFavoriteToggle = async () => {
    if (!recipe) return
    await toggleFavorite(recipe)
  }

  const handleRemixCreated = async (newRecipeId: number) => {
    try { await api.history.record(newRecipeId) } catch (error) {
      console.error('Failed to record history:', error)
    }
    navigate(`/recipe/${newRecipeId}`)
  }

  const recipeIsFavorite = recipe ? isFavorite(recipe.id) : false
  const imageUrl = recipe ? (recipe.image || recipe.image_url) : null

  return {
    recipe, loading, activeTab, setActiveTab, metaExpanded, setMetaExpanded,
    servings, showRemixModal, setShowRemixModal, scaledData, scalingLoading,
    tips, tipsLoading, tipsPolling, profile, aiStatus, recipeId,
    canShowServingAdjustment, recipeIsFavorite, imageUrl,
    handleServingChange, handleGenerateTips, handleFavoriteToggle,
    handleStartCooking: () => navigate(`/recipe/${recipeId}/play`),
    handleAddToNewCollection: () => navigate(`/collections?addRecipe=${recipeId}`),
    handleRemixCreated,
    handleBack: () => navigate(-1),
  }
}

export type { Tab }
