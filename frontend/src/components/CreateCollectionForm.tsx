import { X } from 'lucide-react'

interface CreateCollectionFormProps {
  name: string
  onNameChange: (name: string) => void
  creating: boolean
  onSubmit: (e: React.FormEvent) => void
  onCancel: () => void
}

export default function CreateCollectionForm({
  name,
  onNameChange,
  creating,
  onSubmit,
  onCancel,
}: CreateCollectionFormProps) {
  return (
    <form
      onSubmit={onSubmit}
      className="mb-6 rounded-lg border border-border bg-card p-4"
    >
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-medium text-foreground">New Collection</h2>
        <button
          type="button"
          onClick={onCancel}
          className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
      <input
        type="text"
        value={name}
        onChange={(e) => onNameChange(e.target.value)}
        placeholder="Collection name"
        className="mb-3 w-full rounded-lg border border-border bg-input-background px-3 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        autoFocus
      />
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg px-4 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!name.trim() || creating}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          {creating ? 'Creating...' : 'Create'}
        </button>
      </div>
    </form>
  )
}
