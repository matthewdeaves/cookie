import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { api, type Profile, type ProfileInput } from '../api/client'
import { useProfile } from '../contexts/ProfileContext'
import CreateProfileForm, { PROFILE_COLORS } from '../components/CreateProfileForm'

export default function ProfileSelector() {
  const navigate = useNavigate()
  const { selectProfile } = useProfile()
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [selectedColor, setSelectedColor] = useState(PROFILE_COLORS[0])
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await api.profiles.list()
        if (!cancelled) setProfiles(data)
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load profiles:', error)
          toast.error('Failed to load profiles')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [])

  const handleProfileSelect = async (profile: Profile) => {
    try {
      await selectProfile(profile)
      navigate('/home')
    } catch (error) {
      console.error('Failed to select profile:', error)
      toast.error('Failed to select profile')
    }
  }

  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    setCreating(true)
    try {
      const data: ProfileInput = { name: newName.trim(), avatar_color: selectedColor, theme: 'light', unit_preference: 'metric' }
      const profile = await api.profiles.create(data)
      setProfiles([...profiles, profile])
      await selectProfile(profile)
      toast.success(`Welcome, ${profile.name}!`)
      navigate('/home')
    } catch (error) {
      console.error('Failed to create profile:', error)
      toast.error('Failed to create profile')
    } finally {
      setCreating(false)
    }
  }

  const handleCancelCreate = () => {
    setShowCreateForm(false)
    setNewName('')
    setSelectedColor(PROFILE_COLORS[0])
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
        <h1 className="mb-2 text-4xl font-medium text-primary">Cookie</h1>
        <p className="mb-10 text-muted-foreground">Who's cooking today?</p>
        <ProfileGrid profiles={profiles} onSelect={handleProfileSelect} onAddClick={() => setShowCreateForm(true)} />
        {showCreateForm && (
          <CreateProfileForm newName={newName} onNameChange={setNewName} selectedColor={selectedColor} onColorChange={setSelectedColor} creating={creating} onSubmit={handleCreateProfile} onCancel={handleCancelCreate} />
        )}
      </div>
    </div>
  )
}

function ProfileGrid({ profiles, onSelect, onAddClick }: { profiles: Profile[]; onSelect: (p: Profile) => void; onAddClick: () => void }) {
  const getInitial = (name: string) => name.charAt(0).toUpperCase()
  return (
    <div className="mb-8 flex flex-wrap justify-center gap-6">
      {profiles.map((profile) => (
        <button key={profile.id} onClick={() => onSelect(profile)} className="group flex flex-col items-center gap-2">
          <div className="flex h-20 w-20 items-center justify-center rounded-full text-2xl font-medium text-white transition-transform group-hover:scale-105" style={{ backgroundColor: profile.avatar_color }}>
            {getInitial(profile.name)}
          </div>
          <span className="text-sm text-foreground">{profile.name}</span>
        </button>
      ))}
      <button onClick={onAddClick} className="group flex flex-col items-center gap-2">
        <div className="flex h-20 w-20 items-center justify-center rounded-full border-2 border-dashed border-muted-foreground/40 transition-colors group-hover:border-primary">
          <Plus className="h-8 w-8 text-muted-foreground/60 group-hover:text-primary" />
        </div>
        <span className="text-sm text-muted-foreground">Add Profile</span>
      </button>
    </div>
  )
}
