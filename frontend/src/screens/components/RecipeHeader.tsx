import { type ReactNode, useState, useCallback } from 'react'
import { Star, ExternalLink } from 'lucide-react'
import { type RecipeDetail, type ScaleResponse } from '../../api/client'
import MetaSection from './MetaSection'
import LinkedRecipesNav from './LinkedRecipesNav'

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
      <MetaSection
        recipe={recipe}
        metaExpanded={metaExpanded}
        setMetaExpanded={setMetaExpanded}
        canShowServingAdjustment={canShowServingAdjustment}
        servings={servings}
        scaledData={scaledData}
        scalingLoading={scalingLoading}
        onServingChange={onServingChange}
      />

      {/* Linked Recipes Navigation */}
      {recipe.linked_recipes && recipe.linked_recipes.length > 0 && (
        <LinkedRecipesNav linkedRecipes={recipe.linked_recipes} />
      )}
    </>
  )
}
