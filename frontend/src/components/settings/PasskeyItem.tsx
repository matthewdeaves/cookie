interface PasskeyItemProps {
  id: number
  createdAt: string | null
  lastUsedAt: string | null
  isDeletable: boolean
  onDelete: (id: number) => void
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Never'
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function PasskeyItem({
  id,
  createdAt,
  lastUsedAt,
  isDeletable,
  onDelete,
}: PasskeyItemProps) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-input bg-background p-4">
      <div>
        <div className="text-sm font-medium text-foreground">
          Passkey #{id}
        </div>
        <div className="text-xs text-muted-foreground">
          Added {formatDate(createdAt)}
        </div>
        <div className="text-xs text-muted-foreground">
          Last used: {formatDate(lastUsedAt)}
        </div>
      </div>
      {isDeletable && (
        <button
          onClick={() => onDelete(id)}
          className="rounded-md px-3 py-1 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
        >
          Delete
        </button>
      )}
    </div>
  )
}
