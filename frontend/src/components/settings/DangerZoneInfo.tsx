import { AlertTriangle } from 'lucide-react'

interface DangerZoneInfoProps {
  onResetClick: () => void
}

export default function DangerZoneInfo({ onResetClick }: DangerZoneInfoProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-destructive">
        <AlertTriangle className="h-5 w-5" />
        <h2 className="text-lg font-medium">Danger Zone</h2>
      </div>

      <p className="text-sm text-muted-foreground">
        Destructive operations that cannot be undone
      </p>

      <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-6">
        <h3 className="font-medium text-destructive">Reset Database</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Completely reset the application to factory state
        </p>

        <ul className="mt-4 space-y-1 text-sm text-muted-foreground">
          <li>• All recipes (scraped and remixed)</li>
          <li>• All recipe images</li>
          <li>• All user profiles</li>
          <li>• All favorites, collections, and view history</li>
          <li>• All cached AI data</li>
        </ul>

        <p className="mt-4 text-xs text-muted-foreground">
          Search source configurations and AI prompts will be preserved.
        </p>

        <button
          onClick={onResetClick}
          className="mt-4 rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground transition-colors hover:bg-destructive/90"
        >
          Reset Database
        </button>
      </div>
    </div>
  )
}
