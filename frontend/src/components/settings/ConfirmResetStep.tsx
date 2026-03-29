import { useState } from 'react'
import { AlertTriangle, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../../api/client'

interface ConfirmResetStepProps {
  onBack: () => void
}

export default function ConfirmResetStep({ onBack }: ConfirmResetStepProps) {
  const [confirmText, setConfirmText] = useState('')
  const [resetting, setResetting] = useState(false)

  const handleConfirmReset = async () => {
    if (confirmText !== 'RESET') return

    setResetting(true)
    try {
      await api.system.reset('RESET')
      toast.success('Database reset complete')
      window.location.href = '/'
    } catch (error) {
      console.error('Failed to reset database:', error)
      toast.error('Failed to reset database')
    } finally {
      setResetting(false)
    }
  }

  return (
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
          value={confirmText}
          onChange={(e) => setConfirmText(e.target.value)}
          placeholder="Type RESET"
          className="w-full rounded-lg border border-border bg-background px-3 py-2 font-mono text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </div>

      <div className="mt-6 flex justify-end gap-3">
        <button
          onClick={onBack}
          className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
        >
          Back
        </button>
        <button
          onClick={handleConfirmReset}
          disabled={confirmText !== 'RESET' || resetting}
          className="flex items-center gap-2 rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground transition-colors hover:bg-destructive/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {resetting && <Loader2 className="h-4 w-4 animate-spin" />}
          Reset Database
        </button>
      </div>
    </>
  )
}
