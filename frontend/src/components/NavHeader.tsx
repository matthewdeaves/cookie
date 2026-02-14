import { useNavigate } from 'react-router-dom'
import { Moon, Sun, Home, Heart, FolderOpen, Settings, LogOut } from 'lucide-react'
import { useProfile } from '../contexts/ProfileContext'

export default function NavHeader() {
  const navigate = useNavigate()
  const { profile, theme, toggleTheme, logout } = useProfile()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const getInitial = (name: string) => {
    return name.charAt(0).toUpperCase()
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

      <div className="flex items-center gap-3">
        {/* Home */}
        <button
          onClick={() => navigate('/home')}
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
          aria-label="Home"
        >
          <Home className="h-5 w-5" />
        </button>

        {/* Favorites */}
        <button
          onClick={() => navigate('/favorites')}
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-accent"
          aria-label="View favorites"
        >
          <Heart className="h-5 w-5" />
        </button>

        {/* Collections */}
        <button
          onClick={() => navigate('/collections')}
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
          aria-label="View collections"
        >
          <FolderOpen className="h-5 w-5" />
        </button>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
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
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          aria-label="Settings"
        >
          <Settings className="h-5 w-5" />
        </button>

        {/* Profile avatar */}
        <button
          onClick={handleLogout}
          className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-medium text-white"
          style={{ backgroundColor: profile.avatar_color }}
          aria-label="Switch profile"
        >
          {getInitial(profile.name)}
        </button>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          aria-label="Switch profile"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </header>
  )
}
