import { useState, useEffect } from 'react'
import { Toaster, toast } from 'sonner'
import ProfileSelector from './screens/ProfileSelector'
import Home from './screens/Home'
import Search from './screens/Search'
import { api, type Profile } from './api/client'

type Screen = 'profile-selector' | 'home' | 'search'

function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('profile-selector')
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [searchQuery, setSearchQuery] = useState('')

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
      setCurrentScreen('home')
      setSearchQuery('')
    } catch (error) {
      console.error('Failed to import recipe:', error)
      toast.error('Failed to import recipe. Please check the URL.')
      throw error
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
          onThemeToggle={handleThemeToggle}
          onLogout={handleLogout}
          onSearch={handleSearch}
        />
      )}
      {currentScreen === 'search' && (
        <Search
          query={searchQuery}
          onBack={handleSearchBack}
          onImport={handleImport}
        />
      )}
    </>
  )
}

export default App
