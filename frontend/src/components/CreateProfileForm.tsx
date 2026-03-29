import { cn } from '../lib/utils'

const PROFILE_COLORS = [
  '#d97850',
  '#8fae6f',
  '#6b9dad',
  '#9d80b8',
  '#d16b6b',
  '#e6a05f',
  '#6bb8a5',
  '#c77a9e',
  '#7d9e6f',
  '#5b8abf',
]

interface CreateProfileFormProps {
  newName: string
  onNameChange: (name: string) => void
  selectedColor: string
  onColorChange: (color: string) => void
  creating: boolean
  onSubmit: (e: React.FormEvent) => void
  onCancel: () => void
}

export default function CreateProfileForm({
  newName,
  onNameChange,
  selectedColor,
  onColorChange,
  creating,
  onSubmit,
  onCancel,
}: CreateProfileFormProps) {
  return (
    <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-medium text-card-foreground">
        Create Profile
      </h2>
      <form onSubmit={onSubmit}>
        <div className="mb-4">
          <input
            type="text"
            value={newName}
            onChange={(e) => onNameChange(e.target.value)}
            placeholder="Enter your name"
            className="w-full rounded-lg border border-border bg-input-background px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            autoFocus
            maxLength={20}
          />
        </div>

        {/* Color picker */}
        <div className="mb-6">
          <label className="mb-2 block text-sm text-muted-foreground">
            Choose a color
          </label>
          <div className="flex flex-wrap justify-center gap-2">
            {PROFILE_COLORS.map((color) => (
              <button
                key={color}
                type="button"
                onClick={() => onColorChange(color)}
                className={cn(
                  'h-10 w-10 rounded-full transition-transform hover:scale-110',
                  selectedColor === color &&
                    'ring-2 ring-ring ring-offset-2 ring-offset-card'
                )}
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 rounded-lg border border-border bg-secondary px-4 py-2.5 text-secondary-foreground transition-colors hover:bg-muted"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!newName.trim() || creating}
            className="flex-1 rounded-lg bg-primary px-4 py-2.5 text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
          >
            {creating ? 'Creating...' : 'Create'}
          </button>
        </div>
      </form>
    </div>
  )
}

export { PROFILE_COLORS }
