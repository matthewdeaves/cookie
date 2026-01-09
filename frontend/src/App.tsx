import { useState, useEffect } from 'react'
import { Toaster, toast } from 'sonner'
import ProfileSelector from './screens/ProfileSelector'
import Home from './screens/Home'
import Search from './screens/Search'
import RecipeDetail from './screens/RecipeDetail'
import PlayMode from './screens/PlayMode'
import Favorites from './screens/Favorites'
import AllRecipes from './screens/AllRecipes'
import Collections from './screens/Collections'
import CollectionDetail from './screens/CollectionDetail'
import Settings from './screens/Settings'
import { api, type Profile, type RecipeDetail as RecipeDetailType, type Settings as SettingsType } from './api/client'

type Screen =
  | 'profile-selector'
  | 'home'
  | 'search'
  | 'recipe-detail'
  | 'play-mode'
  | 'favorites'
  | 'all-recipes'
  | 'collections'
  | 'collection-detail'
  | 'settings'

function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('profile-selector')
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedRecipeId, setSelectedRecipeId] = useState<number | null>(null)
  const [playModeRecipe, setPlayModeRecipe] = useState<RecipeDetailType | null>(null)
  const [favoriteRecipeIds, setFavoriteRecipeIds] = useState<Set<number>>(new Set())
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null)
  const [pendingRecipeForCollection, setPendingRecipeForCollection] = useState<number | null>(null)
  const [previousScreen, setPreviousScreen] = useState<Screen>('home')
  const [settings, setSettings] = useState<SettingsType | null>(null)

  // Apply theme class to document
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  // Update theme when profile changes
  useEffect(() => {
    if (currentProfile) {
      setTheme(currentProfile.theme as 'light' | 'dark')
    }
  }, [currentProfile])

  // Load favorites and settings when profile is set
  useEffect(() => {
    if (currentProfile) {
      loadFavorites()
      loadSettings()
    } else {
      setFavoriteRecipeIds(new Set())
      setSettings(null)
    }
  }, [currentProfile])

  const loadFavorites = async () => {
    try {
      const favorites = await api.favorites.list()
      setFavoriteRecipeIds(new Set(favorites.map((f) => f.recipe.id)))
    } catch (error) {
      console.error('Failed to load favorites:', error)
    }
  }

  const loadSettings = async () => {
    try {
      const settingsData = await api.settings.get()
      setSettings(settingsData)
    } catch (error) {
      console.error('Failed to load settings:', error)
    }
  }

  const handleProfileSelect = async (profile: Profile) => {
    try {
      await api.profiles.select(profile.id)
      setCurrentProfile(profile)
      setCurrentScreen('home')
    } catch (error) {
      console.error('Failed to select profile:', error)
    }
  }

  const handleThemeToggle = async () => {
    if (!currentProfile) return

    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)

    try {
      const updated = await api.profiles.update(currentProfile.id, {
        ...currentProfile,
        theme: newTheme,
      })
      setCurrentProfile(updated)
    } catch (error) {
      console.error('Failed to update theme:', error)
      setTheme(theme) // Revert on error
    }
  }

  const handleLogout = () => {
    setCurrentProfile(null)
    setCurrentScreen('profile-selector')
  }

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setCurrentScreen('search')
  }

  const handleSearchBack = () => {
    setCurrentScreen('home')
    setSearchQuery('')
  }

  const handleImport = async (url: string) => {
    try {
      const recipe = await api.recipes.scrape(url)
      toast.success(`Imported: ${recipe.title}`)
      // Record in history
      await api.history.record(recipe.id)
      // Navigate to recipe detail (preserve search context for back navigation)
      setPreviousScreen('search')
      setSelectedRecipeId(recipe.id)
      setCurrentScreen('recipe-detail')
    } catch (error) {
      console.error('Failed to import recipe:', error)
      const message = error instanceof Error ? error.message : 'Failed to import recipe'
      toast.error(message)
      throw error
    }
  }

  const handleRecipeClick = async (recipeId: number) => {
    try {
      await api.history.record(recipeId)
    } catch (error) {
      console.error('Failed to record history:', error)
    }
    setPreviousScreen(currentScreen)
    setSelectedRecipeId(recipeId)
    setCurrentScreen('recipe-detail')
  }

  const handleRecipeDetailBack = () => {
    setSelectedRecipeId(null)
    // Go back to previous screen
    if (previousScreen === 'search' || previousScreen === 'all-recipes' || previousScreen === 'favorites') {
      setCurrentScreen(previousScreen)
    } else {
      setCurrentScreen('home')
    }
  }

  const handleFavoriteToggle = async (recipe: RecipeDetailType) => {
    const isFavorite = favoriteRecipeIds.has(recipe.id)
    try {
      if (isFavorite) {
        await api.favorites.remove(recipe.id)
        setFavoriteRecipeIds((prev) => {
          const next = new Set(prev)
          next.delete(recipe.id)
          return next
        })
        toast.success('Removed from favorites')
      } else {
        await api.favorites.add(recipe.id)
        setFavoriteRecipeIds((prev) => new Set(prev).add(recipe.id))
        toast.success('Added to favorites')
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error)
      toast.error('Failed to update favorites')
    }
  }

  const handleStartCooking = (recipe: RecipeDetailType) => {
    setPlayModeRecipe(recipe)
    setCurrentScreen('play-mode')
  }

  const handleExitPlayMode = () => {
    setPlayModeRecipe(null)
    setCurrentScreen('recipe-detail')
  }

  const handleFavoritesClick = () => {
    setCurrentScreen('favorites')
  }

  const handleFavoritesBack = () => {
    setCurrentScreen('home')
  }

  const handleAllRecipesClick = () => {
    setCurrentScreen('all-recipes')
  }

  const handleAllRecipesBack = () => {
    setCurrentScreen('home')
  }

  const handleCollectionsClick = () => {
    setPreviousScreen(currentScreen)
    setCurrentScreen('collections')
  }

  const handleCollectionsBack = () => {
    setPendingRecipeForCollection(null)
    setCurrentScreen(previousScreen)
  }

  const handleCollectionClick = (collectionId: number) => {
    setSelectedCollectionId(collectionId)
    setPendingRecipeForCollection(null)
    setCurrentScreen('collection-detail')
  }

  const handleCollectionDetailBack = () => {
    setSelectedCollectionId(null)
    setCurrentScreen('collections')
  }

  const handleCollectionDelete = () => {
    setSelectedCollectionId(null)
    setCurrentScreen('collections')
  }

  const handleSettingsClick = () => {
    setCurrentScreen('settings')
  }

  const handleSettingsBack = () => {
    setCurrentScreen('home')
  }

  const handleAddToNewCollection = (recipeId: number) => {
    setPendingRecipeForCollection(recipeId)
    setPreviousScreen('recipe-detail')
    setCurrentScreen('collections')
  }

  const handleRecipeClickFromCollection = async (recipeId: number) => {
    try {
      await api.history.record(recipeId)
    } catch (error) {
      console.error('Failed to record history:', error)
    }
    setSelectedRecipeId(recipeId)
    setCurrentScreen('recipe-detail')
  }

  const handleRecipeDetailBackFromCollection = () => {
    setSelectedRecipeId(null)
    if (selectedCollectionId) {
      setCurrentScreen('collection-detail')
    } else {
      setCurrentScreen(searchQuery ? 'search' : 'home')
    }
  }

  return (
    <>
      <Toaster position="top-center" richColors />
      {currentScreen === 'profile-selector' && (
        <ProfileSelector onProfileSelect={handleProfileSelect} />
      )}
      {currentScreen === 'home' && currentProfile && (
        <Home
          profile={currentProfile}
          theme={theme}
          aiAvailable={settings?.ai_available ?? false}
          onThemeToggle={handleThemeToggle}
          onLogout={handleLogout}
          onSearch={handleSearch}
          onRecipeClick={handleRecipeClick}
          onFavoritesClick={handleFavoritesClick}
          onAllRecipesClick={handleAllRecipesClick}
          onCollectionsClick={handleCollectionsClick}
          onSettingsClick={handleSettingsClick}
        />
      )}
      {currentScreen === 'search' && (
        <Search
          query={searchQuery}
          onBack={handleSearchBack}
          onImport={handleImport}
        />
      )}
      {currentScreen === 'recipe-detail' && selectedRecipeId && currentProfile && (
        <RecipeDetail
          recipeId={selectedRecipeId}
          profileId={currentProfile.id}
          isFavorite={favoriteRecipeIds.has(selectedRecipeId)}
          onBack={selectedCollectionId ? handleRecipeDetailBackFromCollection : handleRecipeDetailBack}
          onFavoriteToggle={handleFavoriteToggle}
          onStartCooking={handleStartCooking}
          onAddToNewCollection={handleAddToNewCollection}
          onRemixCreated={handleRecipeClick}
        />
      )}
      {currentScreen === 'play-mode' && playModeRecipe && (
        <PlayMode recipe={playModeRecipe} onExit={handleExitPlayMode} />
      )}
      {currentScreen === 'favorites' && (
        <Favorites
          onBack={handleFavoritesBack}
          onRecipeClick={handleRecipeClick}
        />
      )}
      {currentScreen === 'all-recipes' && (
        <AllRecipes
          onBack={handleAllRecipesBack}
          onRecipeClick={handleRecipeClick}
        />
      )}
      {currentScreen === 'collections' && (
        <Collections
          onBack={handleCollectionsBack}
          onCollectionClick={handleCollectionClick}
          pendingRecipeId={pendingRecipeForCollection}
        />
      )}
      {currentScreen === 'collection-detail' && selectedCollectionId && (
        <CollectionDetail
          collectionId={selectedCollectionId}
          onBack={handleCollectionDetailBack}
          onRecipeClick={handleRecipeClickFromCollection}
          onDelete={handleCollectionDelete}
        />
      )}
      {currentScreen === 'settings' && (
        <Settings onBack={handleSettingsBack} />
      )}
    </>
  )
}

export default App
