import { type ProfileWithStats } from '../../api/client'
import { useProfileDeletion } from '../../hooks/useProfileDeletion'
import UserProfileCard from './UserProfileCard'
import UserDeletionModal from './UserDeletionModal'

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
  const {
    showDeleteModal,
    deletePreview,
    deleting,
    handleDeleteClick,
    handleConfirmDelete,
    handleCancelDelete,
  } = useProfileDeletion(profiles, onProfilesChange)

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
          {profiles.map((profile) => (
            <UserProfileCard
              key={profile.id}
              profile={profile}
              isCurrent={profile.id === currentProfileId}
              onDeleteClick={handleDeleteClick}
              onProfileUpdate={(id, changes) => {
                onProfilesChange(profiles.map((p) => (p.id === id ? { ...p, ...changes } : p)))
              }}
            />
          ))}
        </div>
      </div>

      {showDeleteModal && deletePreview && (
        <UserDeletionModal
          preview={deletePreview}
          deleting={deleting}
          onConfirm={handleConfirmDelete}
          onCancel={handleCancelDelete}
        />
      )}
    </>
  )
}
