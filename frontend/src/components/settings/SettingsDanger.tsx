import { useState } from 'react'
import { AlertTriangle, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { api, type ResetPreview } from '../../api/client'

export default function SettingsDanger() {
  const [showResetModal, setShowResetModal] = useState(false)
  const [resetPreview, setResetPreview] = useState<ResetPreview | null>(null)
  const [resetStep, setResetStep] = useState<1 | 2>(1)
  const [resetConfirmText, setResetConfirmText] = useState('')
  const [resetting, setResetting] = useState(false)

  const handleResetClick = async () => {
    try {
      const preview = await api.system.resetPreview()
      setResetPreview(preview)
      setResetStep(1)
      setResetConfirmText('')
      setShowResetModal(true)
    } catch (error) {
      console.error('Failed to load reset preview:', error)
      toast.error('Failed to load reset preview')
    }
  }

  const handleResetContinue = () => {
    setResetStep(2)
  }

  const handleResetBack = () => {
    setResetStep(1)
    setResetConfirmText('')
  }

  const handleConfirmReset = async () => {
    if (resetConfirmText !== 'RESET') return

    setResetting(true)
    try {
      await api.system.reset('RESET')
      toast.success('Database reset complete')
      // Redirect to home/profile creation
      window.location.href = '/'
    } catch (error) {
      console.error('Failed to reset database:', error)
      toast.error('Failed to reset database')
    } finally {
      setResetting(false)
    }
  }

  const handleCancelReset = () => {
    setShowResetModal(false)
    setResetPreview(null)
    setResetStep(1)
    setResetConfirmText('')
  }

  return (
    <>
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
            onClick={handleResetClick}
            className="mt-4 rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground transition-colors hover:bg-destructive/90"
          >
            Reset Database
          </button>
        </div>
      </div>

      {/* Database Reset Modal */}
      {showResetModal && resetPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={handleCancelReset}
          />
          <div className="relative w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
            {resetStep === 1 ? (
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
                    onClick={handleCancelReset}
                    className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleResetContinue}
                    className="rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground transition-colors hover:bg-destructive/90"
                  >
                    I understand, continue
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center gap-2 text-destructive">
                  <AlertTriangle className="h-5 w-5" />
                  <h3 className="text-lg font-medium">Confirm Reset</h3>
                </div>

                <div className="mt-4 space-y-4">
                  <p className="text-sm text-foreground">
                    Type{' '}
                    <code className="rounded bg-muted px-1 font-mono">RESET</code>{' '}
                    to confirm:
                  </p>

                  <input
                    type="text"
                    value={resetConfirmText}
                    onChange={(e) => setResetConfirmText(e.target.value)}
                    placeholder="Type RESET"
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 font-mono text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div className="mt-6 flex justify-end gap-3">
                  <button
                    onClick={handleResetBack}
                    className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleConfirmReset}
                    disabled={resetConfirmText !== 'RESET' || resetting}
                    className="flex items-center gap-2 rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground transition-colors hover:bg-destructive/90 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {resetting && <Loader2 className="h-4 w-4 animate-spin" />}
                    Reset Database
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  )
}
