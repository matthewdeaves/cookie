import { useState, useEffect } from 'react'
import {
  ArrowLeft,
  Star,
  Clock,
  Heart,
  PlayCircle,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Minus,
  Plus,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  api,
  type RecipeDetail as RecipeDetailType,
  type ScaleResponse,
} from '../api/client'
import { cn } from '../lib/utils'
import AddToCollectionDropdown from '../components/AddToCollectionDropdown'
import RemixModal from '../components/RemixModal'
import { useAIStatus } from '../contexts/AIStatusContext'
import { RecipeDetailSkeleton } from '../components/Skeletons'

interface RecipeDetailProps {
  recipeId: number
  profileId: number
  isFavorite: boolean
  onBack: () => void
  onFavoriteToggle: (recipe: RecipeDetailType) => void
  onStartCooking: (recipe: RecipeDetailType) => void
  onAddToNewCollection: (recipeId: number) => void
  onRemixCreated: (recipeId: number) => void
}

type Tab = 'ingredients' | 'instructions' | 'nutrition' | 'tips'

export default function RecipeDetail({
  recipeId,
  profileId,
  isFavorite,
  onBack,
  onFavoriteToggle,
  onStartCooking,
  onAddToNewCollection,
  onRemixCreated,
}: RecipeDetailProps) {
  const [recipe, setRecipe] = useState<RecipeDetailType | null>(null)
  const aiStatus = useAIStatus()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<Tab>('ingredients')
  const [metaExpanded, setMetaExpanded] = useState(true)
  const [servings, setServings] = useState<number | null>(null)
  const [showRemixModal, setShowRemixModal] = useState(false)
  const [scaledData, setScaledData] = useState<ScaleResponse | null>(null)
  const [scalingLoading, setScalingLoading] = useState(false)
  const [tips, setTips] = useState<string[]>([])
  const [tipsLoading, setTipsLoading] = useState(false)
  const [tipsPolling, setTipsPolling] = useState(false)

  useEffect(() => {
    loadData()
  }, [recipeId])

  // Poll for tips if recipe is recently imported and has no tips yet
  useEffect(() => {
    if (!recipe) return

    const recipeAge = Date.now() - new Date(recipe.scraped_at).getTime()
    const isRecent = recipeAge < 60000 // 60 seconds

    // Only poll for recent recipes with no tips
    if (!isRecent || tips.length > 0) {
      setTipsPolling(false)
      return
    }

    setTipsPolling(true)
    const startTime = Date.now()
    const POLL_INTERVAL = 3000 // 3 seconds
    const MAX_POLL_DURATION = 30000 // 30 seconds

    const interval = setInterval(async () => {
      // Stop if we've been polling too long
      if (Date.now() - startTime > MAX_POLL_DURATION) {
        clearInterval(interval)
        setTipsPolling(false)
        return
      }

      try {
        const updated = await api.recipes.get(recipe.id)
        if (updated.ai_tips && updated.ai_tips.length > 0) {
          setTips(updated.ai_tips)
          setRecipe((prev) => prev ? { ...prev, ai_tips: updated.ai_tips } : prev)
          clearInterval(interval)
          setTipsPolling(false)
        }
      } catch {
        // Ignore polling errors, will retry on next interval
      }
    }, POLL_INTERVAL)

    return () => {
      clearInterval(interval)
      setTipsPolling(false)
    }
  }, [recipe?.id, recipe?.scraped_at, tips.length])

  // Auto-generate tips when viewing Tips tab for old recipes without tips (QA-046)
  useEffect(() => {
    if (
      activeTab === 'tips' &&
      tips.length === 0 &&
      aiStatus.available &&
      !tipsLoading &&
      !tipsPolling &&
      recipe
    ) {
      handleGenerateTips(false)
    }
  }, [activeTab]) // Only trigger on tab change

  const loadData = async () => {
    try {
      const recipeData = await api.recipes.get(recipeId)
      setRecipe(recipeData)
      setServings(recipeData.servings)
      setTips(recipeData.ai_tips || [])
      // Reset scaled data when loading a new recipe
      setScaledData(null)
    } catch (error) {
      console.error('Failed to load recipe:', error)
      toast.error('Failed to load recipe')
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (minutes: number | null) => {
    if (!minutes) return null
    if (minutes < 60) return `${minutes} min`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }

  const canShowServingAdjustment =
    aiStatus.available && recipe?.servings !== null

  const handleServingChange = async (delta: number) => {
    if (!servings || !recipe) return
    const newServings = Math.max(1, servings + delta)
    setServings(newServings)

    // If returning to original servings, clear scaled data
    if (newServings === recipe.servings) {
      setScaledData(null)
      return
    }

    // Call AI to scale ingredients
    setScalingLoading(true)
    try {
      const result = await api.ai.scale(recipe.id, newServings, profileId)
      setScaledData(result)
      if (result.notes.length > 0) {
        toast.info(result.notes[0])
      }
    } catch (error) {
      console.error('Failed to scale recipe:', error)
      toast.error('Failed to scale ingredients')
      // Revert to previous servings on error
      setServings(servings)
    } finally {
      setScalingLoading(false)
    }
  }

  const handleGenerateTips = async (regenerate: boolean = false) => {
    if (!recipe || tipsLoading) return

    setTipsLoading(true)
    try {
      const result = await api.ai.tips(recipe.id, regenerate)
      setTips(result.tips)
      // Update the recipe object too
      setRecipe({ ...recipe, ai_tips: result.tips })
      toast.success(regenerate ? 'Tips regenerated!' : 'Tips generated!')
    } catch (error) {
      console.error('Failed to generate tips:', error)
      toast.error('Failed to generate tips')
    } finally {
      setTipsLoading(false)
    }
  }

  if (loading) {
    return <RecipeDetailSkeleton />
  }

  if (!recipe) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background">
        <span className="mb-4 text-muted-foreground">Recipe not found</span>
        <button
          onClick={onBack}
          className="rounded-lg bg-primary px-4 py-2 text-primary-foreground"
        >
          Go Back
        </button>
      </div>
    )
  }

  const imageUrl = recipe.image || recipe.image_url

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Image */}
      <div className="relative h-64 sm:h-80">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={recipe.title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-muted">
            <span className="text-muted-foreground">No image</span>
          </div>
        )}

        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />

        {/* Back button */}
        <button
          onClick={onBack}
          className="absolute left-4 top-4 rounded-full bg-black/40 p-2 text-white backdrop-blur-sm transition-colors hover:bg-black/60"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>

        {/* Title and rating overlay */}
        <div className="absolute bottom-4 left-4 right-4">
          <h1 className="mb-2 text-xl font-medium text-white drop-shadow-lg sm:text-2xl">
            {recipe.title}
          </h1>
          <div className="flex items-center gap-3 text-sm text-white/90">
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
            <span>{recipe.host}</span>
          </div>
        </div>

        {/* Action buttons */}
        <div className="absolute bottom-4 right-4 flex gap-2">
          <button
            onClick={() => onFavoriteToggle(recipe)}
            className={cn(
              'rounded-full bg-black/40 p-2 backdrop-blur-sm transition-colors',
              isFavorite ? 'text-accent' : 'text-white hover:text-accent'
            )}
            title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
          >
            <Heart className={cn('h-5 w-5', isFavorite && 'fill-current')} />
          </button>
          <AddToCollectionDropdown
            recipeId={recipeId}
            onCreateNew={() => onAddToNewCollection(recipeId)}
          />
          {aiStatus.available && (
            <button
              onClick={() => setShowRemixModal(true)}
              className="rounded-full bg-black/40 p-2 text-white backdrop-blur-sm transition-colors hover:text-primary"
              title="Remix recipe"
            >
              <Sparkles className="h-5 w-5" />
            </button>
          )}
          <button
            onClick={() => onStartCooking(recipe)}
            className="flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            <PlayCircle className="h-4 w-4" />
            Cook!
          </button>
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
            {/* Prep time */}
            {recipe.prep_time && (
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Prep:</span>
                <span className="text-foreground">
                  {scaledData?.prep_time_adjusted &&
                  scaledData.prep_time_adjusted !== recipe.prep_time ? (
                    <>
                      {formatTime(scaledData.prep_time_adjusted)}
                      <span className="ml-1 text-muted-foreground">
                        (was {formatTime(recipe.prep_time)})
                      </span>
                    </>
                  ) : (
                    formatTime(scaledData?.prep_time_adjusted ?? recipe.prep_time)
                  )}
                </span>
              </div>
            )}

            {/* Cook time */}
            {recipe.cook_time && (
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Cook:</span>
                <span className="text-foreground">
                  {scaledData?.cook_time_adjusted &&
                  scaledData.cook_time_adjusted !== recipe.cook_time ? (
                    <>
                      {formatTime(scaledData.cook_time_adjusted)}
                      <span className="ml-1 text-muted-foreground">
                        (was {formatTime(recipe.cook_time)})
                      </span>
                    </>
                  ) : (
                    formatTime(scaledData?.cook_time_adjusted ?? recipe.cook_time)
                  )}
                </span>
              </div>
            )}

            {/* Total time */}
            {recipe.total_time && (
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Total:</span>
                <span className="text-foreground">
                  {scaledData?.total_time_adjusted &&
                  scaledData.total_time_adjusted !== recipe.total_time ? (
                    <>
                      {formatTime(scaledData.total_time_adjusted)}
                      <span className="ml-1 text-muted-foreground">
                        (was {formatTime(recipe.total_time)})
                      </span>
                    </>
                  ) : (
                    formatTime(scaledData?.total_time_adjusted ?? recipe.total_time)
                  )}
                </span>
              </div>
            )}

            {/* Servings adjuster - only show if AI available and servings present */}
            {canShowServingAdjustment && servings && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground">Servings:</span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleServingChange(-1)}
                    disabled={servings <= 1 || scalingLoading}
                    className="rounded-md bg-muted p-1 text-foreground transition-colors hover:bg-muted/80 disabled:opacity-50"
                  >
                    <Minus className="h-4 w-4" />
                  </button>
                  <span className="w-8 text-center font-medium text-foreground">
                    {scalingLoading ? '...' : servings}
                  </span>
                  <button
                    onClick={() => handleServingChange(1)}
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

      {/* Tabs */}
      <div className="border-b border-border">
        <div className="flex px-4">
          {(
            [
              { key: 'ingredients' as const, label: 'Ingredients' },
              { key: 'instructions' as const, label: 'Instructions' },
              { key: 'nutrition' as const, label: 'Nutrition' },
              // Only show Tips tab when AI is available (8B.11 graceful degradation)
              ...(aiStatus.available ? [{ key: 'tips' as const, label: 'Tips' }] : []),
            ]
          ).map(({ key, label }) => (
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
          <IngredientsTab recipe={recipe} scaledData={scaledData} />
        )}
        {activeTab === 'instructions' && (
          <InstructionsTab recipe={recipe} scaledData={scaledData} />
        )}
        {activeTab === 'nutrition' && (
          <NutritionTab recipe={recipe} />
        )}
        {activeTab === 'tips' && (
          <TipsTab
            tips={tips}
            scalingNotes={scaledData?.notes || []}
            aiAvailable={aiStatus.available}
            loading={tipsLoading}
            polling={tipsPolling}
            onGenerateTips={handleGenerateTips}
          />
        )}
      </div>

      {/* Remix Modal */}
      <RemixModal
        recipe={recipe}
        profileId={profileId}
        isOpen={showRemixModal}
        onClose={() => setShowRemixModal(false)}
        onRemixCreated={onRemixCreated}
      />
    </div>
  )
}

function IngredientsTab({
  recipe,
  scaledData,
}: {
  recipe: RecipeDetailType
  scaledData: ScaleResponse | null
}) {
  // Use scaled ingredients if available, otherwise use recipe ingredients
  const ingredients = scaledData?.ingredients || recipe.ingredients

  // Use ingredient_groups if available and not scaled, otherwise flat ingredients list
  const hasGroups = recipe.ingredient_groups.length > 0 && !scaledData

  if (hasGroups) {
    return (
      <div className="space-y-6">
        {recipe.ingredient_groups.map((group, groupIndex) => (
          <div key={groupIndex}>
            {group.purpose && (
              <h3 className="mb-3 font-medium text-foreground">
                {group.purpose}
              </h3>
            )}
            <ol className="space-y-2">
              {group.ingredients.map((ingredient, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 text-foreground"
                >
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
                    {index + 1}
                  </span>
                  <span>{ingredient}</span>
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>
    )
  }

  return (
    <ol className="space-y-2">
      {ingredients.map((ingredient, index) => (
        <li key={index} className="flex items-start gap-3 text-foreground">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
            {index + 1}
          </span>
          <span>{ingredient}</span>
        </li>
      ))}
    </ol>
  )
}

function InstructionsTab({
  recipe,
  scaledData,
}: {
  recipe: RecipeDetailType
  scaledData: ScaleResponse | null
}) {
  // Use scaled instructions if available, otherwise fall back to original
  const hasScaledInstructions = scaledData?.instructions && scaledData.instructions.length > 0
  const instructions = hasScaledInstructions
    ? scaledData.instructions
    : recipe.instructions.length > 0
      ? recipe.instructions
      : recipe.instructions_text
        ? recipe.instructions_text.split('\n').filter((s) => s.trim())
        : []

  if (instructions.length === 0) {
    return (
      <p className="text-muted-foreground">
        No instructions available for this recipe.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      {hasScaledInstructions && (
        <p className="text-sm text-muted-foreground">
          Instructions adjusted for {scaledData.target_servings} servings
        </p>
      )}
      <ol className="space-y-4">
        {instructions.map((step, index) => (
          <li key={index} className="flex items-start gap-4">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
              {index + 1}
            </span>
            <p className="pt-0.5 text-foreground">{step}</p>
          </li>
        ))}
      </ol>
    </div>
  )
}

function NutritionTab({ recipe }: { recipe: RecipeDetailType }) {
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
            <span className="block text-sm capitalize text-muted-foreground">
              {key.replace(/_/g, ' ')}
            </span>
            <span className="text-lg font-medium text-foreground">{value}</span>
          </div>
        ))}
      </div>
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
  // Show loading state when manually generating tips
  if (loading) {
    return (
      <div className="text-center">
        <Sparkles className="mx-auto mb-3 h-8 w-8 animate-pulse text-primary" />
        <p className="text-foreground">Generating cooking tips...</p>
      </div>
    )
  }

  const hasTips = tips.length > 0
  const hasContent = hasTips || scalingNotes.length > 0

  // Show polling state when waiting for background generation
  if (!hasContent && polling) {
    return (
      <div className="text-center">
        <Sparkles className="mx-auto mb-3 h-8 w-8 animate-pulse text-primary" />
        <p className="text-foreground">Generating cooking tips...</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Tips are being generated in the background
        </p>
      </div>
    )
  }

  if (!hasContent) {
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

  return (
    <div className="space-y-4">
      {/* Scaling notes */}
      {scalingNotes.length > 0 && (
        <div className="rounded-lg bg-accent/10 p-3">
          <h4 className="mb-2 flex items-center gap-2 text-sm font-medium text-foreground">
            <Sparkles className="h-4 w-4 text-accent" />
            Scaling Notes
          </h4>
          <ul className="space-y-1 text-sm text-muted-foreground">
            {scalingNotes.map((note, index) => (
              <li key={index}>• {note}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Tips */}
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

      {/* Regenerate/Generate button */}
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
