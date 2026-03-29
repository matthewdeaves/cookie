import { Sparkles } from 'lucide-react'
import { type RecipeDetail, type ScaleResponse } from '../../api/client'
import { cn, formatNutritionKey } from '../../lib/utils'
import type { Tab } from '../../hooks/useRecipeDetail'
import RecipeIngredients from './RecipeIngredients'
import RecipeInstructions from './RecipeInstructions'

interface RecipeTabsProps {
  recipe: RecipeDetail
  activeTab: Tab
  setActiveTab: (tab: Tab) => void
  scaledData: ScaleResponse | null
  tips: string[]
  tipsLoading: boolean
  tipsPolling: boolean
  aiAvailable: boolean
  onGenerateTips: (regenerate: boolean) => void
}

export default function RecipeTabs({
  recipe,
  activeTab,
  setActiveTab,
  scaledData,
  tips,
  tipsLoading,
  tipsPolling,
  aiAvailable,
  onGenerateTips,
}: RecipeTabsProps) {
  const tabItems: { key: Tab; label: string }[] = [
    { key: 'ingredients', label: 'Ingredients' },
    { key: 'instructions', label: 'Instructions' },
    { key: 'nutrition', label: 'Nutrition' },
    ...(aiAvailable ? [{ key: 'tips' as const, label: 'Tips' }] : []),
  ]

  return (
    <>
      {/* Tab bar */}
      <div className="border-b border-border">
        <div className="flex px-4">
          {tabItems.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={cn(
                'border-b-2 px-4 py-3 text-sm font-medium transition-colors',
                activeTab === key
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="px-4 py-6">
        {activeTab === 'ingredients' && (
          <RecipeIngredients recipe={recipe} scaledData={scaledData} />
        )}
        {activeTab === 'instructions' && (
          <RecipeInstructions recipe={recipe} scaledData={scaledData} />
        )}
        {activeTab === 'nutrition' && (
          <NutritionTab recipe={recipe} />
        )}
        {activeTab === 'tips' && (
          <TipsTab
            tips={tips}
            scalingNotes={scaledData?.notes || []}
            aiAvailable={aiAvailable}
            loading={tipsLoading}
            polling={tipsPolling}
            onGenerateTips={onGenerateTips}
          />
        )}
      </div>
    </>
  )
}

function NutritionTab({ recipe }: { recipe: RecipeDetail }) {
  const nutritionEntries = Object.entries(recipe.nutrition || {})

  if (nutritionEntries.length === 0) {
    return (
      <p className="text-muted-foreground">
        No nutrition information available for this recipe.
      </p>
    )
  }

  return (
    <div>
      {recipe.servings && (
        <p className="mb-4 text-sm text-muted-foreground">
          Per serving (recipe makes {recipe.servings})
        </p>
      )}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {nutritionEntries.map(([key, value]) => (
          <div
            key={key}
            className="rounded-lg bg-muted/50 p-3"
          >
            <span className="block text-sm text-muted-foreground">
              {formatNutritionKey(key)}
            </span>
            <span className="text-lg font-medium text-foreground">{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function TipsLoadingState({ subtitle }: { subtitle?: string }) {
  return (
    <div className="text-center">
      <Sparkles className="mx-auto mb-3 h-8 w-8 animate-pulse text-primary" />
      <p className="text-foreground">Generating cooking tips...</p>
      {subtitle && (
        <p className="mt-2 text-sm text-muted-foreground">{subtitle}</p>
      )}
    </div>
  )
}

function TipsEmptyState({
  aiAvailable,
  onGenerateTips,
}: {
  aiAvailable?: boolean
  onGenerateTips: (regenerate: boolean) => void
}) {
  return (
    <div className="text-center">
      <Sparkles className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
      <p className="mb-2 text-foreground">No cooking tips yet</p>
      {aiAvailable ? (
        <button
          onClick={() => onGenerateTips(false)}
          className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          Generate Tips
        </button>
      ) : (
        <p className="text-sm text-muted-foreground">
          Configure an API key in settings to enable AI-generated tips
        </p>
      )}
    </div>
  )
}

function ScalingNotesSection({ notes }: { notes: string[] }) {
  if (notes.length === 0) return null

  return (
    <div className="rounded-lg bg-accent/10 p-3">
      <h4 className="mb-2 flex items-center gap-2 text-sm font-medium text-foreground">
        <Sparkles className="h-4 w-4 text-accent" />
        Scaling Notes
      </h4>
      <ul className="space-y-1 text-sm text-muted-foreground">
        {notes.map((note, index) => (
          <li key={index}>• {note}</li>
        ))}
      </ul>
    </div>
  )
}

function TipsTab({
  tips,
  scalingNotes,
  aiAvailable,
  loading,
  polling,
  onGenerateTips,
}: {
  tips: string[]
  scalingNotes: string[]
  aiAvailable?: boolean
  loading: boolean
  polling: boolean
  onGenerateTips: (regenerate: boolean) => void
}) {
  if (loading) return <TipsLoadingState />

  const hasTips = tips.length > 0
  const hasContent = hasTips || scalingNotes.length > 0

  if (!hasContent && polling) {
    return <TipsLoadingState subtitle="Tips are being generated in the background" />
  }

  if (!hasContent) {
    return <TipsEmptyState aiAvailable={aiAvailable} onGenerateTips={onGenerateTips} />
  }

  return (
    <div className="space-y-4">
      <ScalingNotesSection notes={scalingNotes} />

      {hasTips && (
        <ol className="space-y-3">
          {tips.map((tip, index) => (
            <li key={index} className="flex items-start gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent text-xs font-medium text-accent-foreground">
                {index + 1}
              </span>
              <p className="text-foreground">{tip}</p>
            </li>
          ))}
        </ol>
      )}

      {aiAvailable && (
        <div className="text-center pt-4">
          <button
            onClick={() => onGenerateTips(hasTips)}
            className="rounded-lg bg-muted px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted/80 hover:text-foreground"
          >
            {hasTips ? 'Regenerate Tips' : 'Generate Tips'}
          </button>
        </div>
      )}
    </div>
  )
}
