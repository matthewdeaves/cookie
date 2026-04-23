import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { api, type CollectionDetail, type Recipe } from '../api/client'

export function useCollectionData(collectionId: number) {
  const navigate = useNavigate()
  const [collection, setCollection] = useState<CollectionDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!collectionId) return
    let cancelled = false
    ;(async () => {
      try {
        const data = await api.collections.get(collectionId)
        if (!cancelled) setCollection(data)
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load collection:', error)
          const msg = error instanceof Error ? error.message : null
          toast.error(msg || 'Failed to load collection')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [collectionId])

  const handleRemoveRecipe = async (recipe: Recipe) => {
    if (!collection) return
    try {
      await api.collections.removeRecipe(collectionId, recipe.id)
      setCollection({
        ...collection,
        recipes: collection.recipes.filter((item) => item.recipe.id !== recipe.id),
      })
      toast.success('Removed from collection')
    } catch (error) {
      console.error('Failed to remove recipe:', error)
      const msg = error instanceof Error ? error.message : null
      toast.error(msg || 'Failed to remove recipe')
    }
  }

  const handleDeleteCollection = async () => {
    setDeleting(true)
    try {
      await api.collections.delete(collectionId)
      toast.success('Collection deleted')
      navigate('/collections')
    } catch (error) {
      console.error('Failed to delete collection:', error)
      const msg = error instanceof Error ? error.message : null
      toast.error(msg || 'Failed to delete collection')
    } finally {
      setDeleting(false)
    }
  }

  const handleRecipeClick = async (recipeId: number) => {
    try {
      await api.history.record(recipeId)
    } catch (error) {
      console.error('Failed to record history:', error)
    }
    navigate(`/recipe/${recipeId}`)
  }

  return {
    collection,
    loading,
    showDeleteConfirm,
    setShowDeleteConfirm,
    deleting,
    handleRemoveRecipe,
    handleDeleteCollection,
    handleRecipeClick,
  }
}
