import { Plus, Sparkles, Loader2 } from 'lucide-react'

interface QuickTimer {
  label: string
  duration: number
}

interface QuickTimerButtonsProps {
  quickTimers: QuickTimer[]
  loadingTimerId: string | null
  aiAvailable: boolean
  instructionText?: string
  onAdd: (label: string, duration: number, index: number) => void
}

export default function QuickTimerButtons({
  quickTimers,
  loadingTimerId,
  aiAvailable,
  instructionText,
  onAdd,
}: QuickTimerButtonsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {quickTimers.map(({ label, duration }, idx) => (
        <button
          key={label}
          onClick={() => onAdd(label, duration, idx)}
          disabled={loadingTimerId !== null}
          className="flex items-center gap-1.5 rounded-full border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted active:bg-muted/70 disabled:opacity-50"
        >
          {loadingTimerId === `quick-${idx}` ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Plus className="h-3.5 w-3.5" />
          )}
          {label}
        </button>
      ))}
      {aiAvailable && instructionText && <Sparkles className="h-4 w-4 self-center text-primary" />}
    </div>
  )
}
