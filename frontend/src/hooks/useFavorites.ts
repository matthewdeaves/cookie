import { useState, useEffect, useCallback } from 'react'
import { toast } from 'sonner'
import { api, type Profile, type RecipeDetail } from '../api/client'

interface UseFavoritesReturn {
  favoriteRecipeIds: Set<number>
  toggleFavorite: (recipe: RecipeDetail) => Promise<void>
  isFavorite: (recipeId: number) => boolean
  clearFavorites: () => void
}

/**
 * Manages favorite recipe state: loading, toggling, and checking favorites.
 */
export function useFavorites(profile: Profile | null): UseFavoritesReturn {
  const [favoriteRecipeIds, setFavoriteRecipeIds] = useState<Set<number>>(new Set())

  useEffect(() => {
    if (!profile) {
      Promise.resolve().then(() => setFavoriteRecipeIds(new Set()))
      return
    }

    api.favorites
      .list()
      .then((favorites) => setFavoriteRecipeIds(new Set(favorites.map((f) => f.recipe.id))))
      .catch((error) => console.error('Failed to load favorites:', error))
  }, [profile])

  const toggleFavorite = useCallback(async (recipe: RecipeDetail) => {
    const isFav = favoriteRecipeIds.has(recipe.id)
    try {
      if (isFav) {
        await api.favorites.remove(recipe.id)
        setFavoriteRecipeIds((prev) => {
          const next = new Set(prev)
          next.delete(recipe.id)
          return next
        })
        toast.success('Removed from favorites')
      } else {
        await api.favorites.add(recipe.id)
        setFavoriteRecipeIds((prev) => new Set(prev).add(recipe.id))
        toast.success('Added to favorites')
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error)
      toast.error('Failed to update favorites')
    }
  }, [favoriteRecipeIds])

  const isFavorite = useCallback((recipeId: number) => {
    return favoriteRecipeIds.has(recipeId)
  }, [favoriteRecipeIds])

  const clearFavorites = useCallback(() => {
    setFavoriteRecipeIds(new Set())
  }, [])

  return { favoriteRecipeIds, toggleFavorite, isFavorite, clearFavorites }
}
