import type { Timer } from '../hooks/useTimers'
import TimerWidget from './TimerWidget'

interface TimerListProps {
  timers: Timer[]
  onToggle: (id: string) => void
  onReset: (id: string) => void
  onDelete: (id: string) => void
}

export default function TimerList({
  timers,
  onToggle,
  onReset,
  onDelete,
}: TimerListProps) {
  if (timers.length === 0) {
    return (
      <p className="text-center text-sm text-muted-foreground">
        No active timers. Add one above!
      </p>
    )
  }

  return (
    <div className="space-y-2">
      {timers.map((timer) => (
        <TimerWidget
          key={timer.id}
          timer={timer}
          onToggle={() => onToggle(timer.id)}
          onReset={() => onReset(timer.id)}
          onDelete={() => onDelete(timer.id)}
        />
      ))}
    </div>
  )
}
