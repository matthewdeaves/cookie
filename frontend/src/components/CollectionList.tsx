import { FolderPlus, Plus } from 'lucide-react'
import type { Collection } from '../api/client'
import { cn } from '../lib/utils'

interface CollectionListProps {
  collections: Collection[]
  loading: boolean
  addingTo: number | null
  onAdd: (collectionId: number) => void
  onCreateNew: () => void
}

export default function CollectionList({
  collections,
  loading,
  addingTo,
  onAdd,
  onCreateNew,
}: CollectionListProps) {
  if (loading) {
    return (
      <div className="px-2 py-4 text-center text-sm text-muted-foreground">
        Loading...
      </div>
    )
  }

  return (
    <>
      {collections.length > 0 ? (
        <div className="max-h-48 overflow-y-auto">
          {collections.map((collection) => (
            <button
              key={collection.id}
              onClick={() => onAdd(collection.id)}
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
          onClick={onCreateNew}
          className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm text-primary transition-colors hover:bg-muted"
        >
          <Plus className="h-4 w-4" />
          Create New Collection
        </button>
      </div>
    </>
  )
}
