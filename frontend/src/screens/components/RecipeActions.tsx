import { Heart, PlayCircle, Sparkles } from 'lucide-react'
import { cn } from '../../lib/utils'
import AddToCollectionDropdown from '../../components/AddToCollectionDropdown'

interface RecipeActionsProps {
  recipeId: number
  recipeIsFavorite: boolean
  aiAvailable: boolean
  onFavoriteToggle: () => void
  onAddToNewCollection: () => void
  onShowRemixModal: () => void
  onStartCooking: () => void
}

export default function RecipeActions({
  recipeId,
  recipeIsFavorite,
  aiAvailable,
  onFavoriteToggle,
  onAddToNewCollection,
  onShowRemixModal,
  onStartCooking,
}: RecipeActionsProps) {
  return (
    <div className="absolute bottom-4 right-4 flex gap-2">
      <button
        onClick={onFavoriteToggle}
        className={cn(
          'rounded-full bg-black/40 p-2 backdrop-blur-sm transition-colors',
          recipeIsFavorite ? 'text-accent' : 'text-white hover:text-accent'
        )}
        title={recipeIsFavorite ? 'Remove from favorites' : 'Add to favorites'}
      >
        <Heart className={cn('h-5 w-5', recipeIsFavorite && 'fill-current')} />
      </button>
      <AddToCollectionDropdown
        recipeId={recipeId}
        onCreateNew={onAddToNewCollection}
      />
      {aiAvailable && (
        <button
          onClick={onShowRemixModal}
          className="rounded-full bg-black/40 p-2 text-white backdrop-blur-sm transition-colors hover:text-primary"
          title="Remix recipe"
        >
          <Sparkles className="h-5 w-5" />
        </button>
      )}
      <button
        onClick={onStartCooking}
        className="flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
      >
        <PlayCircle className="h-4 w-4" />
        Cook!
      </button>
    </div>
  )
}
