import NavHeader from '../components/NavHeader'
import RemixModal from '../components/RemixModal'
import { RecipeDetailSkeleton } from '../components/Skeletons'
import { useRecipeDetail } from '../hooks/useRecipeDetail'
import RecipeHeader from './components/RecipeHeader'
import RecipeActions from './components/RecipeActions'
import RecipeTabs from './components/RecipeTabs'

export default function RecipeDetail() {
  const {
    recipe,
    loading,
    activeTab,
    setActiveTab,
    metaExpanded,
    setMetaExpanded,
    servings,
    showRemixModal,
    setShowRemixModal,
    scaledData,
    scalingLoading,
    tips,
    tipsLoading,
    tipsPolling,
    profile,
    recipeId,
    canShowServingAdjustment,
    recipeIsFavorite,
    imageUrl,
    tipsAvailable,
    remixAvailable,
    handleServingChange,
    handleGenerateTips,
    handleFavoriteToggle,
    handleStartCooking,
    handleAddToNewCollection,
    handleRemixCreated,
    handleBack,
  } = useRecipeDetail()

  if (loading) {
    return <RecipeDetailSkeleton />
  }

  if (!recipe || !profile) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background">
        <span className="mb-4 text-muted-foreground">Recipe not found</span>
        <button
          onClick={handleBack}
          className="rounded-lg bg-primary px-4 py-2 text-primary-foreground"
        >
          Go Back
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <NavHeader />

      <RecipeHeader
        recipe={recipe}
        imageUrl={imageUrl}
        metaExpanded={metaExpanded}
        setMetaExpanded={setMetaExpanded}
        canShowServingAdjustment={canShowServingAdjustment}
        servings={servings}
        scaledData={scaledData}
        scalingLoading={scalingLoading}
        onServingChange={handleServingChange}
      >
        <RecipeActions
          recipeId={recipeId}
          recipeIsFavorite={recipeIsFavorite}
          aiAvailable={remixAvailable}
          onFavoriteToggle={handleFavoriteToggle}
          onAddToNewCollection={handleAddToNewCollection}
          onShowRemixModal={() => setShowRemixModal(true)}
          onStartCooking={handleStartCooking}
        />
      </RecipeHeader>

      <RecipeTabs
        recipe={recipe}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        scaledData={scaledData}
        tips={tips}
        tipsLoading={tipsLoading}
        tipsPolling={tipsPolling}
        aiAvailable={tipsAvailable}
        onGenerateTips={handleGenerateTips}
      />

      <RemixModal
        recipe={recipe}
        profileId={profile.id}
        isOpen={showRemixModal}
        onClose={() => setShowRemixModal(false)}
        onRemixCreated={handleRemixCreated}
      />
    </div>
  )
}
