import { useState, useRef, useEffect } from 'react'
import { LogOut, User } from 'lucide-react'

interface ProfileDropdownProps {
  profileName: string
  avatarColor: string
  mode: string
  onLogout: () => void
}

function getInitial(name: string) {
  return name.charAt(0).toUpperCase()
}

export default function ProfileDropdown({
  profileName,
  avatarColor,
  mode,
  onLogout,
}: ProfileDropdownProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!dropdownOpen) return
    // pointerdown covers mouse, touch and pen (mousedown is unreliable for touch on some browsers).
    const handleClick = (e: Event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDropdownOpen(false)
    }
    document.addEventListener('pointerdown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('pointerdown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [dropdownOpen])

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setDropdownOpen(!dropdownOpen)}
        className="inline-flex h-11 w-11 items-center justify-center rounded-full"
        aria-label={`${profileName} menu`}
        aria-haspopup="menu"
        aria-expanded={dropdownOpen}
      >
        <span
          className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium text-white"
          style={{ backgroundColor: avatarColor }}
        >
          {mode === 'passkey' ? (
            <User className="h-4 w-4" aria-hidden="true" />
          ) : (
            getInitial(profileName)
          )}
        </span>
      </button>

      {dropdownOpen && (
        <div role="menu" className="absolute right-0 top-full z-50 mt-1 w-48 rounded-lg border border-border bg-card py-1 shadow-lg">
          <button
            role="menuitem"
            onClick={() => { setDropdownOpen(false); onLogout() }}
            className="flex min-h-11 w-full items-center gap-2 px-3 py-2 text-sm text-card-foreground hover:bg-muted"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
      )}
    </div>
  )
}
