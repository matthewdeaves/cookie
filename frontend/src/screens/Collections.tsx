import { FolderPlus, Plus } from 'lucide-react'
import { useCollectionsPage } from '../hooks/useCollectionsPage'
import NavHeader from '../components/NavHeader'
import CreateCollectionForm from '../components/CreateCollectionForm'
import CollectionCard from '../components/CollectionCard'
import { CollectionGridSkeleton } from '../components/Skeletons'

export default function Collections() {
  const {
    pendingRecipeId,
    collections,
    loading,
    showCreateForm,
    setShowCreateForm,
    newCollectionName,
    setNewCollectionName,
    creating,
    handleCreateCollection,
    handleCollectionClick,
    handleCancelCreate,
  } = useCollectionsPage()

  return (
    <div className="min-h-screen bg-background">
      <NavHeader />
      <main className="px-4 py-6">
        <div className="mx-auto max-w-4xl">
          <CollectionsPageHeader onCreateClick={() => setShowCreateForm(true)} />

          {showCreateForm && (
            <CreateCollectionForm
              name={newCollectionName}
              onNameChange={setNewCollectionName}
              creating={creating}
              onSubmit={handleCreateCollection}
              onCancel={handleCancelCreate}
            />
          )}

          {pendingRecipeId && (
            <div className="mb-4 rounded-lg border border-primary/30 bg-primary/10 p-3 text-sm text-foreground">
              Select a collection or create a new one to add the recipe
            </div>
          )}

          {loading ? (
            <CollectionGridSkeleton count={8} />
          ) : collections.length > 0 ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
              {collections.map((collection) => (
                <CollectionCard
                  key={collection.id}
                  collection={collection}
                  highlighted={!!pendingRecipeId}
                  onClick={() => handleCollectionClick(collection.id)}
                />
              ))}
            </div>
          ) : (
            <EmptyCollections onCreateClick={() => setShowCreateForm(true)} />
          )}
        </div>
      </main>
    </div>
  )
}

function CollectionsPageHeader({ onCreateClick }: { onCreateClick: () => void }) {
  return (
    <div className="mb-4 flex items-center justify-between">
      <h2 className="text-lg font-medium text-foreground">Collections</h2>
      <button
        onClick={onCreateClick}
        className="flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
      >
        <Plus className="h-4 w-4" />
        New
      </button>
    </div>
  )
}

function EmptyCollections({ onCreateClick }: { onCreateClick: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border py-12">
      <div className="mb-4 rounded-full bg-muted p-4">
        <FolderPlus className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="mb-2 text-lg font-medium text-foreground">No collections yet</h3>
      <p className="mb-4 text-center text-muted-foreground">Create one to organize your recipes!</p>
      <button onClick={onCreateClick} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90">
        Create Collection
      </button>
    </div>
  )
}
