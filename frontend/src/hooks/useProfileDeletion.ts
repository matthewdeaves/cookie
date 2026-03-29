import { useState } from 'react'
import { toast } from 'sonner'
import { api, type ProfileWithStats, type DeletionPreview } from '../api/client'

interface UseProfileDeletionResult {
  showDeleteModal: boolean
  deletePreview: DeletionPreview | null
  deleting: boolean
  handleDeleteClick: (profileId: number) => Promise<void>
  handleConfirmDelete: () => Promise<void>
  handleCancelDelete: () => void
}

export function useProfileDeletion(
  profiles: ProfileWithStats[],
  onProfilesChange: (profiles: ProfileWithStats[]) => void
): UseProfileDeletionResult {
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deletePreview, setDeletePreview] = useState<DeletionPreview | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)

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

  return {
    showDeleteModal,
    deletePreview,
    deleting,
    handleDeleteClick,
    handleConfirmDelete,
    handleCancelDelete,
  }
}
