import { useState, useEffect } from 'react'
import { ArrowLeft, FolderPlus, Plus, X } from 'lucide-react'
import { toast } from 'sonner'
import { api, type Collection } from '../api/client'
import { cn } from '../lib/utils'

interface CollectionsProps {
  onBack: () => void
  onCollectionClick: (collectionId: number) => void
  pendingRecipeId?: number | null
}

export default function Collections({
  onBack,
  onCollectionClick,
  pendingRecipeId,
}: CollectionsProps) {
  const [collections, setCollections] = useState<Collection[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newCollectionName, setNewCollectionName] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    loadCollections()
  }, [])

  const loadCollections = async () => {
    try {
      const data = await api.collections.list()
      setCollections(data)
    } catch (error) {
      console.error('Failed to load collections:', error)
      toast.error('Failed to load collections')
    } finally {
      setLoading(false)
    }
  }

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

      // If there's a pending recipe to add, add it and navigate to collection
      if (pendingRecipeId) {
        try {
          await api.collections.addRecipe(collection.id, pendingRecipeId)
          toast.success('Recipe added to collection')
        } catch (error) {
          console.error('Failed to add recipe to collection:', error)
        }
        onCollectionClick(collection.id)
      }
    } catch (error) {
      console.error('Failed to create collection:', error)
      toast.error('Failed to create collection')
    } finally {
      setCreating(false)
    }
  }

  const handleCollectionClick = async (collectionId: number) => {
    // If there's a pending recipe, add it first
    if (pendingRecipeId) {
      try {
        await api.collections.addRecipe(collectionId, pendingRecipeId)
        toast.success('Recipe added to collection')
      } catch (error: unknown) {
        // Ignore "already in collection" error
        if (error instanceof Error && !error.message.includes('already')) {
          console.error('Failed to add recipe to collection:', error)
          toast.error('Failed to add recipe to collection')
        } else {
          toast.info('Recipe is already in this collection')
        }
      }
    }
    onCollectionClick(collectionId)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-xl font-medium text-foreground">Collections</h1>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          New Collection
        </button>
      </header>

      {/* Content */}
      <main className="px-4 py-6">
        <div className="mx-auto max-w-4xl">
          {/* Create form */}
          {showCreateForm && (
            <form
              onSubmit={handleCreateCollection}
              className="mb-6 rounded-lg border border-border bg-card p-4"
            >
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-medium text-foreground">New Collection</h2>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false)
                    setNewCollectionName('')
                  }}
                  className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <input
                type="text"
                value={newCollectionName}
                onChange={(e) => setNewCollectionName(e.target.value)}
                placeholder="Collection name"
                className="mb-3 w-full rounded-lg border border-border bg-input-background px-3 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                autoFocus
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false)
                    setNewCollectionName('')
                  }}
                  className="rounded-lg px-4 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newCollectionName.trim() || creating}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          )}

          {/* Pending recipe notice */}
          {pendingRecipeId && (
            <div className="mb-4 rounded-lg border border-primary/30 bg-primary/10 p-3 text-sm text-foreground">
              Select a collection or create a new one to add the recipe
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <span className="text-muted-foreground">Loading...</span>
            </div>
          ) : collections.length > 0 ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
              {collections.map((collection) => (
                <button
                  key={collection.id}
                  onClick={() => handleCollectionClick(collection.id)}
                  className={cn(
                    'group relative overflow-hidden rounded-lg bg-card p-4 text-left shadow-sm transition-all hover:shadow-md',
                    pendingRecipeId && 'ring-2 ring-primary/20 hover:ring-primary/40'
                  )}
                >
                  <div className="mb-8 rounded-lg bg-muted p-3">
                    <FolderPlus className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="mb-1 font-medium text-card-foreground line-clamp-1">
                    {collection.name}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {collection.recipe_count} recipe
                    {collection.recipe_count !== 1 ? 's' : ''}
                  </p>
                </button>
              ))}
            </div>
          ) : (
            /* Empty state */
            <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border py-12">
              <div className="mb-4 rounded-full bg-muted p-4">
                <FolderPlus className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-foreground">
                No collections yet
              </h3>
              <p className="mb-4 text-center text-muted-foreground">
                Create one to organize your recipes!
              </p>
              <button
                onClick={() => setShowCreateForm(true)}
                className="rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
              >
                Create Collection
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
