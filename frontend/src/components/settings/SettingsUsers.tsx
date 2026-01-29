import { useState } from 'react'
import { Trash2, AlertTriangle, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { api, type ProfileWithStats, type DeletionPreview } from '../../api/client'
import { cn } from '../../lib/utils'

interface SettingsUsersProps {
  profiles: ProfileWithStats[]
  currentProfileId?: number
  onProfilesChange: (profiles: ProfileWithStats[]) => void
}

export default function SettingsUsers({
  profiles,
  currentProfileId,
  onProfilesChange,
}: SettingsUsersProps) {
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deletePreview, setDeletePreview] = useState<DeletionPreview | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString()
  }

  const handleDeleteClick = async (profileId: number) => {
    try {
      const preview = await api.profiles.deletionPreview(profileId)
      setDeletePreview(preview)
      setDeletingId(profileId)
      setShowDeleteModal(true)
    } catch (error) {
      console.error('Failed to load deletion preview:', error)
      toast.error('Failed to load profile info')
    }
  }

  const handleConfirmDelete = async () => {
    if (!deletingId) return

    setDeleting(true)
    try {
      await api.profiles.delete(deletingId)
      onProfilesChange(profiles.filter((p) => p.id !== deletingId))
      toast.success('Profile deleted successfully')
      setShowDeleteModal(false)
      setDeletePreview(null)
      setDeletingId(null)
    } catch (error) {
      console.error('Failed to delete profile:', error)
      toast.error('Failed to delete profile')
    } finally {
      setDeleting(false)
    }
  }

  const handleCancelDelete = () => {
    setShowDeleteModal(false)
    setDeletePreview(null)
    setDeletingId(null)
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium text-foreground">User Management</h2>
            <p className="text-sm text-muted-foreground">
              Manage user profiles and their data
            </p>
          </div>
          <span className="text-sm text-muted-foreground">
            {profiles.length} profile{profiles.length !== 1 ? 's' : ''}
          </span>
        </div>

        <div className="space-y-3">
          {profiles.map((profile) => {
            const isCurrent = profile.id === currentProfileId

            return (
              <div
                key={profile.id}
                className="flex items-center justify-between rounded-lg border border-border bg-card p-4"
              >
                <div className="flex items-center gap-3">
                  {/* Avatar */}
                  <div
                    className="h-10 w-10 rounded-full"
                    style={{ backgroundColor: profile.avatar_color }}
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-foreground">
                        {profile.name}
                      </span>
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
                  onClick={() => handleDeleteClick(profile.id)}
                  disabled={isCurrent}
                  className={cn(
                    'rounded p-2 transition-colors',
                    isCurrent
                      ? 'cursor-not-allowed text-muted-foreground/50'
                      : 'text-muted-foreground hover:bg-destructive/10 hover:text-destructive'
                  )}
                  title={
                    isCurrent ? 'Cannot delete current profile' : 'Delete profile'
                  }
                >
                  <Trash2 className="h-5 w-5" />
                </button>
              </div>
            )
          })}
        </div>
      </div>

      {/* Delete Profile Modal */}
      {showDeleteModal && deletePreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={handleCancelDelete}
          />
          <div className="relative w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
            <div className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              <h3 className="text-lg font-medium">Delete Profile?</h3>
            </div>

            <div className="mt-4 space-y-4">
              {/* Profile info */}
              <div className="flex items-center gap-3">
                <div
                  className="h-12 w-12 rounded-full"
                  style={{ backgroundColor: deletePreview.profile.avatar_color }}
                />
                <div>
                  <div className="font-medium text-foreground">
                    {deletePreview.profile.name}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Created {formatDate(deletePreview.profile.created_at)}
                  </div>
                </div>
              </div>

              {/* Data summary */}
              <div className="rounded-lg border border-border bg-muted/50 p-3">
                <div className="mb-2 text-sm font-medium text-foreground">
                  Data to be deleted:
                </div>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  {deletePreview.data_to_delete.remixes > 0 && (
                    <li>
                      • {deletePreview.data_to_delete.remixes} remixed recipe
                      {deletePreview.data_to_delete.remixes !== 1 ? 's' : ''} (
                      {deletePreview.data_to_delete.remix_images} images)
                    </li>
                  )}
                  {deletePreview.data_to_delete.favorites > 0 && (
                    <li>
                      • {deletePreview.data_to_delete.favorites} favorite
                      {deletePreview.data_to_delete.favorites !== 1 ? 's' : ''}
                    </li>
                  )}
                  {deletePreview.data_to_delete.collections > 0 && (
                    <li>
                      • {deletePreview.data_to_delete.collections} collection
                      {deletePreview.data_to_delete.collections !== 1 ? 's' : ''} (
                      {deletePreview.data_to_delete.collection_items} items)
                    </li>
                  )}
                  {deletePreview.data_to_delete.view_history > 0 && (
                    <li>
                      • {deletePreview.data_to_delete.view_history} view history
                      entries
                    </li>
                  )}
                  {(deletePreview.data_to_delete.scaling_cache > 0 ||
                    deletePreview.data_to_delete.discover_cache > 0) && (
                    <li>• Cached AI data</li>
                  )}
                  {deletePreview.data_to_delete.remixes === 0 &&
                    deletePreview.data_to_delete.favorites === 0 &&
                    deletePreview.data_to_delete.collections === 0 &&
                    deletePreview.data_to_delete.view_history === 0 &&
                    deletePreview.data_to_delete.scaling_cache === 0 &&
                    deletePreview.data_to_delete.discover_cache === 0 && (
                      <li>• No associated data</li>
                    )}
                </ul>
              </div>

              {/* Warning */}
              <div className="text-sm text-destructive">
                This action cannot be undone. All data will be permanently deleted.
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={handleCancelDelete}
                className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={deleting}
                className="flex items-center gap-2 rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground transition-colors hover:bg-destructive/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {deleting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                Delete Profile
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
