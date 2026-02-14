import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { BookOpen, Search, X } from 'lucide-react'
import { toast } from 'sonner'
import { api, type Recipe } from '../api/client'
import NavHeader from '../components/NavHeader'
import RecipeCard from '../components/RecipeCard'
import { RecipeGridSkeleton } from '../components/Skeletons'

export default function AllRecipes() {
  const navigate = useNavigate()
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadRecipes()
  }, [])

  const loadRecipes = async () => {
    try {
      // Load all recipes owned by the profile
      const data = await api.recipes.list(1000)
      setRecipes(data)
    } catch (error) {
      console.error('Failed to load recipes:', error)
      toast.error('Failed to load recipes')
    } finally {
      setLoading(false)
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

  // Filter recipes by search query
  const filteredRecipes = useMemo(() => {
    if (!searchQuery.trim()) return recipes
    const query = searchQuery.toLowerCase()
    return recipes.filter(
      (recipe) =>
        recipe.title.toLowerCase().includes(query) ||
        recipe.host.toLowerCase().includes(query)
    )
  }, [recipes, searchQuery])

  return (
    <div className="min-h-screen bg-background">
      <NavHeader />

      {/* Content */}
      <main className="px-4 py-6">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-4 text-lg font-medium text-foreground">My Recipes</h2>
          {loading ? (
            <RecipeGridSkeleton count={8} />
          ) : recipes.length > 0 ? (
            <>
              {/* Search box */}
              <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter recipes..."
                  className="w-full rounded-lg border border-border bg-input-background py-2 pl-10 pr-10 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>

              <p className="mb-4 text-sm text-muted-foreground">
                {searchQuery
                  ? `${filteredRecipes.length} of ${recipes.length} recipe${recipes.length !== 1 ? 's' : ''}`
                  : `${recipes.length} recipe${recipes.length !== 1 ? 's' : ''}`}
              </p>

              {filteredRecipes.length > 0 ? (
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
                  {filteredRecipes.map((recipe) => (
                    <RecipeCard
                      key={recipe.id}
                      recipe={recipe}
                      onClick={() => handleRecipeClick(recipe.id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  No recipes match "{searchQuery}"
                </div>
              )}
            </>
          ) : (
            /* Empty state */
            <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border py-12">
              <div className="mb-4 rounded-full bg-muted p-4">
                <BookOpen className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-foreground">
                No recipes yet
              </h3>
              <p className="mb-4 text-center text-muted-foreground">
                Import recipes from the web to see them here
              </p>
              <button
                onClick={() => navigate('/home')}
                className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
              >
                <Search className="h-4 w-4" />
                Import Recipes
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
