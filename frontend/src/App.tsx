import { useState, useEffect } from 'react'
import { Toaster, toast } from 'sonner'
import ProfileSelector from './screens/ProfileSelector'
import Home from './screens/Home'
import Search from './screens/Search'
import RecipeDetail from './screens/RecipeDetail'
import { api, type Profile, type RecipeDetail as RecipeDetailType } from './api/client'

type Screen = 'profile-selector' | 'home' | 'search' | 'recipe-detail'

function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('profile-selector')
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedRecipeId, setSelectedRecipeId] = useState<number | null>(null)
  const [favoriteRecipeIds, setFavoriteRecipeIds] = useState<Set<number>>(new Set())

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

  // Load favorites when profile is set
  useEffect(() => {
    if (currentProfile) {
      loadFavorites()
    } else {
      setFavoriteRecipeIds(new Set())
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
      // Navigate to recipe detail
      setSelectedRecipeId(recipe.id)
      setCurrentScreen('recipe-detail')
      setSearchQuery('')
    } catch (error) {
      console.error('Failed to import recipe:', error)
      toast.error('Failed to import recipe. Please check the URL.')
      throw error
    }
  }

  const handleRecipeClick = async (recipeId: number) => {
    try {
      await api.history.record(recipeId)
    } catch (error) {
      console.error('Failed to record history:', error)
    }
    setSelectedRecipeId(recipeId)
    setCurrentScreen('recipe-detail')
  }

  const handleRecipeDetailBack = () => {
    setSelectedRecipeId(null)
    // Go back to previous screen (could be home or search)
    setCurrentScreen(searchQuery ? 'search' : 'home')
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

  const handleStartCooking = (_recipe: RecipeDetailType) => {
    // TODO: Navigate to play mode in Phase 6 Session B
    toast.info('Play mode coming in Phase 6 Session B')
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
          onThemeToggle={handleThemeToggle}
          onLogout={handleLogout}
          onSearch={handleSearch}
          onRecipeClick={handleRecipeClick}
        />
      )}
      {currentScreen === 'search' && (
        <Search
          query={searchQuery}
          onBack={handleSearchBack}
          onImport={handleImport}
        />
      )}
      {currentScreen === 'recipe-detail' && selectedRecipeId && (
        <RecipeDetail
          recipeId={selectedRecipeId}
          isFavorite={favoriteRecipeIds.has(selectedRecipeId)}
          onBack={handleRecipeDetailBack}
          onFavoriteToggle={handleFavoriteToggle}
          onStartCooking={handleStartCooking}
        />
      )}
    </>
  )
}

export default App
