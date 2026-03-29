import { useState, useEffect, type Dispatch, type SetStateAction } from 'react'
import { api, type Profile } from '../api/client'

const PROFILE_STORAGE_KEY = 'cookie_selected_profile_id'

export function saveProfileId(id: number) {
  localStorage.setItem(PROFILE_STORAGE_KEY, String(id))
  document.cookie = `selected_profile_id=${id};path=/;SameSite=Lax`
}

export function clearProfileId() {
  localStorage.removeItem(PROFILE_STORAGE_KEY)
  document.cookie = 'selected_profile_id=;path=/;expires=Thu, 01 Jan 1970 00:00:00 GMT'
}

function getStoredProfileId(): number | null {
  const stored = localStorage.getItem(PROFILE_STORAGE_KEY)
  if (!stored) return null
  const id = parseInt(stored, 10)
  return isNaN(id) ? null : id
}

interface AuthProfile {
  id: number
  name: string
  avatar_color: string
  theme: string
  unit_preference: string
}

interface UseStoredProfileReturn {
  profile: Profile | null
  setProfile: Dispatch<SetStateAction<Profile | null>>
  theme: 'light' | 'dark'
  setTheme: Dispatch<SetStateAction<'light' | 'dark'>>
  loading: boolean
}

/**
 * Manages profile restoration from localStorage (home mode) or auth (passkey mode).
 * Applies the theme class to the document element.
 */
export function useStoredProfile(authProfile?: AuthProfile | null): UseStoredProfileReturn {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [loading, setLoading] = useState(true)

  // Apply theme class to document
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  // Restore profile from auth or localStorage
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

  return { profile, setProfile, theme, setTheme, loading }
}
