import { AlertTriangle } from 'lucide-react'
import type { ResetPreview } from '../../api/client'

interface ResetPreviewStepProps {
  resetPreview: ResetPreview
  onCancel: () => void
  onContinue: () => void
}

export default function ResetPreviewStep({
  resetPreview,
  onCancel,
  onContinue,
}: ResetPreviewStepProps) {
  return (
    <>
      <div className="flex items-center gap-2 text-destructive">
        <AlertTriangle className="h-5 w-5" />
        <h3 className="text-lg font-medium">Reset Database?</h3>
      </div>

      <div className="mt-4 space-y-4">
        <p className="text-sm text-foreground">
          This will permanently delete ALL data from the application:
        </p>

        <div className="rounded-lg border border-border bg-muted/50 p-3">
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>• {resetPreview.data_counts.profiles} profiles</li>
            <li>
              • {resetPreview.data_counts.recipes} recipes (
              {resetPreview.data_counts.recipe_images} images)
            </li>
            <li>• {resetPreview.data_counts.favorites} favorites</li>
            <li>• {resetPreview.data_counts.collections} collections</li>
            <li>
              • {resetPreview.data_counts.view_history} view history
              entries
            </li>
            <li>
              •{' '}
              {resetPreview.data_counts.ai_suggestions +
                resetPreview.data_counts.serving_adjustments}{' '}
              cached AI entries
            </li>
          </ul>
        </div>

        <p className="text-sm font-medium text-destructive">
          This action cannot be undone.
        </p>
      </div>

      <div className="mt-6 flex justify-end gap-3">
        <button
          onClick={onCancel}
          className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
        >
          Cancel
        </button>
        <button
          onClick={onContinue}
          className="rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground transition-colors hover:bg-destructive/90"
        >
          I understand, continue
        </button>
      </div>
    </>
  )
}
