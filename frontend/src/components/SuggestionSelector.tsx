import { Check, Loader2 } from 'lucide-react'
import { cn } from '../lib/utils'

interface SuggestionSelectorProps {
  suggestions: string[]
  selectedSuggestions: string[]
  loadingSuggestions: boolean
  disabled: boolean
  onSuggestionClick: (suggestion: string) => void
}

export default function SuggestionSelector({
  suggestions,
  selectedSuggestions,
  loadingSuggestions,
  disabled,
  onSuggestionClick,
}: SuggestionSelectorProps) {
  return (
    <div className="mb-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium text-foreground">Suggestions</h3>
        {selectedSuggestions.length > 0 && (
          <span className="text-xs text-muted-foreground">
            {selectedSuggestions.length} selected
          </span>
        )}
      </div>
      {loadingSuggestions ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <span className="ml-2 text-sm text-muted-foreground">
            Generating suggestions...
          </span>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {suggestions.map((suggestion, index) => {
            const isSelected = selectedSuggestions.includes(suggestion)
            return (
              <button
                key={index}
                onClick={() => onSuggestionClick(suggestion)}
                disabled={disabled}
                className={cn(
                  'flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm transition-colors',
                  isSelected
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground hover:bg-muted/80'
                )}
              >
                {isSelected && <Check className="h-3.5 w-3.5" />}
                {suggestion}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
