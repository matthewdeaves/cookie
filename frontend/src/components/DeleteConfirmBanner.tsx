interface DeleteConfirmBannerProps {
  itemName: string
  deleting: boolean
  onConfirm: () => void
  onCancel: () => void
}

export default function DeleteConfirmBanner({
  itemName,
  deleting,
  onConfirm,
  onCancel,
}: DeleteConfirmBannerProps) {
  return (
    <div className="border-b border-destructive/30 bg-destructive/10 px-4 py-3">
      <div className="mx-auto flex max-w-4xl items-center justify-between">
        <p className="text-sm text-foreground">
          Delete "{itemName}"? This cannot be undone.
        </p>
        <div className="flex gap-2">
          <button
            onClick={onCancel}
            className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={deleting}
            className="rounded-lg bg-destructive px-3 py-1.5 text-sm font-medium text-destructive-foreground transition-colors hover:bg-destructive/90 disabled:opacity-50"
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}
