import { useState, useEffect } from 'react'
import { Toaster } from 'sonner'
import ProfileSelector from './screens/ProfileSelector'
import Home from './screens/Home'
import { api, type Profile } from './api/client'

type Screen = 'profile-selector' | 'home'

function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('profile-selector')
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

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
    // Search screen will be implemented in Session C
    console.log('Search:', query)
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
    </>
  )
}

export default App
