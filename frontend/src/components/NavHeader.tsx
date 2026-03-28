import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Moon, Sun, Home, Heart, BookOpen, FolderOpen, Settings, LogOut, Users, User } from 'lucide-react'
import { useProfile } from '../contexts/ProfileContext'
import { useMode } from '../router'

export default function NavHeader() {
  const navigate = useNavigate()
  const mode = useMode()
  const { profile, theme, toggleTheme, logout } = useProfile()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const getInitial = (name: string) => {
    return name.charAt(0).toUpperCase()
  }

  // Close dropdown on outside click
  useEffect(() => {
    if (!dropdownOpen) return
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [dropdownOpen])

  if (!profile) return null

  return (
    <header className="flex items-center justify-between border-b border-border px-4 py-3">
      <button
        onClick={() => navigate('/home')}
        className="text-xl font-medium text-primary hover:opacity-80 transition-opacity"
      >
        Cookie
      </button>

      <div className="flex items-center gap-1">
        {/* Home */}
        <button
          onClick={() => navigate('/home')}
          className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
          aria-label="Home"
        >
          <Home className="h-5 w-5" />
        </button>

        {/* All Recipes */}
        <button
          onClick={() => navigate('/all-recipes')}
          className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
          aria-label="All recipes"
        >
          <BookOpen className="h-5 w-5" />
        </button>

        {/* Favorites */}
        <button
          onClick={() => navigate('/favorites')}
          className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-accent"
          aria-label="View favorites"
        >
          <Heart className="h-5 w-5" />
        </button>

        {/* Collections */}
        <button
          onClick={() => navigate('/collections')}
          className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
          aria-label="View collections"
        >
          <FolderOpen className="h-5 w-5" />
        </button>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
        >
          {theme === 'light' ? (
            <Moon className="h-5 w-5" />
          ) : (
            <Sun className="h-5 w-5" />
          )}
        </button>

        {/* Settings */}
        <button
          onClick={() => navigate('/settings')}
          className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          aria-label="Settings"
        >
          <Settings className="h-5 w-5" />
        </button>

        {/* Profile avatar with dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium text-white"
            style={{ backgroundColor: profile.avatar_color }}
            aria-label={profile.name}
          >
            {mode === 'passkey' ? (
              <User className="h-4 w-4" />
            ) : (
              getInitial(profile.name)
            )}
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 top-full z-50 mt-1 w-44 rounded-lg border border-border bg-card py-1 shadow-lg">
              <button
                onClick={() => { setDropdownOpen(false); handleLogout() }}
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-card-foreground hover:bg-muted"
              >
                <Users className="h-4 w-4" />
                Switch profile
              </button>
              <button
                onClick={() => { setDropdownOpen(false); handleLogout() }}
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-card-foreground hover:bg-muted"
              >
                <LogOut className="h-4 w-4" />
                Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
