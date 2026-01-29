import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Trash2, X, FolderOpen } from 'lucide-react'
import { toast } from 'sonner'
import { api, type CollectionDetail as CollectionDetailType, type Recipe } from '../api/client'
import RecipeCard from '../components/RecipeCard'
import { LoadingSpinner } from '../components/Skeletons'

export default function CollectionDetail() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const collectionId = Number(id)

  const [collection, setCollection] = useState<CollectionDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (collectionId) {
      loadCollection()
    }
  }, [collectionId])

  const loadCollection = async () => {
    try {
      const data = await api.collections.get(collectionId)
      setCollection(data)
    } catch (error) {
      console.error('Failed to load collection:', error)
      toast.error('Failed to load collection')
    } finally {
      setLoading(false)
    }
  }

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
      toast.error('Failed to remove recipe')
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
      toast.error('Failed to delete collection')
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

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <LoadingSpinner className="min-h-screen" />
      </div>
    )
  }

  if (!collection) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background">
        <span className="mb-4 text-muted-foreground">Collection not found</span>
        <button
          onClick={() => navigate('/collections')}
          className="rounded-lg bg-primary px-4 py-2 text-primary-foreground"
        >
          Go Back
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/collections')}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-xl font-medium text-foreground">
              {collection.name}
            </h1>
            <p className="text-sm text-muted-foreground">
              {collection.recipes.length} recipe
              {collection.recipes.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowDeleteConfirm(true)}
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
          title="Delete collection"
        >
          <Trash2 className="h-5 w-5" />
        </button>
      </header>

      {/* Delete confirmation */}
      {showDeleteConfirm && (
        <div className="border-b border-destructive/30 bg-destructive/10 px-4 py-3">
          <div className="mx-auto flex max-w-4xl items-center justify-between">
            <p className="text-sm text-foreground">
              Delete "{collection.name}"? This cannot be undone.
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteCollection}
                disabled={deleting}
                className="rounded-lg bg-destructive px-3 py-1.5 text-sm font-medium text-destructive-foreground transition-colors hover:bg-destructive/90 disabled:opacity-50"
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      <main className="px-4 py-6">
        <div className="mx-auto max-w-4xl">
          {collection.recipes.length > 0 ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
              {collection.recipes.map((item) => (
                <div key={item.recipe.id} className="group relative">
                  <RecipeCard
                    recipe={item.recipe}
                    onClick={() => handleRecipeClick(item.recipe.id)}
                  />
                  {/* Remove button overlay */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRemoveRecipe(item.recipe)
                    }}
                    className="absolute right-2 top-2 rounded-full bg-destructive/90 p-1.5 text-destructive-foreground opacity-0 transition-opacity group-hover:opacity-100"
                    title="Remove from collection"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            /* Empty state */
            <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border py-12">
              <div className="mb-4 rounded-full bg-muted p-4">
                <FolderOpen className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-foreground">
                This collection is empty
              </h3>
              <p className="text-center text-muted-foreground">
                Add recipes from their detail pages.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
