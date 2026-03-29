import { useState, useEffect, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { api, type Recipe, type Favorite, type HistoryItem } from '../api/client'

export function useHomeData() {
  const navigate = useNavigate()
  const [favorites, setFavorites] = useState<Favorite[]>([])
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [recipesCount, setRecipesCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [favoritesData, historyData, recipesData] = await Promise.all([
        api.favorites.list(),
        api.history.list(6),
        api.recipes.list(1000),
      ])
      setFavorites(favoritesData)
      setHistory(historyData)
      setRecipesCount(recipesData.length)
    } catch (error) {
      console.error('Failed to load data:', error)
      toast.error('Failed to load recipes')
    } finally {
      setLoading(false)
    }
  }

  const favoriteIds = useMemo(
    () => new Set(favorites.map((f) => f.recipe.id)),
    [favorites]
  )

  const handleRecipeClick = useCallback(async (recipeId: number) => {
    try {
      await api.history.record(recipeId)
    } catch (error) {
      console.error('Failed to record history:', error)
    }
    navigate(`/recipe/${recipeId}`)
  }, [navigate])

  const handleToggleFavorite = useCallback(async (recipe: Recipe) => {
    const isFav = favoriteIds.has(recipe.id)
    try {
      if (isFav) {
        await api.favorites.remove(recipe.id)
        setFavorites((prev) => prev.filter((f) => f.recipe.id !== recipe.id))
        toast.success('Removed from favorites')
      } else {
        const newFav = await api.favorites.add(recipe.id)
        setFavorites((prev) => [...prev, newFav])
        toast.success('Added to favorites')
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error)
      toast.error(isFav ? 'Failed to remove from favorites' : 'Failed to add to favorites')
    }
  }, [favoriteIds])

  return {
    favorites,
    history,
    recipesCount,
    loading,
    favoriteIds,
    handleRecipeClick,
    handleToggleFavorite,
  }
}
