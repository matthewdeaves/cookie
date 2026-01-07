import { useState, useEffect, useRef } from 'react'
import { FolderPlus, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { api, type Collection } from '../api/client'
import { cn } from '../lib/utils'

interface AddToCollectionDropdownProps {
  recipeId: number
  onCreateNew: () => void
}

export default function AddToCollectionDropdown({
  recipeId,
  onCreateNew,
}: AddToCollectionDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [collections, setCollections] = useState<Collection[]>([])
  const [loading, setLoading] = useState(false)
  const [addingTo, setAddingTo] = useState<number | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  // Load collections when dropdown opens
  useEffect(() => {
    if (isOpen) {
      loadCollections()
    }
  }, [isOpen])

  const loadCollections = async () => {
    setLoading(true)
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

  const handleAddToCollection = async (collectionId: number) => {
    setAddingTo(collectionId)
    try {
      await api.collections.addRecipe(collectionId, recipeId)
      const collection = collections.find((c) => c.id === collectionId)
      toast.success(`Added to ${collection?.name || 'collection'}`)
      setIsOpen(false)
    } catch (error: unknown) {
      if (error instanceof Error && error.message.includes('already')) {
        toast.info('Recipe is already in this collection')
      } else {
        console.error('Failed to add to collection:', error)
        toast.error('Failed to add to collection')
      }
    } finally {
      setAddingTo(null)
    }
  }

  const handleCreateNew = () => {
    setIsOpen(false)
    onCreateNew()
  }

  return (
    <div ref={dropdownRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="rounded-full bg-black/40 p-2 text-white backdrop-blur-sm transition-colors hover:text-primary"
        title="Add to collection"
      >
        <FolderPlus className="h-5 w-5" />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full z-50 mt-2 w-56 rounded-lg border border-border bg-card shadow-lg">
          <div className="p-2">
            <h3 className="mb-2 px-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Add to Collection
            </h3>

            {loading ? (
              <div className="px-2 py-4 text-center text-sm text-muted-foreground">
                Loading...
              </div>
            ) : (
              <>
                {collections.length > 0 ? (
                  <div className="max-h-48 overflow-y-auto">
                    {collections.map((collection) => (
                      <button
                        key={collection.id}
                        onClick={() => handleAddToCollection(collection.id)}
                        disabled={addingTo === collection.id}
                        className={cn(
                          'flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm transition-colors',
                          'text-foreground hover:bg-muted disabled:opacity-50'
                        )}
                      >
                        <FolderPlus className="h-4 w-4 text-muted-foreground" />
                        <span className="flex-1 truncate">{collection.name}</span>
                        {addingTo === collection.id && (
                          <span className="text-xs text-muted-foreground">Adding...</span>
                        )}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="px-2 py-2 text-sm text-muted-foreground">
                    No collections yet
                  </div>
                )}

                <div className="mt-1 border-t border-border pt-1">
                  <button
                    onClick={handleCreateNew}
                    className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm text-primary transition-colors hover:bg-muted"
                  >
                    <Plus className="h-4 w-4" />
                    Create New Collection
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
