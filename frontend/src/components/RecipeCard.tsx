import { useState, useCallback, useEffect } from 'react'
import { Star, Clock, Heart, Trash2 } from 'lucide-react'
import type { Recipe } from '../api/client'
import { cn } from '../lib/utils'
import { formatTime } from '../lib/formatting'

interface RecipeCardProps {
  recipe: Recipe
  isFavorite?: boolean
  onFavoriteToggle?: (recipe: Recipe) => void
  onDelete?: (recipe: Recipe) => void
  onClick?: (recipe: Recipe) => void
}

function RecipeImage({ recipe, imgError, onError }: {
  recipe: Recipe
  imgError: boolean
  onError: () => void
}) {
  const imageUrl = recipe.image || recipe.image_url

  if (imageUrl && !imgError) {
    return (
      <img
        src={imageUrl}
        alt={recipe.title}
        loading="lazy"
        onError={onError}
        className="h-full w-full object-cover transition-transform group-hover:scale-105"
      />
    )
  }

  return (
    <div className="flex h-full w-full items-center justify-center bg-muted px-3 text-center text-sm font-medium text-muted-foreground">
      {recipe.title}
    </div>
  )
}

function FavoriteButton({ isFavorite, onClick }: {
  isFavorite: boolean
  onClick: (e: React.MouseEvent) => void
}) {
  return (
    <button
      onClick={onClick}
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
  )
}

function DeleteButton({ onDelete }: { onDelete: () => void }) {
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    if (!confirming) return
    const t = setTimeout(() => setConfirming(false), 2500)
    return () => clearTimeout(t)
  }, [confirming])

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirming) {
      onDelete()
    } else {
      setConfirming(true)
    }
  }

  return (
    <button
      onClick={handleClick}
      className={cn(
        'absolute left-2 top-2 rounded-full p-2 transition-colors backdrop-blur-sm',
        confirming
          ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
          : 'bg-background/80 text-muted-foreground hover:bg-background hover:text-destructive'
      )}
      aria-label={confirming ? 'Confirm delete' : 'Delete recipe'}
      title={confirming ? 'Click again to confirm' : 'Delete recipe'}
    >
      <Trash2 className="h-4 w-4" />
    </button>
  )
}

function RecipeMeta({ recipe }: { recipe: Recipe }) {
  return (
    <div className="flex items-center gap-3 text-xs text-muted-foreground">
      <span className="truncate">{recipe.host}</span>
      {recipe.total_time && (
        <span className="flex shrink-0 items-center gap-1">
          <Clock className="h-3 w-3" />
          {formatTime(recipe.total_time)}
        </span>
      )}
      {recipe.rating && (
        <span className="flex shrink-0 items-center gap-1">
          <Star className="h-3 w-3 fill-star text-star" />
          {recipe.rating.toFixed(1)}
        </span>
      )}
    </div>
  )
}

export default function RecipeCard({
  recipe,
  isFavorite = false,
  onFavoriteToggle,
  onDelete,
  onClick,
}: RecipeCardProps) {
  const [imgError, setImgError] = useState(false)

  const handleImgError = useCallback(() => {
    setImgError(true)
  }, [])

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
        <RecipeImage recipe={recipe} imgError={imgError} onError={handleImgError} />

        {onDelete && (
          <DeleteButton onDelete={() => onDelete(recipe)} />
        )}

        {onFavoriteToggle && (
          <FavoriteButton isFavorite={isFavorite} onClick={handleFavoriteClick} />
        )}

        {recipe.is_remix && (
          <div className={cn(
            'absolute top-2 rounded-full bg-primary/90 px-2 py-0.5 text-xs text-primary-foreground backdrop-blur-sm',
            onDelete ? 'left-10' : 'left-2'
          )}>
            Remix
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-3">
        <h3 className="mb-1 line-clamp-2 text-sm font-medium text-card-foreground">
          {recipe.title}
        </h3>
        <RecipeMeta recipe={recipe} />
      </div>
    </div>
  )
}
