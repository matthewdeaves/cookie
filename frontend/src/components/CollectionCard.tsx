import { FolderPlus } from 'lucide-react'
import { cn } from '../lib/utils'
import type { Collection } from '../api/client'

interface CollectionCardProps {
  collection: Collection
  highlighted?: boolean
  onClick: () => void
}

export default function CollectionCard({
  collection,
  highlighted,
  onClick,
}: CollectionCardProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'group relative overflow-hidden rounded-lg bg-card text-left shadow-sm transition-all hover:shadow-md',
        highlighted && 'ring-2 ring-primary/20 hover:ring-primary/40'
      )}
    >
      {collection.cover_image ? (
        <div className="aspect-video w-full overflow-hidden bg-muted">
          <img
            src={collection.cover_image}
            alt={collection.name}
            className="h-full w-full object-cover"
          />
        </div>
      ) : (
        <div className="flex aspect-video w-full items-center justify-center bg-muted">
          <FolderPlus className="h-8 w-8 text-muted-foreground/50" />
        </div>
      )}
      <div className="p-3">
        <h3 className="mb-1 font-medium text-card-foreground line-clamp-1">
          {collection.name}
        </h3>
        <p className="text-sm text-muted-foreground">
          {collection.recipe_count} recipe
          {collection.recipe_count !== 1 ? 's' : ''}
        </p>
      </div>
    </button>
  )
}
