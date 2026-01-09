import { useState, useEffect } from 'react'
import { ArrowLeft, BookOpen } from 'lucide-react'
import { toast } from 'sonner'
import { api, type HistoryItem } from '../api/client'
import RecipeCard from '../components/RecipeCard'
import { RecipeGridSkeleton } from '../components/Skeletons'

interface AllRecipesProps {
  onBack: () => void
  onRecipeClick: (recipeId: number) => void
}

export default function AllRecipes({ onBack, onRecipeClick }: AllRecipesProps) {
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    try {
      // Load all history (use large limit)
      const data = await api.history.list(1000)
      setHistory(data)
    } catch (error) {
      console.error('Failed to load recipes:', error)
      toast.error('Failed to load recipes')
    } finally {
      setLoading(false)
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
        <h1 className="text-xl font-medium text-foreground">All Recipes</h1>
      </header>

      {/* Content */}
      <main className="px-4 py-6">
        <div className="mx-auto max-w-4xl">
          {loading ? (
            <RecipeGridSkeleton count={8} />
          ) : history.length > 0 ? (
            <>
              <p className="mb-4 text-sm text-muted-foreground">
                {history.length} recipe{history.length !== 1 ? 's' : ''}
              </p>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
                {history.map((item) => (
                  <RecipeCard
                    key={item.recipe.id}
                    recipe={item.recipe}
                    onClick={() => onRecipeClick(item.recipe.id)}
                  />
                ))}
              </div>
            </>
          ) : (
            /* Empty state */
            <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border py-12">
              <div className="mb-4 rounded-full bg-muted p-4">
                <BookOpen className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-foreground">
                No recipes viewed yet
              </h3>
              <p className="mb-4 text-center text-muted-foreground">
                Start browsing and viewing recipes to see them here
              </p>
              <button
                onClick={onBack}
                className="rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
              >
                Browse Recipes
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
