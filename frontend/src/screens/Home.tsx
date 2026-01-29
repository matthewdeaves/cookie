import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Moon, Sun, LogOut, Search, Sparkles, Heart, FolderOpen, Settings, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import {
  api,
  type Recipe,
  type Favorite,
  type HistoryItem,
  type DiscoverSuggestion,
} from '../api/client'
import { useProfile } from '../contexts/ProfileContext'
import { useAIStatus } from '../contexts/AIStatusContext'
import RecipeCard from '../components/RecipeCard'
import { RecipeGridSkeleton } from '../components/Skeletons'
import { cn } from '../lib/utils'

type Tab = 'favorites' | 'discover'

export default function Home() {
  const navigate = useNavigate()
  const { profile, theme, toggleTheme, logout } = useProfile()
  const aiStatus = useAIStatus()

  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<Tab>('favorites')
  const [favorites, setFavorites] = useState<Favorite[]>([])
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [historyCount, setHistoryCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [discoverSuggestions, setDiscoverSuggestions] = useState<DiscoverSuggestion[]>([])
  const [discoverLoading, setDiscoverLoading] = useState(false)
  const [discoverError, setDiscoverError] = useState(false)
  const [_discoverRefreshedAt, setDiscoverRefreshedAt] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [favoritesData, historyData] = await Promise.all([
        api.favorites.list(),
        api.history.list(1000),
      ])
      setFavorites(favoritesData)
      setHistoryCount(historyData.length)
      setHistory(historyData.slice(0, 6))
    } catch (error) {
      console.error('Failed to load data:', error)
      toast.error('Failed to load recipes')
    } finally {
      setLoading(false)
    }
  }

  const loadDiscoverSuggestions = async () => {
    if (!profile) return
    setDiscoverLoading(true)
    setDiscoverError(false)
    try {
      const result = await api.ai.discover(profile.id)
      setDiscoverSuggestions(result.suggestions)
      setDiscoverRefreshedAt(result.refreshed_at)
    } catch (error) {
      console.error('Failed to load discover suggestions:', error)
      setDiscoverError(true)
    } finally {
      setDiscoverLoading(false)
    }
  }

  // Load discover suggestions when tab is clicked (Task 4.3 - move to onClick)
  const handleDiscoverTabClick = () => {
    setActiveTab('discover')
    if (discoverSuggestions.length === 0 && !discoverLoading && !discoverError && aiStatus.available) {
      loadDiscoverSuggestions()
    }
  }

  const handleSuggestionClick = (suggestion: DiscoverSuggestion) => {
    navigate(`/search?q=${encodeURIComponent(suggestion.search_query)}`)
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  const handleRecipeClick = async (recipeId: number) => {
    try {
      await api.history.record(recipeId)
    } catch (error) {
      console.error('Failed to record history:', error)
    }
    navigate(`/recipe/${recipeId}`)
  }

  const handleRemoveFavorite = async (recipe: Recipe) => {
    try {
      await api.favorites.remove(recipe.id)
      setFavorites(favorites.filter((f) => f.recipe.id !== recipe.id))
      toast.success('Removed from favorites')
    } catch (error) {
      console.error('Failed to remove favorite:', error)
      toast.error('Failed to remove from favorites')
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const getInitial = (name: string) => {
    return name.charAt(0).toUpperCase()
  }

  // Memoize favorite IDs set (Task 5.2)
  const localFavoriteIds = useMemo(
    () => new Set(favorites.map((f) => f.recipe.id)),
    [favorites]
  )

  if (!profile) return null

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border px-4 py-3">
        <h1 className="text-xl font-medium text-primary">Cookie</h1>

        <div className="flex items-center gap-3">
          {/* Favorites */}
          <button
            onClick={() => navigate('/favorites')}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-accent"
            aria-label="View favorites"
          >
            <Heart className="h-5 w-5" />
          </button>

          {/* Collections */}
          <button
            onClick={() => navigate('/collections')}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
            aria-label="View collections"
          >
            <FolderOpen className="h-5 w-5" />
          </button>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
          >
            {theme === 'light' ? (
              <Moon className="h-5 w-5" />
            ) : (
              <Sun className="h-5 w-5" />
            )}
          </button>

          {/* Settings */}
          <button
            onClick={() => navigate('/settings')}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Settings"
          >
            <Settings className="h-5 w-5" />
          </button>

          {/* Profile avatar */}
          <button
            onClick={handleLogout}
            className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-medium text-white"
            style={{ backgroundColor: profile.avatar_color }}
            aria-label="Switch profile"
          >
            {getInitial(profile.name)}
          </button>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Switch profile"
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 px-4 py-6">
        <div className="mx-auto max-w-4xl">
          {/* Search bar */}
          <form onSubmit={handleSearchSubmit} className="mb-6">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search recipes or paste a URL..."
                className="w-full rounded-xl border border-border bg-input-background py-3 pl-12 pr-4 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </form>

          {/* Tab toggle - only show if AI is available */}
          {aiStatus.available && (
            <div className="mb-6 flex justify-center">
              <div className="inline-flex rounded-lg bg-muted p-1">
                <button
                  onClick={() => setActiveTab('favorites')}
                  className={cn(
                    'rounded-md px-4 py-2 text-sm font-medium transition-colors',
                    activeTab === 'favorites'
                      ? 'bg-background text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  My Favorites
                </button>
                <button
                  onClick={handleDiscoverTabClick}
                  className={cn(
                    'rounded-md px-4 py-2 text-sm font-medium transition-colors',
                    activeTab === 'discover'
                      ? 'bg-background text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  Discover
                </button>
              </div>
            </div>
          )}

          {loading ? (
            <RecipeGridSkeleton count={6} />
          ) : activeTab === 'favorites' || !aiStatus.available ? (
            <>
              {/* Recently Viewed */}
              {history.length > 0 && (
                <section className="mb-8">
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-lg font-medium text-foreground">
                      Recently Viewed
                    </h2>
                    <button
                      onClick={() => navigate('/all-recipes')}
                      className="text-sm font-medium text-primary hover:underline"
                    >
                      View All ({historyCount})
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
                    {history.map((item) => (
                      <RecipeCard
                        key={item.recipe.id}
                        recipe={item.recipe}
                        isFavorite={localFavoriteIds.has(item.recipe.id)}
                        onClick={() => handleRecipeClick(item.recipe.id)}
                      />
                    ))}
                  </div>
                </section>
              )}

              {/* Favorites */}
              <section>
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-lg font-medium text-foreground">
                    My Favorite Recipes
                  </h2>
                  {favorites.length > 0 && (
                    <button
                      onClick={() => navigate('/favorites')}
                      className="text-sm font-medium text-primary hover:underline"
                    >
                      View All ({favorites.length})
                    </button>
                  )}
                </div>
                {favorites.length > 0 ? (
                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
                    {favorites.map((favorite) => (
                      <RecipeCard
                        key={favorite.recipe.id}
                        recipe={favorite.recipe}
                        isFavorite
                        onFavoriteToggle={handleRemoveFavorite}
                        onClick={() => handleRecipeClick(favorite.recipe.id)}
                      />
                    ))}
                  </div>
                ) : (
                  /* Empty state */
                  <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border py-12">
                    <div className="mb-4 rounded-full bg-muted p-4">
                      <Search className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <h3 className="mb-2 text-lg font-medium text-foreground">
                      No favorites yet
                    </h3>
                    <p className="mb-4 text-center text-muted-foreground">
                      Search for recipes and add them to your favorites
                    </p>
                    <button
                      onClick={() => document.querySelector('input')?.focus()}
                      className="rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
                    >
                      Discover Recipes
                    </button>
                  </div>
                )}
              </section>
            </>
          ) : (
            /* Discover tab - AI recommendations */
            <div>
              {discoverLoading ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="mb-4 rounded-full bg-muted p-4">
                    <Sparkles className="h-8 w-8 animate-pulse text-primary" />
                  </div>
                  <p className="text-muted-foreground">
                    Generating personalized suggestions...
                  </p>
                </div>
              ) : discoverSuggestions.length > 0 ? (
                <div className="space-y-6">
                  {/* Header with refresh time */}
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-medium text-foreground">
                      Personalized For You
                    </h2>
                    <button
                      onClick={loadDiscoverSuggestions}
                      className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
                      disabled={discoverLoading}
                    >
                      <RefreshCw className={cn('h-4 w-4', discoverLoading && 'animate-spin')} />
                      Refresh
                    </button>
                  </div>

                  {/* Suggestions grid */}
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {discoverSuggestions.map((suggestion, index) => (
                      <button
                        key={`${suggestion.type}-${index}`}
                        onClick={() => handleSuggestionClick(suggestion)}
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
                    ))}
                  </div>
                </div>
              ) : !aiStatus.available ? (
                /* Empty state - AI unavailable (no API key) */
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="mb-4 rounded-full bg-muted p-4">
                    <Sparkles className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <h3 className="mb-2 text-lg font-medium text-foreground">
                    AI Recommendations
                  </h3>
                  <p className="mb-4 text-center text-muted-foreground">
                    Configure an API key in settings to enable personalized recipe suggestions
                  </p>
                  <button
                    onClick={() => navigate('/settings')}
                    className="rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
                  >
                    Go to Settings
                  </button>
                </div>
              ) : discoverError ? (
                /* Empty state - API error */
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="mb-4 rounded-full bg-muted p-4">
                    <Sparkles className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <h3 className="mb-2 text-lg font-medium text-foreground">
                    Unable to Load Suggestions
                  </h3>
                  <p className="mb-4 text-center text-muted-foreground">
                    Something went wrong. Please try again.
                  </p>
                  <button
                    onClick={loadDiscoverSuggestions}
                    className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Try Again
                  </button>
                </div>
              ) : (
                /* Empty state - No suggestions available */
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="mb-4 rounded-full bg-muted p-4">
                    <Sparkles className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <h3 className="mb-2 text-lg font-medium text-foreground">
                    No Suggestions Yet
                  </h3>
                  <p className="mb-4 text-center text-muted-foreground">
                    Add some favorites to get personalized recommendations
                  </p>
                  <button
                    onClick={() => setActiveTab('favorites')}
                    className="rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
                  >
                    View Favorites
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
