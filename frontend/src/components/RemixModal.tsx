import { useState, useEffect } from 'react'
import { X, Sparkles, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { api, type RecipeDetail } from '../api/client'
import { cn } from '../lib/utils'
import SuggestionSelector from './SuggestionSelector'
import CustomRemixInput from './CustomRemixInput'

interface RemixModalProps {
  recipe: RecipeDetail
  profileId: number
  isOpen: boolean
  onClose: () => void
  onRemixCreated: (recipeId: number) => void
}

interface RemixHeaderProps {
  onClose: () => void
  disabled: boolean
}

function RemixHeader({ onClose, disabled }: RemixHeaderProps) {
  return (
    <div className="flex items-center justify-between border-b border-border px-6 py-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold text-foreground">Remix This Recipe</h2>
      </div>
      <button
        onClick={onClose}
        disabled={disabled}
        className="rounded-full p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      >
        <X className="h-5 w-5" />
      </button>
    </div>
  )
}

interface RemixCreateButtonProps {
  creating: boolean
  enabled: boolean
  onClick: () => void
}

function RemixCreateButton({ creating, enabled, onClick }: RemixCreateButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={!enabled}
      className={cn(
        'flex w-full items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-colors',
        enabled
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
  )
}

function toggleSuggestion(
  prev: string[],
  suggestion: string,
  clearCustom: () => void
): string[] {
  if (prev.includes(suggestion)) {
    return prev.filter((s) => s !== suggestion)
  }
  if (prev.length >= 4) {
    toast.info('You can select up to 4 modifications')
    return prev
  }
  clearCustom()
  return [...prev, suggestion]
}

function getModification(customInput: string, selectedSuggestions: string[]): string | null {
  if (customInput.trim()) return customInput.trim()
  if (selectedSuggestions.length === 1) return selectedSuggestions[0]
  if (selectedSuggestions.length > 1) return selectedSuggestions.join(' AND ')
  return null
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
  const [selectedSuggestions, setSelectedSuggestions] = useState<string[]>([])
  const [customInput, setCustomInput] = useState('')
  const [creating, setCreating] = useState(false)

  // Load suggestions when modal opens
  useEffect(() => {
    if (isOpen) {
      loadSuggestions()
    } else {
      setSuggestions([])
      setSelectedSuggestions([])
      setCustomInput('')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- loadSuggestions is stable, only re-run when modal opens or recipe changes
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
    setSelectedSuggestions((prev) =>
      toggleSuggestion(prev, suggestion, () => setCustomInput(''))
    )
  }

  const handleCustomInputChange = (value: string) => {
    setCustomInput(value)
    if (value.trim()) setSelectedSuggestions([])
  }

  const canSubmit = !creating && (selectedSuggestions.length > 0 || customInput.trim() !== '')

  const handleCreateRemix = async () => {
    const modification = getModification(customInput, selectedSuggestions)
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
        <RemixHeader onClose={onClose} disabled={creating} />
        <div className="px-6 py-5">
          <p className="mb-4 text-sm text-muted-foreground">
            Choose one or more modifications, or describe your own remix of "{recipe.title}"
          </p>
          <SuggestionSelector
            suggestions={suggestions}
            selectedSuggestions={selectedSuggestions}
            loadingSuggestions={loadingSuggestions}
            disabled={creating}
            onSuggestionClick={handleSuggestionClick}
          />
          <CustomRemixInput
            value={customInput}
            onChange={handleCustomInputChange}
            disabled={creating}
          />
          <RemixCreateButton creating={creating} enabled={canSubmit} onClick={handleCreateRemix} />
        </div>
      </div>
    </div>
  )
}
