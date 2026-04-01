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

  return (
    <div
      className={cn(
        'flex items-center rounded-lg border border-border bg-card p-2.5',
        isComplete
          ? 'border-l-[3px] border-l-accent'
          : timer.isRunning
            ? 'border-l-[3px] border-l-primary'
            : 'border-l-[3px] border-l-muted',
      )}
    >
      {/* Info */}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-muted-foreground">
          {timer.label}
        </p>
        <p
          className={cn(
            'font-mono text-2xl font-bold tabular-nums',
            isComplete
              ? 'text-accent'
              : timer.isRunning
                ? 'text-primary'
                : 'text-foreground',
          )}
        >
          {formatTimerDisplay(timer.remaining)}
        </p>
      </div>

      {/* Actions */}
      <div className="ml-2 flex shrink-0 items-center gap-1.5">
        {!isComplete && (
          <>
            <button
              onClick={onToggle}
              className={cn(
                'flex h-9 w-9 items-center justify-center rounded-full transition-colors',
                timer.isRunning
                  ? 'bg-muted text-muted-foreground hover:bg-muted/80'
                  : 'bg-primary text-primary-foreground hover:bg-primary/90',
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
              className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-muted-foreground transition-colors hover:bg-muted/80"
              aria-label="Reset"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
          </>
        )}
        <button
          onClick={onDelete}
          className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-muted-foreground transition-colors hover:bg-destructive hover:text-destructive-foreground"
          aria-label="Delete"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
