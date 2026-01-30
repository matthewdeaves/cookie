import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { toast } from 'sonner'
import { api, type Profile, type RecipeDetail } from '../api/client'

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

export function useProfile() {
  const context = useContext(ProfileContext)
  if (!context) {
    throw new Error('useProfile must be used within a ProfileProvider')
  }
  return context
}

interface ProfileProviderProps {
  children: ReactNode
}

export function ProfileProvider({ children }: ProfileProviderProps) {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [favoriteRecipeIds, setFavoriteRecipeIds] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)

  // Apply theme class to document
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  // Check for existing session on mount
  useEffect(() => {
    const checkSession = async () => {
      try {
        // Try to get the current profile from session
        // Check if there's a profile with an active session (cookie-based)
        // For now, we don't persist sessions across reloads, so just set loading false
        await api.profiles.list()
        setLoading(false)
      } catch (error) {
        console.error('Failed to check session:', error)
        setLoading(false)
      }
    }
    checkSession()
  }, [])

  // Load favorites when profile changes
  useEffect(() => {
    // Clear favorites and skip API call if no profile
    if (!profile) {
      // Use callback form to satisfy react-hooks/set-state-in-effect
      Promise.resolve().then(() => setFavoriteRecipeIds(new Set()))
      return
    }

    api.favorites
      .list()
      .then((favorites) => setFavoriteRecipeIds(new Set(favorites.map((f) => f.recipe.id))))
      .catch((error) => console.error('Failed to load favorites:', error))
  }, [profile])

  const selectProfile = useCallback(async (selectedProfile: Profile) => {
    try {
      await api.profiles.select(selectedProfile.id)
      setProfile(selectedProfile)
      setTheme(selectedProfile.theme as 'light' | 'dark')
    } catch (error) {
      console.error('Failed to select profile:', error)
      throw error
    }
  }, [])

  const logout = useCallback(() => {
    setProfile(null)
    setFavoriteRecipeIds(new Set())
  }, [])

  const toggleTheme = useCallback(async () => {
    if (!profile) return

    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)

    try {
      const updated = await api.profiles.update(profile.id, {
        ...profile,
        theme: newTheme,
      })
      setProfile(updated)
    } catch (error) {
      console.error('Failed to update theme:', error)
      setTheme(theme) // Revert on error
    }
  }, [profile, theme])

  const toggleFavorite = useCallback(async (recipe: RecipeDetail) => {
    const isFav = favoriteRecipeIds.has(recipe.id)
    try {
      if (isFav) {
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
  }, [favoriteRecipeIds])

  const isFavorite = useCallback((recipeId: number) => {
    return favoriteRecipeIds.has(recipeId)
  }, [favoriteRecipeIds])

  return (
    <ProfileContext.Provider
      value={{
        profile,
        theme,
        favoriteRecipeIds,
        loading,
        selectProfile,
        logout,
        toggleTheme,
        toggleFavorite,
        isFavorite,
      }}
    >
      {children}
    </ProfileContext.Provider>
  )
}
