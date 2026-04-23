import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { api, type Collection } from '../api/client'

export function useCollectionsPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const pendingRecipeId = searchParams.get('addRecipe')
    ? Number(searchParams.get('addRecipe'))
    : null

  const [collections, setCollections] = useState<Collection[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newCollectionName, setNewCollectionName] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await api.collections.list()
        if (!cancelled) setCollections(data)
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load collections:', error)
          toast.error('Failed to load collections')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [])

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newCollectionName.trim()) return

    setCreating(true)
    try {
      const collection = await api.collections.create({
        name: newCollectionName.trim(),
      })
      setCollections([collection, ...collections])
      setNewCollectionName('')
      setShowCreateForm(false)
      toast.success('Collection created')

      if (pendingRecipeId) {
        try {
          await api.collections.addRecipe(collection.id, pendingRecipeId)
          toast.success('Recipe added to collection')
        } catch (error) {
          console.error('Failed to add recipe to collection:', error)
        }
        navigate(`/collection/${collection.id}`)
      }
    } catch (error) {
      console.error('Failed to create collection:', error)
      const msg = error instanceof Error ? error.message : null
      toast.error(msg || 'Failed to create collection')
    } finally {
      setCreating(false)
    }
  }

  const handleCollectionClick = async (collectionId: number) => {
    if (pendingRecipeId) {
      try {
        await api.collections.addRecipe(collectionId, pendingRecipeId)
        toast.success('Recipe added to collection')
      } catch (error: unknown) {
        const msg = error instanceof Error ? error.message : null
        toast.error(msg || 'Failed to add recipe to collection')
      }
    }
    navigate(`/collection/${collectionId}`)
  }

  const handleCancelCreate = () => {
    setShowCreateForm(false)
    setNewCollectionName('')
  }

  return {
    pendingRecipeId,
    collections,
    loading,
    showCreateForm,
    setShowCreateForm,
    newCollectionName,
    setNewCollectionName,
    creating,
    handleCreateCollection,
    handleCollectionClick,
    handleCancelCreate,
  }
}
