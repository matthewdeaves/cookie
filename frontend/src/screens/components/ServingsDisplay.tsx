import { Minus, Plus } from 'lucide-react'
import { type RecipeDetail, type ScaleResponse } from '../../api/client'

interface ServingsDisplayProps {
  recipe: RecipeDetail
  canShowServingAdjustment: boolean
  servings: number | null
  scaledData: ScaleResponse | null
  scalingLoading: boolean
  onServingChange: (delta: number) => void
}

function AdjustableServings({
  recipe,
  servings,
  scaledData,
  scalingLoading,
  onServingChange,
}: Omit<ServingsDisplayProps, 'canShowServingAdjustment'>) {
  if (!servings) return null

  return (
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
  )
}

function StaticServings({ servings }: { servings: number }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-muted-foreground">Servings:</span>
      <span className="text-foreground">{servings}</span>
    </div>
  )
}

export default function ServingsDisplay({
  recipe,
  canShowServingAdjustment,
  servings,
  scaledData,
  scalingLoading,
  onServingChange,
}: ServingsDisplayProps) {
  if (canShowServingAdjustment && servings) {
    return (
      <AdjustableServings
        recipe={recipe}
        servings={servings}
        scaledData={scaledData}
        scalingLoading={scalingLoading}
        onServingChange={onServingChange}
      />
    )
  }

  if (!canShowServingAdjustment && recipe.servings) {
    return <StaticServings servings={recipe.servings} />
  }

  return null
}
