import { Trash2, AlertTriangle, Loader2 } from 'lucide-react'
import { type DeletionPreview } from '../../api/client'
import { formatDate } from './settingsUtils'

interface UserDeletionModalProps {
  preview: DeletionPreview
  deleting: boolean
  onConfirm: () => void
  onCancel: () => void
}

function getDeletionItems(data: DeletionPreview['data_to_delete']): string[] {
  const items: string[] = []
  if (data.remixes > 0) {
    items.push(`${data.remixes} remixed recipe${data.remixes !== 1 ? 's' : ''} (${data.remix_images} images)`)
  }
  if (data.favorites > 0) {
    items.push(`${data.favorites} favorite${data.favorites !== 1 ? 's' : ''}`)
  }
  if (data.collections > 0) {
    items.push(`${data.collections} collection${data.collections !== 1 ? 's' : ''} (${data.collection_items} items)`)
  }
  if (data.view_history > 0) {
    items.push(`${data.view_history} view history entries`)
  }
  if (data.scaling_cache > 0 || data.discover_cache > 0) {
    items.push('Cached AI data')
  }
  return items
}

function DeletionDataSummary({ data }: { data: DeletionPreview['data_to_delete'] }) {
  const items = getDeletionItems(data)

  return (
    <div className="rounded-lg border border-border bg-muted/50 p-3">
      <div className="mb-2 text-sm font-medium text-foreground">
        Data to be deleted:
      </div>
      <ul className="space-y-1 text-sm text-muted-foreground">
        {items.length === 0
          ? <li>• No associated data</li>
          : items.map((item) => <li key={item}>• {item}</li>)
        }
      </ul>
    </div>
  )
}

export default function UserDeletionModal({
  preview,
  deleting,
  onConfirm,
  onCancel,
}: UserDeletionModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onCancel}
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
              style={{ backgroundColor: preview.profile.avatar_color }}
            />
            <div>
              <div className="font-medium text-foreground">
                {preview.profile.name}
              </div>
              <div className="text-sm text-muted-foreground">
                Created {formatDate(preview.profile.created_at)}
              </div>
            </div>
          </div>

          <DeletionDataSummary data={preview.data_to_delete} />

          {/* Warning */}
          <div className="text-sm text-destructive">
            This action cannot be undone. All data will be permanently deleted.
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
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
  )
}
