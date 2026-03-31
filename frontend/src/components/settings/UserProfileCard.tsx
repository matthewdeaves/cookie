import { useState } from 'react'
import { Trash2, Pencil, Check, X } from 'lucide-react'
import { toast } from 'sonner'
import { api, type ProfileWithStats } from '../../api/client'
import { cn } from '../../lib/utils'
import { formatDate } from './settingsUtils'

interface UserProfileCardProps {
  profile: ProfileWithStats
  isCurrent: boolean
  onDeleteClick: (profileId: number) => void
  onProfileUpdate: (id: number, changes: Partial<ProfileWithStats>) => void
}

export default function UserProfileCard({
  profile,
  isCurrent,
  onDeleteClick,
  onProfileUpdate,
}: UserProfileCardProps) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full" style={{ backgroundColor: profile.avatar_color }} />
          <div>
            <ProfileName profile={profile} onProfileUpdate={onProfileUpdate} isCurrent={isCurrent} />
            <div className="text-sm text-muted-foreground">Created {formatDate(profile.created_at)}</div>
            <div className="text-xs text-muted-foreground">
              {profile.stats.favorites} favorites · {profile.stats.collections} collections · {profile.stats.remixes} remixes
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <UnlimitedToggle profile={profile} onProfileUpdate={onProfileUpdate} />
          <button
            onClick={() => onDeleteClick(profile.id)}
            disabled={isCurrent}
            className={cn(
              'rounded p-2 transition-colors',
              isCurrent
                ? 'cursor-not-allowed text-muted-foreground/50'
                : 'text-muted-foreground hover:bg-destructive/10 hover:text-destructive',
            )}
            title={isCurrent ? 'Cannot delete current profile' : 'Delete profile'}
          >
            <Trash2 className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}

function UnlimitedToggle({
  profile,
  onProfileUpdate,
}: {
  profile: ProfileWithStats
  onProfileUpdate: (id: number, changes: Partial<ProfileWithStats>) => void
}) {
  const [toggling, setToggling] = useState(false)
  const isUnlimited = profile.unlimited_ai

  const handleToggle = async () => {
    setToggling(true)
    try {
      const res = await api.profiles.setUnlimited(profile.id, !isUnlimited)
      onProfileUpdate(profile.id, { unlimited_ai: res.unlimited_ai })
      toast.success(res.unlimited_ai ? 'Unlimited AI enabled' : 'Unlimited AI disabled')
    } catch {
      toast.error('Failed to update unlimited status')
    } finally {
      setToggling(false)
    }
  }

  return (
    <label className="flex items-center gap-1.5 text-xs text-muted-foreground" title="Unlimited AI">
      <span>Unlimited</span>
      <button
        role="switch"
        aria-checked={isUnlimited}
        aria-label={`Unlimited AI for ${profile.name}`}
        onClick={handleToggle}
        disabled={toggling}
        className={cn(
          'relative inline-flex h-5 w-9 items-center rounded-full transition-colors',
          isUnlimited ? 'bg-primary' : 'bg-muted',
          toggling && 'opacity-50',
        )}
      >
        <span className={cn('inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform', isUnlimited ? 'translate-x-4' : 'translate-x-0.5')} />
      </button>
    </label>
  )
}

function ProfileName({
  profile,
  onProfileUpdate,
  isCurrent,
}: {
  profile: ProfileWithStats
  onProfileUpdate: (id: number, changes: Partial<ProfileWithStats>) => void
  isCurrent: boolean
}) {
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(profile.name)

  const save = async () => {
    const trimmed = name.trim()
    if (!trimmed || trimmed === profile.name) { setEditing(false); return }
    try {
      const res = await api.profiles.rename(profile.id, trimmed)
      onProfileUpdate(profile.id, { name: res.name })
      toast.success('Profile renamed')
    } catch {
      toast.error('Failed to rename profile')
      setName(profile.name)
    }
    setEditing(false)
  }

  if (editing) {
    return (
      <div className="flex items-center gap-1">
        <input
          autoFocus
          aria-label="Profile name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={save}
          onKeyDown={(e) => { if (e.key === 'Enter') save(); if (e.key === 'Escape') { setName(profile.name); setEditing(false) } }}
          className="w-32 rounded border border-border bg-input-background px-1.5 py-0.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        />
        <button onClick={save} className="text-primary"><Check className="h-3.5 w-3.5" /></button>
        <button onClick={() => { setName(profile.name); setEditing(false) }} className="text-muted-foreground"><X className="h-3.5 w-3.5" /></button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <span className="font-medium text-foreground">{profile.name}</span>
      {isCurrent && (
        <span className="rounded bg-primary/10 px-2 py-0.5 text-xs text-primary">Current</span>
      )}
      <button onClick={() => setEditing(true)} className="text-muted-foreground hover:text-foreground" title="Rename">
        <Pencil className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}
