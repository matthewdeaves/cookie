import { type ReactNode, useState, useCallback } from 'react'
import {
  Star,
  Clock,
  ChevronDown,
  ChevronUp,
  Minus,
  Plus,
  GitCompareArrows,
  ExternalLink,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { type RecipeDetail, type ScaleResponse } from '../../api/client'
import { cn } from '../../lib/utils'
import { formatTime } from '../../lib/formatting'

interface RecipeHeaderProps {
  recipe: RecipeDetail
  imageUrl: string | null | undefined
  metaExpanded: boolean
  setMetaExpanded: (expanded: boolean) => void
  canShowServingAdjustment: boolean
  servings: number | null
  scaledData: ScaleResponse | null
  scalingLoading: boolean
  onServingChange: (delta: number) => void
  children?: ReactNode
}

export default function RecipeHeader({
  recipe,
  imageUrl,
  metaExpanded,
  setMetaExpanded,
  canShowServingAdjustment,
  servings,
  scaledData,
  scalingLoading,
  onServingChange,
  children,
}: RecipeHeaderProps) {
  const navigate = useNavigate()
  const [imgError, setImgError] = useState(false)

  const handleImgError = useCallback(() => {
    setImgError(true)
  }, [])

  return (
    <>
      {/* Hero Image */}
      <div className="relative h-64 sm:h-80">
        {imageUrl && !imgError ? (
          <img
            src={imageUrl}
            alt={recipe.title}
            loading="lazy"
            onError={handleImgError}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-muted to-muted/60">
            <span className="px-4 text-center text-lg font-medium text-muted-foreground">
              {recipe.title}
            </span>
          </div>
        )}

        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />

        {/* Title, meta, and actions overlay */}
        <div className="absolute inset-x-0 bottom-0 flex flex-col gap-2 px-4 pb-4">
          <div>
            <h1 className="text-xl font-medium text-white drop-shadow-lg sm:text-2xl">
              {recipe.title}
            </h1>
            <div className="mt-1 flex items-center gap-3 text-sm text-white/90">
              {recipe.rating && (
                <span className="flex items-center gap-1">
                  <Star className="h-4 w-4 fill-star text-star" />
                  {recipe.rating.toFixed(1)}
                  {recipe.rating_count && (
                    <span className="text-white/70">
                      ({recipe.rating_count})
                    </span>
                  )}
                </span>
              )}
              {recipe.canonical_url ? (
              <a
                href={recipe.canonical_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 underline decoration-white/40 underline-offset-2"
              >
                {recipe.host}
                <ExternalLink className="h-3 w-3" />
              </a>
            ) : (
              <span>{recipe.host}</span>
            )}
            </div>
          </div>

          {/* Action buttons row */}
          {children}
        </div>
      </div>

      {/* Meta info (collapsible) */}
      <div className="border-b border-border">
        <button
          onClick={() => setMetaExpanded(!metaExpanded)}
          className="flex w-full items-center justify-between px-4 py-3 text-left"
        >
          <span className="text-sm font-medium text-foreground">
            Recipe Details
          </span>
          {metaExpanded ? (
            <ChevronUp className="h-5 w-5 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-5 w-5 text-muted-foreground" />
          )}
        </button>

        {metaExpanded && (
          <div className="flex flex-wrap gap-4 px-4 pb-4">
            <TimeDisplay
              label="Prep"
              time={recipe.prep_time}
              adjustedTime={scaledData?.prep_time_adjusted}
            />
            <TimeDisplay
              label="Cook"
              time={recipe.cook_time}
              adjustedTime={scaledData?.cook_time_adjusted}
            />
            <TimeDisplay
              label="Total"
              time={recipe.total_time}
              adjustedTime={scaledData?.total_time_adjusted}
            />

            {/* Servings adjuster - only show if AI available and servings present */}
            {canShowServingAdjustment && servings && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground">Servings:</span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => onServingChange(-1)}
                    disabled={servings <= 1 || scalingLoading}
                    className="rounded-md bg-muted p-1 text-foreground transition-colors hover:bg-muted/80 disabled:opacity-50"
                  >
                    <Minus className="h-4 w-4" />
                  </button>
                  <span className="w-8 text-center font-medium text-foreground">
                    {scalingLoading ? '...' : servings}
                  </span>
                  <button
                    onClick={() => onServingChange(1)}
                    disabled={scalingLoading}
                    className="rounded-md bg-muted p-1 text-foreground transition-colors hover:bg-muted/80 disabled:opacity-50"
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>
                {scaledData && servings !== recipe?.servings && (
                  <span className="text-xs text-muted-foreground">
                    (scaled from {recipe?.servings})
                  </span>
                )}
              </div>
            )}

            {/* Show static servings if AI not available */}
            {!canShowServingAdjustment && recipe.servings && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground">Servings:</span>
                <span className="text-foreground">{recipe.servings}</span>
              </div>
            )}

            {/* Yields (if different from servings) */}
            {recipe.yields && !recipe.servings && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground">Yields:</span>
                <span className="text-foreground">{recipe.yields}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Linked Recipes Navigation */}
      {recipe.linked_recipes && recipe.linked_recipes.length > 0 && (
        <div className="border-b border-border px-4 py-3">
          <div className="flex items-center gap-2 text-sm">
            <GitCompareArrows className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Linked recipes:</span>
            <div className="flex flex-wrap gap-2">
              {recipe.linked_recipes.map((linked) => (
                <button
                  key={linked.id}
                  onClick={() => navigate(`/recipe/${linked.id}`)}
                  className="inline-flex items-center gap-1 rounded-full bg-muted px-3 py-1 text-xs font-medium text-foreground transition-colors hover:bg-muted/80"
                >
                  <span
                    className={cn(
                      'h-1.5 w-1.5 rounded-full',
                      linked.relationship === 'original'
                        ? 'bg-primary'
                        : linked.relationship === 'remix'
                          ? 'bg-accent'
                          : 'bg-muted-foreground'
                    )}
                  />
                  {linked.title}
                  <span className="text-muted-foreground">
                    ({linked.relationship})
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

function TimeDisplay({
  label,
  time,
  adjustedTime,
}: {
  label: string
  time: number | null
  adjustedTime: number | null | undefined
}) {
  if (!time) return null

  return (
    <div className="flex items-center gap-2 text-sm">
      <Clock className="h-4 w-4 text-muted-foreground" />
      <span className="text-muted-foreground">{label}:</span>
      <span className="text-foreground">
        {adjustedTime && adjustedTime !== time ? (
          <>
            {formatTime(adjustedTime)}
            <span className="ml-1 text-muted-foreground">
              (was {formatTime(time)})
            </span>
          </>
        ) : (
          formatTime(adjustedTime ?? time)
        )}
      </span>
    </div>
  )
}
