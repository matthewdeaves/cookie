import { useState, useEffect } from 'react'
import { X, Sparkles, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { api, type RecipeDetail } from '../api/client'
import { cn } from '../lib/utils'

interface RemixModalProps {
  recipe: RecipeDetail
  profileId: number
  isOpen: boolean
  onClose: () => void
  onRemixCreated: (recipeId: number) => void
}

export default function RemixModal({
  recipe,
  profileId,
  isOpen,
  onClose,
  onRemixCreated,
}: RemixModalProps) {
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null)
  const [customInput, setCustomInput] = useState('')
  const [creating, setCreating] = useState(false)

  // Load suggestions when modal opens
  useEffect(() => {
    if (isOpen) {
      loadSuggestions()
    } else {
      // Reset state when modal closes
      setSuggestions([])
      setSelectedSuggestion(null)
      setCustomInput('')
    }
  }, [isOpen, recipe.id])

  const loadSuggestions = async () => {
    setLoadingSuggestions(true)
    try {
      const response = await api.ai.remix.getSuggestions(recipe.id)
      setSuggestions(response.suggestions)
    } catch (error) {
      console.error('Failed to load remix suggestions:', error)
      toast.error('Failed to load suggestions')
    } finally {
      setLoadingSuggestions(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    if (selectedSuggestion === suggestion) {
      setSelectedSuggestion(null)
    } else {
      setSelectedSuggestion(suggestion)
      setCustomInput('')
    }
  }

  const handleCustomInputChange = (value: string) => {
    setCustomInput(value)
    if (value.trim()) {
      setSelectedSuggestion(null)
    }
  }

  const getModification = () => {
    if (customInput.trim()) {
      return customInput.trim()
    }
    return selectedSuggestion
  }

  const canSubmit = () => {
    return !creating && (selectedSuggestion !== null || customInput.trim() !== '')
  }

  const handleCreateRemix = async () => {
    const modification = getModification()
    if (!modification) return

    setCreating(true)
    try {
      const remix = await api.ai.remix.create(recipe.id, modification, profileId)
      toast.success(`Created "${remix.title}"`)
      onRemixCreated(remix.id)
      onClose()
    } catch (error) {
      console.error('Failed to create remix:', error)
      toast.error('Failed to create remix')
    } finally {
      setCreating(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="relative w-full max-w-md rounded-xl bg-card shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">Remix This Recipe</h2>
          </div>
          <button
            onClick={onClose}
            disabled={creating}
            className="rounded-full p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-5">
          <p className="mb-4 text-sm text-muted-foreground">
            Choose a modification or describe your own remix of "{recipe.title}"
          </p>

          {/* AI Suggestions */}
          <div className="mb-5">
            <h3 className="mb-3 text-sm font-medium text-foreground">Suggestions</h3>
            {loadingSuggestions ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                <span className="ml-2 text-sm text-muted-foreground">
                  Generating suggestions...
                </span>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    disabled={creating}
                    className={cn(
                      'rounded-full px-3 py-1.5 text-sm transition-colors',
                      selectedSuggestion === suggestion
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-foreground hover:bg-muted/80'
                    )}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Custom Input */}
          <div className="mb-5">
            <label
              htmlFor="custom-remix"
              className="mb-2 block text-sm font-medium text-foreground"
            >
              Or describe your own remix
            </label>
            <input
              id="custom-remix"
              type="text"
              value={customInput}
              onChange={(e) => handleCustomInputChange(e.target.value)}
              disabled={creating}
              placeholder="e.g., Make it gluten-free"
              className="w-full rounded-lg border border-border bg-background px-4 py-2.5 text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
            />
          </div>

          {/* Create Button */}
          <button
            onClick={handleCreateRemix}
            disabled={!canSubmit()}
            className={cn(
              'flex w-full items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-colors',
              canSubmit()
                ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                : 'bg-muted text-muted-foreground cursor-not-allowed'
            )}
          >
            {creating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating Remix...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Create Remix
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
