import { createContext, useContext, useCallback, ReactNode } from 'react'
import { api, type Profile, type RecipeDetail } from '../api/client'
import { useStoredProfile, saveProfileId, clearProfileId } from '../hooks/useStoredProfile'
import { useFavorites } from '../hooks/useFavorites'

interface ProfileContextType {
  profile: Profile | null
  theme: 'light' | 'dark'
  favoriteRecipeIds: Set<number>
  loading: boolean
  selectProfile: (profile: Profile) => Promise<void>
  logout: () => void
  toggleTheme: () => Promise<void>
  toggleFavorite: (recipe: RecipeDetail) => Promise<void>
  isFavorite: (recipeId: number) => boolean
}

const ProfileContext = createContext<ProfileContextType | null>(null)

// eslint-disable-next-line react-refresh/only-export-components -- Hook is tightly coupled to provider
export function useProfile() {
  const context = useContext(ProfileContext)
  if (!context) {
    throw new Error('useProfile must be used within a ProfileProvider')
  }
  return context
}

interface AuthProfile {
  id: number
  name: string
  avatar_color: string
  theme: string
  unit_preference: string
}

interface ProfileProviderProps {
  children: ReactNode
  authProfile?: AuthProfile | null
  onProfileSelected?: () => void
}

export function ProfileProvider({ children, authProfile, onProfileSelected }: ProfileProviderProps) {
  const { profile, setProfile, theme, setTheme, loading } = useStoredProfile(authProfile)
  const { favoriteRecipeIds, toggleFavorite, isFavorite, clearFavorites } = useFavorites(profile)

  const selectProfile = useCallback(async (selectedProfile: Profile) => {
    try {
      await api.profiles.select(selectedProfile.id)
      setProfile(selectedProfile)
      setTheme(selectedProfile.theme as 'light' | 'dark')
      saveProfileId(selectedProfile.id)
      // Re-check AI availability now that a session exists.  On first visit
      // after import the initial /api/ai/status call returns 401 (no session
      // yet); this ensures AI features are shown once the profile is active.
      onProfileSelected?.()
    } catch (error) {
      console.error('Failed to select profile:', error)
      throw error
    }
  }, [setProfile, setTheme, onProfileSelected])

  const logout = useCallback(() => {
    setProfile(null)
    clearFavorites()
    clearProfileId()
  }, [setProfile, clearFavorites])

  const toggleTheme = useCallback(async () => {
    if (!profile) return
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    try {
      // updatePreferences works in both home + passkey modes. The old PUT
      // /profiles/{id}/ returns 404 in passkey mode (HomeOnlyAuth), which
      // caused the toggle to flip dark → immediately flip back to light
      // when the caught error triggered the rollback below.
      const updated = await api.profiles.updatePreferences(profile.id, { theme: newTheme })
      setProfile(updated)
    } catch (error) {
      console.error('Failed to update theme:', error)
      setTheme(theme)
    }
  }, [profile, theme, setProfile, setTheme])

  return (
    <ProfileContext.Provider
      value={{
        profile, theme, favoriteRecipeIds, loading,
        selectProfile, logout, toggleTheme,
        toggleFavorite, isFavorite,
      }}
    >
      {children}
    </ProfileContext.Provider>
  )
}
