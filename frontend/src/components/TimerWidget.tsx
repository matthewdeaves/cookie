import { Play, Pause, RotateCcw, X } from 'lucide-react'
import type { Timer } from '../hooks/useTimers'
import { formatTimerDisplay } from '../hooks/useTimers'
import { cn } from '../lib/utils'

interface TimerWidgetProps {
  timer: Timer
  onToggle: () => void
  onReset: () => void
  onDelete: () => void
}

export default function TimerWidget({
  timer,
  onToggle,
  onReset,
  onDelete,
}: TimerWidgetProps) {
  const isComplete = timer.remaining === 0
  const progress = ((timer.duration - timer.remaining) / timer.duration) * 100

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-lg border bg-card p-3',
        isComplete && 'border-accent bg-accent/10'
      )}
    >
      {/* Progress bar background */}
      <div
        className={cn(
          'absolute inset-0 opacity-20 transition-all',
          isComplete ? 'bg-accent' : 'bg-primary'
        )}
        style={{ width: `${progress}%` }}
      />

      {/* Content */}
      <div className="relative flex items-center justify-between">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-card-foreground">
            {timer.label}
          </p>
          <p
            className={cn(
              'text-2xl font-mono font-bold tabular-nums',
              isComplete ? 'text-accent' : 'text-foreground'
            )}
          >
            {formatTimerDisplay(timer.remaining)}
          </p>
        </div>

        <div className="flex items-center gap-1">
          {!isComplete && (
            <>
              <button
                onClick={onToggle}
                className={cn(
                  'rounded-full p-2 transition-colors',
                  timer.isRunning
                    ? 'bg-muted text-muted-foreground hover:bg-muted/80'
                    : 'bg-primary text-primary-foreground hover:bg-primary/90'
                )}
                aria-label={timer.isRunning ? 'Pause' : 'Play'}
              >
                {timer.isRunning ? (
                  <Pause className="h-4 w-4" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
              </button>
              <button
                onClick={onReset}
                className="rounded-full bg-muted p-2 text-muted-foreground transition-colors hover:bg-muted/80"
                aria-label="Reset"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
            </>
          )}
          <button
            onClick={onDelete}
            className="rounded-full bg-muted p-2 text-muted-foreground transition-colors hover:bg-destructive hover:text-destructive-foreground"
            aria-label="Delete"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
