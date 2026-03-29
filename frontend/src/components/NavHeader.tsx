import { useNavigate } from 'react-router-dom'
import { Moon, Sun, Home, Heart, BookOpen, FolderOpen, Settings } from 'lucide-react'
import { useProfile } from '../contexts/ProfileContext'
import { useMode } from '../router'
import ProfileDropdown from './ProfileDropdown'

export default function NavHeader() {
  const navigate = useNavigate()
  const mode = useMode()
  const { profile, theme, toggleTheme, logout } = useProfile()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

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
        <ProfileDropdown
          profileName={profile.name}
          avatarColor={profile.avatar_color}
          mode={mode}
          onSwitchProfile={handleLogout}
          onLogout={handleLogout}
        />
      </div>
    </header>
  )
}
