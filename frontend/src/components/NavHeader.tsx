import { useNavigate, useLocation } from 'react-router-dom'
import { Moon, Sun, Home, Heart, BookOpen, FolderOpen, Settings } from 'lucide-react'
import { useProfile } from '../contexts/ProfileContext'
import { useMode } from '../router'
import ProfileDropdown from './ProfileDropdown'

// 44x44px hit area (Apple HIG minimum) even though the icon is 20px.
const NAV_BASE = 'inline-flex h-11 w-11 items-center justify-center rounded-lg transition-colors'
const NAV_INACTIVE = `${NAV_BASE} text-muted-foreground hover:bg-muted hover:text-primary`
const NAV_ACTIVE = `${NAV_BASE} bg-muted text-primary`

export default function NavHeader() {
  const navigate = useNavigate()
  const location = useLocation()
  const mode = useMode()
  const { profile, theme, toggleTheme, logout } = useProfile()

  const isActive = (path: string) => location.pathname === path
    || (path !== '/home' && location.pathname.startsWith(path))

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  if (!profile) return null

  return (
    <header className="flex items-center justify-between border-b border-border px-3 py-1.5 sm:px-4">
      {/* The wordmark is dropped on phones to make room for 44px tap targets; the Home icon covers it. */}
      <button
        onClick={() => navigate('/home')}
        className="hidden min-h-11 text-xl font-medium text-primary transition-opacity hover:opacity-80 sm:block"
      >
        Cookie
      </button>

      <nav aria-label="Main" className="flex w-full items-center justify-between sm:w-auto sm:justify-end sm:gap-1">
        {/* Home */}
        <button
          onClick={() => navigate('/home')}
          className={isActive('/home') ? NAV_ACTIVE : NAV_INACTIVE}
          aria-label="Home"
          aria-current={isActive('/home') ? 'page' : undefined}
        >
          <Home className="h-5 w-5" />
        </button>

        {/* All Recipes */}
        <button
          onClick={() => navigate('/all-recipes')}
          className={isActive('/all-recipes') ? NAV_ACTIVE : NAV_INACTIVE}
          aria-label="All recipes"
          aria-current={isActive('/all-recipes') ? 'page' : undefined}
        >
          <BookOpen className="h-5 w-5" />
        </button>

        {/* Favorites */}
        <button
          onClick={() => navigate('/favorites')}
          className={isActive('/favorites') ? `${NAV_BASE} bg-muted text-accent` : `${NAV_BASE} text-muted-foreground hover:bg-muted hover:text-accent`}
          aria-label="View favorites"
          aria-current={isActive('/favorites') ? 'page' : undefined}
        >
          <Heart className="h-5 w-5" />
        </button>

        {/* Collections */}
        <button
          onClick={() => navigate('/collections')}
          className={isActive('/collections') || isActive('/collection') ? NAV_ACTIVE : NAV_INACTIVE}
          aria-label="View collections"
          aria-current={isActive('/collections') || isActive('/collection') ? 'page' : undefined}
        >
          <FolderOpen className="h-5 w-5" />
        </button>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className={`${NAV_BASE} text-muted-foreground hover:bg-muted hover:text-foreground`}
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
          className={isActive('/settings') ? NAV_ACTIVE : NAV_INACTIVE}
          aria-label="Settings"
          aria-current={isActive('/settings') ? 'page' : undefined}
        >
          <Settings className="h-5 w-5" />
        </button>

        {/* Profile avatar with dropdown */}
        <ProfileDropdown
          profileName={profile.name}
          avatarColor={profile.avatar_color}
          mode={mode}
          onLogout={handleLogout}
        />
      </nav>
    </header>
  )
}
