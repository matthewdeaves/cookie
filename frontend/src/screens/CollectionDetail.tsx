import { useNavigate, useParams } from 'react-router-dom'
import { Trash2, X, FolderOpen } from 'lucide-react'
import { type CollectionDetail as CollectionDetailType, type Recipe } from '../api/client'
import { useCollectionData } from '../hooks/useCollectionData'
import NavHeader from '../components/NavHeader'
import RecipeCard from '../components/RecipeCard'
import DeleteConfirmBanner from '../components/DeleteConfirmBanner'
import { LoadingSpinner } from '../components/Skeletons'

export default function CollectionDetail() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const collectionId = Number(id)

  const {
    collection,
    loading,
    showDeleteConfirm,
    setShowDeleteConfirm,
    deleting,
    handleRemoveRecipe,
    handleDeleteCollection,
    handleRecipeClick,
  } = useCollectionData(collectionId)

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <LoadingSpinner className="min-h-screen" />
      </div>
    )
  }

  if (!collection) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background">
        <span className="mb-4 text-muted-foreground">Collection not found</span>
        <button onClick={() => navigate('/collections')} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">
          Go Back
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <NavHeader />
      <main className="px-4 py-6">
        <div className="mx-auto max-w-4xl">
          <CollectionHeader name={collection.name} recipeCount={collection.recipes.length} onDelete={() => setShowDeleteConfirm(true)} />
          {showDeleteConfirm && (
            <DeleteConfirmBanner itemName={collection.name} deleting={deleting} onConfirm={handleDeleteCollection} onCancel={() => setShowDeleteConfirm(false)} />
          )}
          {collection.recipes.length > 0 ? (
            <CollectionRecipeGrid recipes={collection.recipes} onRecipeClick={handleRecipeClick} onRemoveRecipe={handleRemoveRecipe} />
          ) : (
            <EmptyCollection />
          )}
        </div>
      </main>
    </div>
  )
}

function CollectionHeader({ name, recipeCount, onDelete }: { name: string; recipeCount: number; onDelete: () => void }) {
  return (
    <div className="mb-4 flex items-center justify-between">
      <div>
        <h2 className="text-lg font-medium text-foreground">{name}</h2>
        <p className="text-sm text-muted-foreground">{recipeCount} recipe{recipeCount !== 1 ? 's' : ''}</p>
      </div>
      <button onClick={onDelete} className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive" title="Delete collection">
        <Trash2 className="h-5 w-5" />
      </button>
    </div>
  )
}

function CollectionRecipeGrid({
  recipes,
  onRecipeClick,
  onRemoveRecipe,
}: {
  recipes: CollectionDetailType['recipes']
  onRecipeClick: (id: number) => void
  onRemoveRecipe: (recipe: Recipe) => void
}) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
      {recipes.map((item) => (
        <div key={item.recipe.id} className="group relative">
          <RecipeCard recipe={item.recipe} onClick={() => onRecipeClick(item.recipe.id)} />
          <button
            onClick={(e) => { e.stopPropagation(); onRemoveRecipe(item.recipe) }}
            className="absolute right-2 top-2 rounded-full bg-destructive/90 p-1.5 text-destructive-foreground opacity-0 transition-opacity group-hover:opacity-100"
            title="Remove from collection"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  )
}

function EmptyCollection() {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border py-12">
      <div className="mb-4 rounded-full bg-muted p-4">
        <FolderOpen className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="mb-2 text-lg font-medium text-foreground">This collection is empty</h3>
      <p className="text-center text-muted-foreground">Add recipes from their detail pages.</p>
    </div>
  )
}
