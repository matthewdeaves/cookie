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
  type Settings,
} from '../api/client'
import { cn } from '../lib/utils'
import AddToCollectionDropdown from '../components/AddToCollectionDropdown'

interface RecipeDetailProps {
  recipeId: number
  isFavorite: boolean
  onBack: () => void
  onFavoriteToggle: (recipe: RecipeDetailType) => void
  onStartCooking: (recipe: RecipeDetailType) => void
  onAddToNewCollection: (recipeId: number) => void
}

type Tab = 'ingredients' | 'instructions' | 'nutrition' | 'tips'

export default function RecipeDetail({
  recipeId,
  isFavorite,
  onBack,
  onFavoriteToggle,
  onStartCooking,
  onAddToNewCollection,
}: RecipeDetailProps) {
  const [recipe, setRecipe] = useState<RecipeDetailType | null>(null)
  const [settings, setSettings] = useState<Settings | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<Tab>('ingredients')
  const [metaExpanded, setMetaExpanded] = useState(true)
  const [servings, setServings] = useState<number | null>(null)

  useEffect(() => {
    loadData()
  }, [recipeId])

  const loadData = async () => {
    try {
      const [recipeData, settingsData] = await Promise.all([
        api.recipes.get(recipeId),
        api.settings.get(),
      ])
      setRecipe(recipeData)
      setSettings(settingsData)
      setServings(recipeData.servings)
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
    settings?.ai_available && recipe?.servings !== null

  const handleServingChange = (delta: number) => {
    if (!servings) return
    const newServings = Math.max(1, servings + delta)
    setServings(newServings)
    // TODO: In Phase 8, call AI to adjust ingredient quantities
    toast.info('Serving adjustment will be AI-powered in Phase 8')
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <span className="text-muted-foreground">Loading...</span>
      </div>
    )
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
          <button
            onClick={() => toast.info('Remix coming in Phase 8')}
            className="rounded-full bg-black/40 p-2 text-white backdrop-blur-sm transition-colors hover:text-primary"
            title="Remix recipe"
          >
            <Sparkles className="h-5 w-5" />
          </button>
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
                  {formatTime(recipe.prep_time)}
                </span>
              </div>
            )}

            {/* Cook time */}
            {recipe.cook_time && (
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Cook:</span>
                <span className="text-foreground">
                  {formatTime(recipe.cook_time)}
                </span>
              </div>
            )}

            {/* Total time */}
            {recipe.total_time && (
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Total:</span>
                <span className="text-foreground">
                  {formatTime(recipe.total_time)}
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
                    disabled={servings <= 1}
                    className="rounded-md bg-muted p-1 text-foreground transition-colors hover:bg-muted/80 disabled:opacity-50"
                  >
                    <Minus className="h-4 w-4" />
                  </button>
                  <span className="w-8 text-center font-medium text-foreground">
                    {servings}
                  </span>
                  <button
                    onClick={() => handleServingChange(1)}
                    className="rounded-md bg-muted p-1 text-foreground transition-colors hover:bg-muted/80"
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>
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
              { key: 'ingredients', label: 'Ingredients' },
              { key: 'instructions', label: 'Instructions' },
              { key: 'nutrition', label: 'Nutrition' },
              { key: 'tips', label: 'Tips' },
            ] as const
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
          <IngredientsTab recipe={recipe} />
        )}
        {activeTab === 'instructions' && (
          <InstructionsTab recipe={recipe} />
        )}
        {activeTab === 'nutrition' && (
          <NutritionTab recipe={recipe} />
        )}
        {activeTab === 'tips' && (
          <TipsTab recipe={recipe} aiAvailable={settings?.ai_available} />
        )}
      </div>
    </div>
  )
}

function IngredientsTab({ recipe }: { recipe: RecipeDetailType }) {
  // Use ingredient_groups if available, otherwise flat ingredients list
  const hasGroups = recipe.ingredient_groups.length > 0

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
      {recipe.ingredients.map((ingredient, index) => (
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

function InstructionsTab({ recipe }: { recipe: RecipeDetailType }) {
  const instructions = recipe.instructions.length > 0
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
          Per {recipe.servings} serving{recipe.servings > 1 ? 's' : ''}
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
  recipe,
  aiAvailable,
}: {
  recipe: RecipeDetailType
  aiAvailable?: boolean
}) {
  const tips = recipe.ai_tips || []

  if (tips.length === 0) {
    return (
      <div className="text-center">
        <Sparkles className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
        <p className="mb-2 text-foreground">No cooking tips yet</p>
        {aiAvailable ? (
          <p className="text-sm text-muted-foreground">
            Tips will be generated when you start cooking
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">
            Configure an API key in settings to enable AI-generated tips
          </p>
        )}
      </div>
    )
  }

  return (
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
  )
}
