import { useState } from 'react'
import { Trash2, AlertTriangle, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { api, type DeletionPreview } from '../../api/client'
import UserDeletionModal from './UserDeletionModal'

interface DeleteAccountSectionProps {
  /**
   * Kept for API stability / test compatibility; the passkey self-delete
   * endpoint infers the target profile from the authenticated session.
   * Legacy callers that passed a numeric id don't need to change.
   */
  profileId: number
  onDeleted: () => void
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- profileId kept for API stability
export default function DeleteAccountSection({ profileId: _profileId, onDeleted }: DeleteAccountSectionProps) {
  const [showModal, setShowModal] = useState(false)
  const [preview, setPreview] = useState<DeletionPreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleDeleteClick = async () => {
    setLoading(true)
    try {
      // Passkey-mode self-delete uses /auth/me/* which works under SessionAuth.
      // The /profiles/{id}/* equivalents are HomeOnlyAuth (404 in passkey) —
      // pre-v1.53.0 this silently failed ("Failed to load account info").
      const data = await api.auth.meDeletionPreview()
      setPreview(data)
      setShowModal(true)
    } catch {
      toast.error('Failed to load account info')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = async () => {
    setDeleting(true)
    try {
      await api.auth.deleteMe()
      toast.success('Account deleted')
      onDeleted()
    } catch {
      toast.error('Failed to delete account')
      setDeleting(false)
    }
  }

  const handleCancel = () => {
    setShowModal(false)
    setPreview(null)
  }

  return (
    <div className="rounded-lg border border-destructive/30 bg-card p-4">
      <div className="flex items-center gap-2 text-destructive">
        <AlertTriangle className="h-5 w-5" />
        <h2 className="text-lg font-medium">Delete Account</h2>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">
        Permanently delete your account and all associated data. This cannot be undone.
      </p>
      <button
        onClick={handleDeleteClick}
        disabled={loading}
        className="mt-4 flex items-center gap-2 rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground transition-colors hover:bg-destructive/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Trash2 className="h-4 w-4" />
        )}
        Delete My Account
      </button>

      {showModal && preview && (
        <UserDeletionModal
          preview={preview}
          deleting={deleting}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}
    </div>
  )
}
