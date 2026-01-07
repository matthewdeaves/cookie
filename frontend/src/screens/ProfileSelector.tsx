import { useState, useEffect } from 'react'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { api, type Profile, type ProfileInput } from '../api/client'
import { cn } from '../lib/utils'

const PROFILE_COLORS = [
  '#d97850',
  '#8fae6f',
  '#c9956b',
  '#6b9dad',
  '#d16b6b',
  '#9d80b8',
  '#e6a05f',
  '#6bb8a5',
  '#c77a9e',
  '#7d9e6f',
]

interface ProfileSelectorProps {
  onProfileSelect: (profile: Profile) => void
}

export default function ProfileSelector({
  onProfileSelect,
}: ProfileSelectorProps) {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [selectedColor, setSelectedColor] = useState(PROFILE_COLORS[0])
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    loadProfiles()
  }, [])

  const loadProfiles = async () => {
    try {
      const data = await api.profiles.list()
      setProfiles(data)
    } catch (error) {
      console.error('Failed to load profiles:', error)
      toast.error('Failed to load profiles')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return

    setCreating(true)
    try {
      const data: ProfileInput = {
        name: newName.trim(),
        avatar_color: selectedColor,
        theme: 'light',
        unit_preference: 'metric',
      }
      const profile = await api.profiles.create(data)
      setProfiles([...profiles, profile])
      setShowCreateForm(false)
      setNewName('')
      setSelectedColor(PROFILE_COLORS[0])
      toast.success(`Welcome, ${profile.name}!`)
    } catch (error) {
      console.error('Failed to create profile:', error)
      toast.error('Failed to create profile')
    } finally {
      setCreating(false)
    }
  }

  const getInitial = (name: string) => {
    return name.charAt(0).toUpperCase()
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-md text-center">
        {/* Title */}
        <h1 className="mb-2 text-4xl font-medium text-primary">Cookie</h1>
        <p className="mb-10 text-muted-foreground">Who's cooking today?</p>

        {/* Profile grid */}
        <div className="mb-8 flex flex-wrap justify-center gap-6">
          {profiles.map((profile) => (
            <button
              key={profile.id}
              onClick={() => onProfileSelect(profile)}
              className="group flex flex-col items-center gap-2"
            >
              <div
                className="flex h-20 w-20 items-center justify-center rounded-full text-2xl font-medium text-white transition-transform group-hover:scale-105"
                style={{ backgroundColor: profile.avatar_color }}
              >
                {getInitial(profile.name)}
              </div>
              <span className="text-sm text-foreground">{profile.name}</span>
            </button>
          ))}

          {/* Add profile button */}
          <button
            onClick={() => setShowCreateForm(true)}
            className="group flex flex-col items-center gap-2"
          >
            <div className="flex h-20 w-20 items-center justify-center rounded-full border-2 border-dashed border-muted-foreground/40 transition-colors group-hover:border-primary">
              <Plus className="h-8 w-8 text-muted-foreground/60 group-hover:text-primary" />
            </div>
            <span className="text-sm text-muted-foreground">Add Profile</span>
          </button>
        </div>

        {/* Create profile form */}
        {showCreateForm && (
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-medium text-card-foreground">
              Create Profile
            </h2>
            <form onSubmit={handleCreateProfile}>
              <div className="mb-4">
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Enter your name"
                  className="w-full rounded-lg border border-border bg-input-background px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  autoFocus
                  maxLength={20}
                />
              </div>

              {/* Color picker */}
              <div className="mb-6">
                <label className="mb-2 block text-sm text-muted-foreground">
                  Choose a color
                </label>
                <div className="flex flex-wrap justify-center gap-2">
                  {PROFILE_COLORS.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setSelectedColor(color)}
                      className={cn(
                        'h-10 w-10 rounded-full transition-transform hover:scale-110',
                        selectedColor === color && 'ring-2 ring-ring ring-offset-2 ring-offset-card'
                      )}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>

              {/* Buttons */}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false)
                    setNewName('')
                    setSelectedColor(PROFILE_COLORS[0])
                  }}
                  className="flex-1 rounded-lg border border-border bg-secondary px-4 py-2.5 text-secondary-foreground transition-colors hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newName.trim() || creating}
                  className="flex-1 rounded-lg bg-primary px-4 py-2.5 text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  )
}
