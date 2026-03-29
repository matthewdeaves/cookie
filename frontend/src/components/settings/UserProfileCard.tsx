import { Trash2 } from 'lucide-react'
import { type ProfileWithStats } from '../../api/client'
import { cn } from '../../lib/utils'
import { formatDate } from './settingsUtils'

interface UserProfileCardProps {
  profile: ProfileWithStats
  isCurrent: boolean
  onDeleteClick: (profileId: number) => void
}

export default function UserProfileCard({
  profile,
  isCurrent,
  onDeleteClick,
}: UserProfileCardProps) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-card p-4">
      <div className="flex items-center gap-3">
        {/* Avatar */}
        <div
          className="h-10 w-10 rounded-full"
          style={{ backgroundColor: profile.avatar_color }}
        />
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium text-foreground">{profile.name}</span>
            {isCurrent && (
              <span className="rounded bg-primary/10 px-2 py-0.5 text-xs text-primary">
                Current
              </span>
            )}
          </div>
          <div className="text-sm text-muted-foreground">
            Created {formatDate(profile.created_at)}
          </div>
          <div className="text-xs text-muted-foreground">
            {profile.stats.favorites} favorites ·{' '}
            {profile.stats.collections} collections ·{' '}
            {profile.stats.remixes} remixes
          </div>
        </div>
      </div>

      <button
        onClick={() => onDeleteClick(profile.id)}
        disabled={isCurrent}
        className={cn(
          'rounded p-2 transition-colors',
          isCurrent
            ? 'cursor-not-allowed text-muted-foreground/50'
            : 'text-muted-foreground hover:bg-destructive/10 hover:text-destructive'
        )}
        title={isCurrent ? 'Cannot delete current profile' : 'Delete profile'}
      >
        <Trash2 className="h-5 w-5" />
      </button>
    </div>
  )
}
