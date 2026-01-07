import { useState, useEffect } from 'react'
import { Moon, Sun, LogOut, Search, Sparkles, Heart, FolderOpen } from 'lucide-react'
import { toast } from 'sonner'
import {
  api,
  type Profile,
  type Recipe,
  type Favorite,
  type HistoryItem,
} from '../api/client'
import RecipeCard from '../components/RecipeCard'
import { cn } from '../lib/utils'

interface HomeProps {
  profile: Profile
  theme: 'light' | 'dark'
  onThemeToggle: () => void
  onLogout: () => void
  onSearch: (query: string) => void
  onRecipeClick: (recipeId: number) => void
  onFavoritesClick: () => void
  onCollectionsClick: () => void
}

type Tab = 'favorites' | 'discover'

export default function Home({
  profile,
  theme,
  onThemeToggle,
  onLogout,
  onSearch,
  onRecipeClick,
  onFavoritesClick,
  onCollectionsClick,
}: HomeProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<Tab>('favorites')
  const [favorites, setFavorites] = useState<Favorite[]>([])
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [favoritesData, historyData] = await Promise.all([
        api.favorites.list(),
        api.history.list(6),
      ])
      setFavorites(favoritesData)
      setHistory(historyData)
    } catch (error) {
      console.error('Failed to load data:', error)
      toast.error('Failed to load recipes')
    } finally {
      setLoading(false)
    }
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      onSearch(searchQuery.trim())
    }
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

  const getInitial = (name: string) => {
    return name.charAt(0).toUpperCase()
  }

  const favoriteRecipeIds = new Set(favorites.map((f) => f.recipe.id))

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border px-4 py-3">
        <h1 className="text-xl font-medium text-primary">Cookie</h1>

        <div className="flex items-center gap-3">
          {/* Favorites */}
          <button
            onClick={onFavoritesClick}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-accent"
            aria-label="View favorites"
          >
            <Heart className="h-5 w-5" />
          </button>

          {/* Collections */}
          <button
            onClick={onCollectionsClick}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
            aria-label="View collections"
          >
            <FolderOpen className="h-5 w-5" />
          </button>

          {/* Theme toggle */}
          <button
            onClick={onThemeToggle}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
          >
            {theme === 'light' ? (
              <Moon className="h-5 w-5" />
            ) : (
              <Sun className="h-5 w-5" />
            )}
          </button>

          {/* Profile avatar */}
          <div
            className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-medium text-white"
            style={{ backgroundColor: profile.avatar_color }}
          >
            {getInitial(profile.name)}
          </div>

          {/* Logout */}
          <button
            onClick={onLogout}
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

          {/* Tab toggle */}
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
                onClick={() => setActiveTab('discover')}
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

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <span className="text-muted-foreground">Loading...</span>
            </div>
          ) : activeTab === 'favorites' ? (
            <>
              {/* Recently Viewed */}
              {history.length > 0 && (
                <section className="mb-8">
                  <h2 className="mb-4 text-lg font-medium text-foreground">
                    Recently Viewed
                  </h2>
                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
                    {history.map((item) => (
                      <RecipeCard
                        key={item.recipe.id}
                        recipe={item.recipe}
                        isFavorite={favoriteRecipeIds.has(item.recipe.id)}
                        onClick={() => onRecipeClick(item.recipe.id)}
                      />
                    ))}
                  </div>
                </section>
              )}

              {/* Favorites */}
              <section>
                <h2 className="mb-4 text-lg font-medium text-foreground">
                  My Favorite Recipes
                </h2>
                {favorites.length > 0 ? (
                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
                    {favorites.map((favorite) => (
                      <RecipeCard
                        key={favorite.recipe.id}
                        recipe={favorite.recipe}
                        isFavorite
                        onFavoriteToggle={handleRemoveFavorite}
                        onClick={() => onRecipeClick(favorite.recipe.id)}
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
            /* Discover tab - placeholder for AI recommendations */
            <div className="flex flex-col items-center justify-center py-12">
              <div className="mb-4 rounded-full bg-muted p-4">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-foreground">
                AI Recommendations Coming Soon
              </h3>
              <p className="text-center text-muted-foreground">
                Personalized recipe suggestions will appear here
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
