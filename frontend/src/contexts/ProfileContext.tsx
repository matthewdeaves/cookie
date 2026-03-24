import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { toast } from 'sonner'
import { api, type Profile, type RecipeDetail } from '../api/client'

const PROFILE_STORAGE_KEY = 'cookie_selected_profile_id'

function saveProfileId(id: number) {
  localStorage.setItem(PROFILE_STORAGE_KEY, String(id))
  document.cookie = `selected_profile_id=${id};path=/;SameSite=Lax`
}

function clearProfileId() {
  localStorage.removeItem(PROFILE_STORAGE_KEY)
  document.cookie = 'selected_profile_id=;path=/;expires=Thu, 01 Jan 1970 00:00:00 GMT'
}

function getStoredProfileId(): number | null {
  const stored = localStorage.getItem(PROFILE_STORAGE_KEY)
  if (!stored) return null
  const id = parseInt(stored, 10)
  return isNaN(id) ? null : id
}

interface ProfileContextType {
  profile: Profile | null
  theme: 'light' | 'dark'
  favoriteRecipeIds: Set<number>
  loading: boolean
  selectProfile: (profile: Profile) => Promise<void>
  logout: () => void
  toggleTheme: () => Promise<void>
  updateUnitPreference: (unit: 'metric' | 'imperial') => Promise<void>
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
}

export function ProfileProvider({ children, authProfile }: ProfileProviderProps) {
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

  // In public mode, profile comes from auth
  useEffect(() => {
    if (authProfile !== undefined) {
      if (authProfile) {
        setProfile(authProfile as Profile)
        setTheme(authProfile.theme as 'light' | 'dark')
      } else {
        setProfile(null)
      }
      setLoading(false)
      return
    }

    // Home mode: restore from localStorage
    const restoreSession = async () => {
      try {
        const storedId = getStoredProfileId()
        if (storedId) {
          try {
            const restored = await api.profiles.select(storedId)
            setProfile(restored)
            setTheme(restored.theme as 'light' | 'dark')
          } catch {
            clearProfileId()
          }
        }
      } catch (error) {
        console.error('Failed to restore session:', error)
      } finally {
        setLoading(false)
      }
    }
    restoreSession()
  }, [authProfile])

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
      saveProfileId(selectedProfile.id)
    } catch (error) {
      console.error('Failed to select profile:', error)
      throw error
    }
  }, [])

  const logout = useCallback(() => {
    setProfile(null)
    setFavoriteRecipeIds(new Set())
    clearProfileId()
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

  const updateUnitPreference = useCallback(async (unit: 'metric' | 'imperial') => {
    if (!profile) return

    const previousUnit = profile.unit_preference
    setProfile({ ...profile, unit_preference: unit })

    try {
      const updated = await api.profiles.update(profile.id, {
        ...profile,
        unit_preference: unit,
      })
      setProfile(updated)
    } catch (error) {
      console.error('Failed to update unit preference:', error)
      setProfile({ ...profile, unit_preference: previousUnit }) // Revert on error
    }
  }, [profile])

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
        updateUnitPreference,
        toggleFavorite,
        isFavorite,
      }}
    >
      {children}
    </ProfileContext.Provider>
  )
}
