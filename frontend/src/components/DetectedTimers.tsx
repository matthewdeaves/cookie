import { Plus, Loader2 } from 'lucide-react'

interface DetectedTimersProps {
  detectedTimes: number[]
  loadingTimerId: string | null
  formatTime: (seconds: number) => string
  onAdd: (seconds: number, index: number) => void
}

export default function DetectedTimers({
  detectedTimes,
  loadingTimerId,
  formatTime,
  onAdd,
}: DetectedTimersProps) {
  if (detectedTimes.length === 0) return null

  return (
    <div>
      <p className="mb-2 text-xs text-muted-foreground">
        Detected in this step:
      </p>
      <div className="flex flex-wrap gap-2">
        {detectedTimes.map((seconds, idx) => (
          <button
            key={idx}
            onClick={() => onAdd(seconds, idx)}
            disabled={loadingTimerId !== null}
            className="flex items-center gap-1.5 rounded-full bg-primary/10 px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/20 active:bg-primary/30 disabled:opacity-50"
          >
            {loadingTimerId === `detected-${idx}` ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Plus className="h-3.5 w-3.5" />
            )}
            {formatTime(seconds)}
          </button>
        ))}
      </div>
    </div>
  )
}
