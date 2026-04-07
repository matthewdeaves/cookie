import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { BookOpen, Search } from 'lucide-react'
import { toast } from 'sonner'
import { api, type Recipe } from '../api/client'
import NavHeader from '../components/NavHeader'
import RecipeCard from '../components/RecipeCard'
import RecipeSearchFilter from '../components/RecipeSearchFilter'
import { RecipeGridSkeleton } from '../components/Skeletons'

export default function AllRecipes() {
  const navigate = useNavigate()
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await api.recipes.list(1000)
        if (!cancelled) setRecipes(data)
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load recipes:', error)
          toast.error('Failed to load recipes')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [])

  const handleRecipeClick = async (recipeId: number) => {
    try {
      await api.history.record(recipeId)
    } catch (error) {
      console.error('Failed to record history:', error)
    }
    navigate(`/recipe/${recipeId}`)
  }

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
      <main className="px-4 py-6">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-4 text-lg font-medium text-foreground">My Recipes</h2>
          {loading ? (
            <RecipeGridSkeleton count={8} />
          ) : recipes.length > 0 ? (
            <RecipeList
              recipes={recipes}
              filteredRecipes={filteredRecipes}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              onRecipeClick={handleRecipeClick}
            />
          ) : (
            <EmptyRecipes onImport={() => navigate('/home')} />
          )}
        </div>
      </main>
    </div>
  )
}

function RecipeList({
  recipes,
  filteredRecipes,
  searchQuery,
  onSearchChange,
  onRecipeClick,
}: {
  recipes: Recipe[]
  filteredRecipes: Recipe[]
  searchQuery: string
  onSearchChange: (q: string) => void
  onRecipeClick: (id: number) => void
}) {
  return (
    <>
      <RecipeSearchFilter
        searchQuery={searchQuery}
        onSearchChange={onSearchChange}
        totalCount={recipes.length}
        filteredCount={filteredRecipes.length}
      />
      {filteredRecipes.length > 0 ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
          {filteredRecipes.map((recipe) => (
            <RecipeCard
              key={recipe.id}
              recipe={recipe}
              onClick={() => onRecipeClick(recipe.id)}
            />
          ))}
        </div>
      ) : (
        <div className="py-8 text-center text-muted-foreground">
          No recipes match "{searchQuery}"
        </div>
      )}
    </>
  )
}

function EmptyRecipes({ onImport }: { onImport: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border py-12">
      <div className="mb-4 rounded-full bg-muted p-4">
        <BookOpen className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="mb-2 text-lg font-medium text-foreground">No recipes yet</h3>
      <p className="mb-4 text-center text-muted-foreground">
        Import recipes from the web to see them here
      </p>
      <button
        onClick={onImport}
        className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
      >
        <Search className="h-4 w-4" />
        Import Recipes
      </button>
    </div>
  )
}
