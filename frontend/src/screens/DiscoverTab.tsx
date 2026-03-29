import { useNavigate } from 'react-router-dom'
import { Search, Sparkles, RefreshCw } from 'lucide-react'
import type { DiscoverSuggestion } from '../api/client'
import { cn } from '../lib/utils'

interface DiscoverTabProps {
  suggestions: DiscoverSuggestion[]
  loading: boolean
  error: boolean
  aiAvailable: boolean
  onRefresh: () => void
  onRetry: () => void
  onSwitchToFavorites: () => void
}

function DiscoverEmptyState({ icon, title, description, action }: {
  icon: React.ReactNode
  title: string
  description: string
  action: React.ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="mb-4 rounded-full bg-muted p-4">{icon}</div>
      {title && <h3 className="mb-2 text-lg font-medium text-foreground">{title}</h3>}
      <p className="mb-4 text-center text-muted-foreground">{description}</p>
      {action}
    </div>
  )
}

function SuggestionCard({ suggestion, onClick }: {
  suggestion: DiscoverSuggestion
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="group flex flex-col rounded-xl border border-border bg-card p-4 text-left transition-all hover:border-primary hover:shadow-md"
    >
      <div className="mb-2 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <span className="text-xs uppercase tracking-wide text-muted-foreground">
          {suggestion.type === 'favorites' && 'Based on Favorites'}
          {suggestion.type === 'seasonal' && 'Seasonal'}
          {suggestion.type === 'new' && 'Try Something New'}
        </span>
      </div>
      <h3 className="mb-1 font-medium text-foreground group-hover:text-primary">
        {suggestion.title}
      </h3>
      <p className="text-sm text-muted-foreground">
        {suggestion.description}
      </p>
      <div className="mt-3 flex items-center gap-1 text-xs text-primary">
        <Search className="h-3 w-3" />
        <span>Search: {suggestion.search_query}</span>
      </div>
    </button>
  )
}

function SuggestionsGrid({ suggestions, loading, onRefresh, onSuggestionClick }: {
  suggestions: DiscoverSuggestion[]
  loading: boolean
  onRefresh: () => void
  onSuggestionClick: (suggestion: DiscoverSuggestion) => void
}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-foreground">
          Personalized For You
        </h2>
        <button
          onClick={onRefresh}
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
          disabled={loading}
        >
          <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
          Refresh
        </button>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {suggestions.map((suggestion, index) => (
          <SuggestionCard
            key={`${suggestion.type}-${index}`}
            suggestion={suggestion}
            onClick={() => onSuggestionClick(suggestion)}
          />
        ))}
      </div>
    </div>
  )
}

export default function DiscoverTab({
  suggestions,
  loading,
  error,
  aiAvailable,
  onRefresh,
  onRetry,
  onSwitchToFavorites,
}: DiscoverTabProps) {
  const navigate = useNavigate()

  if (loading) {
    return (
      <DiscoverEmptyState
        icon={<Sparkles className="h-8 w-8 animate-pulse text-primary" />}
        title=""
        description="Generating personalized suggestions..."
        action={null}
      />
    )
  }

  if (suggestions.length > 0) {
    return (
      <SuggestionsGrid
        suggestions={suggestions}
        loading={loading}
        onRefresh={onRefresh}
        onSuggestionClick={(s) => navigate(`/search?q=${encodeURIComponent(s.search_query)}`)}
      />
    )
  }

  if (!aiAvailable) {
    return (
      <DiscoverEmptyState
        icon={<Sparkles className="h-8 w-8 text-muted-foreground" />}
        title="AI Recommendations"
        description="Configure an API key in settings to enable personalized recipe suggestions"
        action={
          <button
            onClick={() => navigate('/settings')}
            className="rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Go to Settings
          </button>
        }
      />
    )
  }

  if (error) {
    return (
      <DiscoverEmptyState
        icon={<Sparkles className="h-8 w-8 text-muted-foreground" />}
        title="Unable to Load Suggestions"
        description="Something went wrong. Please try again."
        action={
          <button
            onClick={onRetry}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </button>
        }
      />
    )
  }

  return (
    <DiscoverEmptyState
      icon={<Sparkles className="h-8 w-8 text-muted-foreground" />}
      title="No Suggestions Yet"
      description="Add some favorites to get personalized recommendations"
      action={
        <button
          onClick={onSwitchToFavorites}
          className="rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
        >
          View Favorites
        </button>
      }
    />
  )
}
