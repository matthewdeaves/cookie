import { useState, useRef, useEffect } from 'react'
import { LogOut, Users, User } from 'lucide-react'

interface ProfileDropdownProps {
  profileName: string
  avatarColor: string
  mode: string
  onSwitchProfile: () => void
  onLogout: () => void
}

function getInitial(name: string) {
  return name.charAt(0).toUpperCase()
}

export default function ProfileDropdown({
  profileName,
  avatarColor,
  mode,
  onSwitchProfile,
  onLogout,
}: ProfileDropdownProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

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

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setDropdownOpen(!dropdownOpen)}
        className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium text-white"
        style={{ backgroundColor: avatarColor }}
        aria-label={profileName}
      >
        {mode === 'passkey' ? (
          <User className="h-4 w-4" />
        ) : (
          getInitial(profileName)
        )}
      </button>

      {dropdownOpen && (
        <div className="absolute right-0 top-full z-50 mt-1 w-44 rounded-lg border border-border bg-card py-1 shadow-lg">
          <button
            onClick={() => { setDropdownOpen(false); onSwitchProfile() }}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-card-foreground hover:bg-muted"
          >
            <Users className="h-4 w-4" />
            Switch profile
          </button>
          <button
            onClick={() => { setDropdownOpen(false); onLogout() }}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-card-foreground hover:bg-muted"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
      )}
    </div>
  )
}
