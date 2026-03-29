import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import type { Recipe, Favorite, HistoryItem } from '../api/client'
import RecipeCard from '../components/RecipeCard'

interface FavoritesTabProps {
  history: HistoryItem[]
  favorites: Favorite[]
  recipesCount: number
  favoriteIds: Set<number>
  onRecipeClick: (recipeId: number) => void
  onFavoriteToggle: (recipe: Recipe) => void
}

export default function FavoritesTab({
  history,
  favorites,
  recipesCount,
  favoriteIds,
  onRecipeClick,
  onFavoriteToggle,
}: FavoritesTabProps) {
  const navigate = useNavigate()

  return (
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
              My Recipes ({recipesCount})
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {history.map((item) => (
              <RecipeCard
                key={item.recipe.id}
                recipe={item.recipe}
                isFavorite={favoriteIds.has(item.recipe.id)}
                onFavoriteToggle={onFavoriteToggle}
                onClick={() => onRecipeClick(item.recipe.id)}
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
                onFavoriteToggle={onFavoriteToggle}
                onClick={() => onRecipeClick(favorite.recipe.id)}
              />
            ))}
          </div>
        ) : (
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
  )
}
