import { Timer as TimerIcon, Plus, ChevronUp, ChevronDown, Sparkles, Loader2 } from 'lucide-react'
import { useState } from 'react'
import type { UseTimersReturn } from '../hooks/useTimers'
import { detectTimes } from '../hooks/useTimers'
import TimerWidget from './TimerWidget'
import { api } from '../api/client'

interface TimerPanelProps {
  timers: UseTimersReturn
  instructionText?: string
  aiAvailable?: boolean
}

const QUICK_TIMERS = [
  { label: '+5 min', duration: 5 * 60 },
  { label: '+10 min', duration: 10 * 60 },
  { label: '+15 min', duration: 15 * 60 },
]

export default function TimerPanel({ timers, instructionText, aiAvailable = false }: TimerPanelProps) {
  const [expanded, setExpanded] = useState(true)
  const [loadingTimerId, setLoadingTimerId] = useState<string | null>(null)

  // Detect times from current instruction
  const detectedTimes = instructionText ? detectTimes(instructionText) : []

  const formatDetectedTime = (seconds: number): string => {
    if (seconds >= 3600) {
      const hrs = Math.floor(seconds / 3600)
      const mins = Math.floor((seconds % 3600) / 60)
      return mins > 0 ? `${hrs}h ${mins}m` : `${hrs}h`
    }
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    if (mins === 0) return `${secs}s`
    if (secs === 0) return `${mins} min`
    return `${mins}m ${secs}s`
  }

  const handleAddTimer = async (id: string, fallbackLabel: string, duration: number) => {
    const durationMinutes = Math.ceil(duration / 60)

    // If AI is available and we have instruction text, try to get an AI-generated name
    if (aiAvailable && instructionText) {
      setLoadingTimerId(id)
      try {
        const response = await api.ai.timerName(instructionText, durationMinutes)
        timers.addTimer(response.label, duration)
      } catch {
        // AI failed, use fallback
        timers.addTimer(fallbackLabel, duration)
      } finally {
        setLoadingTimerId(null)
      }
    } else {
      // No AI available, use fallback label
      timers.addTimer(fallbackLabel, duration)
    }
  }

  const handleAddQuickTimer = (label: string, duration: number, index: number) => {
    handleAddTimer(`quick-${index}`, label, duration)
  }

  const handleAddDetectedTimer = (seconds: number, index: number) => {
    handleAddTimer(`detected-${index}`, formatDetectedTime(seconds), seconds)
  }

  const activeTimerCount = timers.timers.filter((t) => t.isRunning).length

  return (
    <div className="border-t border-border bg-card">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3"
      >
        <div className="flex items-center gap-2">
          <TimerIcon className="h-5 w-5 text-primary" />
          <span className="font-medium text-foreground">Timers</span>
          {timers.timers.length > 0 && (
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              {timers.timers.length}
              {activeTimerCount > 0 && (
                <span className="text-primary"> ({activeTimerCount} active)</span>
              )}
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronDown className="h-5 w-5 text-muted-foreground" />
        ) : (
          <ChevronUp className="h-5 w-5 text-muted-foreground" />
        )}
      </button>

      {expanded && (
        <div className="space-y-4 px-4 pb-4">
          {/* Quick timer buttons */}
          <div className="flex flex-wrap gap-2">
            {QUICK_TIMERS.map(({ label, duration }, idx) => (
              <button
                key={label}
                onClick={() => handleAddQuickTimer(label.replace('+', '').trim(), duration, idx)}
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

          {/* Detected time suggestions */}
          {detectedTimes.length > 0 && (
            <div>
              <p className="mb-2 text-xs text-muted-foreground">
                Detected in this step:
              </p>
              <div className="flex flex-wrap gap-2">
                {detectedTimes.map((seconds, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleAddDetectedTimer(seconds, idx)}
                    disabled={loadingTimerId !== null}
                    className="flex items-center gap-1 rounded-full bg-primary/10 px-3 py-1.5 text-sm text-primary transition-colors hover:bg-primary/20 disabled:opacity-50"
                  >
                    {loadingTimerId === `detected-${idx}` ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Plus className="h-3 w-3" />
                    )}
                    {formatDetectedTime(seconds)}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Timer list */}
          {timers.timers.length > 0 ? (
            <div className="space-y-2">
              {timers.timers.map((timer) => (
                <TimerWidget
                  key={timer.id}
                  timer={timer}
                  onToggle={() => timers.toggleTimer(timer.id)}
                  onReset={() => timers.resetTimer(timer.id)}
                  onDelete={() => timers.deleteTimer(timer.id)}
                />
              ))}
            </div>
          ) : (
            <p className="text-center text-sm text-muted-foreground">
              No active timers. Add one above!
            </p>
          )}
        </div>
      )}
    </div>
  )
}
