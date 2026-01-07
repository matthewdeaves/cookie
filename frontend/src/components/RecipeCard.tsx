import { Star, Clock, Heart } from 'lucide-react'
import type { Recipe } from '../api/client'
import { cn } from '../lib/utils'

interface RecipeCardProps {
  recipe: Recipe
  isFavorite?: boolean
  onFavoriteToggle?: (recipe: Recipe) => void
  onClick?: (recipe: Recipe) => void
}

export default function RecipeCard({
  recipe,
  isFavorite = false,
  onFavoriteToggle,
  onClick,
}: RecipeCardProps) {
  const imageUrl = recipe.image || recipe.image_url

  const formatTime = (minutes: number | null) => {
    if (!minutes) return null
    if (minutes < 60) return `${minutes} min`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    onFavoriteToggle?.(recipe)
  }

  return (
    <div
      className={cn(
        'group relative overflow-hidden rounded-lg bg-card shadow-sm transition-all hover:shadow-md',
        onClick && 'cursor-pointer'
      )}
      onClick={() => onClick?.(recipe)}
    >
      {/* Image */}
      <div className="relative aspect-[4/3] overflow-hidden bg-muted">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={recipe.title}
            className="h-full w-full object-cover transition-transform group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground">
            No image
          </div>
        )}

        {/* Favorite button */}
        {onFavoriteToggle && (
          <button
            onClick={handleFavoriteClick}
            className={cn(
              'absolute right-2 top-2 rounded-full bg-background/80 p-2 backdrop-blur-sm transition-colors',
              isFavorite
                ? 'text-accent hover:bg-background'
                : 'text-muted-foreground hover:bg-background hover:text-accent'
            )}
            aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
          >
            <Heart
              className={cn('h-5 w-5', isFavorite && 'fill-current')}
            />
          </button>
        )}

        {/* Remix badge */}
        {recipe.is_remix && (
          <div className="absolute left-2 top-2 rounded-full bg-primary/90 px-2 py-0.5 text-xs text-primary-foreground backdrop-blur-sm">
            Remix
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-3">
        {/* Title */}
        <h3 className="mb-1 line-clamp-2 text-sm font-medium text-card-foreground">
          {recipe.title}
        </h3>

        {/* Meta */}
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {/* Source */}
          <span className="truncate">{recipe.host}</span>

          {/* Time */}
          {recipe.total_time && (
            <span className="flex shrink-0 items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatTime(recipe.total_time)}
            </span>
          )}

          {/* Rating */}
          {recipe.rating && (
            <span className="flex shrink-0 items-center gap-1">
              <Star className="h-3 w-3 fill-star text-star" />
              {recipe.rating.toFixed(1)}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
