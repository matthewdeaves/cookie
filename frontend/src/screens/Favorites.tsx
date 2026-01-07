import { useState, useEffect } from 'react'
import { ArrowLeft, Heart } from 'lucide-react'
import { toast } from 'sonner'
import { api, type Recipe, type Favorite } from '../api/client'
import RecipeCard from '../components/RecipeCard'

interface FavoritesProps {
  onBack: () => void
  onRecipeClick: (recipeId: number) => void
}

export default function Favorites({ onBack, onRecipeClick }: FavoritesProps) {
  const [favorites, setFavorites] = useState<Favorite[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadFavorites()
  }, [])

  const loadFavorites = async () => {
    try {
      const data = await api.favorites.list()
      setFavorites(data)
    } catch (error) {
      console.error('Failed to load favorites:', error)
      toast.error('Failed to load favorites')
    } finally {
      setLoading(false)
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

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="flex items-center gap-4 border-b border-border px-4 py-3">
        <button
          onClick={onBack}
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="text-xl font-medium text-foreground">Favorites</h1>
      </header>

      {/* Content */}
      <main className="px-4 py-6">
        <div className="mx-auto max-w-4xl">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <span className="text-muted-foreground">Loading...</span>
            </div>
          ) : favorites.length > 0 ? (
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
                <Heart className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-foreground">
                No favorites yet
              </h3>
              <p className="mb-4 text-center text-muted-foreground">
                Browse recipes to add some!
              </p>
              <button
                onClick={onBack}
                className="rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
              >
                Discover Recipes
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
