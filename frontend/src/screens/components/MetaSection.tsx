import { ChevronDown, ChevronUp, Clock } from 'lucide-react'
import { type RecipeDetail, type ScaleResponse } from '../../api/client'
import { formatTime } from '../../lib/formatting'
import ServingsDisplay from './ServingsDisplay'

interface MetaSectionProps {
  recipe: RecipeDetail
  metaExpanded: boolean
  setMetaExpanded: (expanded: boolean) => void
  canShowServingAdjustment: boolean
  servings: number | null
  scaledData: ScaleResponse | null
  scalingLoading: boolean
  onServingChange: (delta: number) => void
}

export default function MetaSection({
  recipe,
  metaExpanded,
  setMetaExpanded,
  canShowServingAdjustment,
  servings,
  scaledData,
  scalingLoading,
  onServingChange,
}: MetaSectionProps) {
  return (
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

          <ServingsDisplay
            recipe={recipe}
            canShowServingAdjustment={canShowServingAdjustment}
            servings={servings}
            scaledData={scaledData}
            scalingLoading={scalingLoading}
            onServingChange={onServingChange}
          />

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
