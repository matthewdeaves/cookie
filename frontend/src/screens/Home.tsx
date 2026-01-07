import { Moon, Sun, LogOut } from 'lucide-react'
import type { Profile } from '../api/client'

interface HomeProps {
  profile: Profile
  theme: 'light' | 'dark'
  onThemeToggle: () => void
  onLogout: () => void
}

export default function Home({
  profile,
  theme,
  onThemeToggle,
  onLogout,
}: HomeProps) {
  const getInitial = (name: string) => {
    return name.charAt(0).toUpperCase()
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border px-4 py-3">
        <h1 className="text-xl font-medium text-primary">Cookie</h1>

        <div className="flex items-center gap-3">
          {/* Theme toggle */}
          <button
            onClick={onThemeToggle}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
          >
            {theme === 'light' ? (
              <Moon className="h-5 w-5" />
            ) : (
              <Sun className="h-5 w-5" />
            )}
          </button>

          {/* Profile avatar */}
          <div
            className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-medium text-white"
            style={{ backgroundColor: profile.avatar_color }}
          >
            {getInitial(profile.name)}
          </div>

          {/* Logout */}
          <button
            onClick={onLogout}
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Switch profile"
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </header>

      {/* Main content placeholder */}
      <main className="flex flex-1 flex-col items-center justify-center p-4">
        <div className="text-center">
          <h2 className="mb-2 text-2xl font-medium text-foreground">
            Welcome, {profile.name}!
          </h2>
          <p className="text-muted-foreground">
            Home screen with search and favorites coming in Session B
          </p>
        </div>
      </main>
    </div>
  )
}
