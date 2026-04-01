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
          className="flex items-center gap-1 rounded-full border border-border bg-background px-3 py-1.5 text-sm text-foreground transition-colors hover:bg-muted disabled:opacity-50"
        >
          {loadingTimerId === `quick-${idx}` ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Plus className="h-3 w-3" />
          )}
          {label}
        </button>
      ))}
      {aiAvailable && instructionText && <Sparkles className="h-4 w-4 text-primary self-center" />}
    </div>
  )
}
