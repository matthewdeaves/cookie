import { Timer as TimerIcon, ChevronUp, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import type { UseTimersReturn } from '../hooks/useTimers'
import { detectTimes } from '../hooks/useTimers'
import { api } from '../api/client'
import { cn } from '../lib/utils'
import QuickTimerButtons from './QuickTimerButtons'
import DetectedTimers from './DetectedTimers'
import TimerList from './TimerList'

interface TimerPanelProps {
  timers: UseTimersReturn
  instructionText?: string
  aiAvailable?: boolean
  isLandscape?: boolean
}

const QUICK_TIMERS = [
  { label: '5 min', duration: 5 * 60 },
  { label: '10 min', duration: 10 * 60 },
  { label: '15 min', duration: 15 * 60 },
]

function formatDetectedTime(seconds: number): string {
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

interface TimerPanelHeaderProps {
  expanded: boolean
  timerCount: number
  activeCount: number
  isLandscape: boolean
  onToggle: () => void
}

function TimerPanelHeader({ expanded, timerCount, activeCount, isLandscape, onToggle }: TimerPanelHeaderProps) {
  return (
    <button
      onClick={isLandscape ? undefined : onToggle}
      className={cn(
        'flex w-full shrink-0 items-center justify-between px-4 py-3',
        !isLandscape && 'cursor-pointer',
      )}
    >
      <div className="flex items-center gap-2">
        <TimerIcon className="h-5 w-5 text-primary" />
        <span className="font-medium text-foreground">Timers</span>
        {timerCount > 0 && (
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            {timerCount}
            {activeCount > 0 && (
              <span className="text-primary"> ({activeCount} active)</span>
            )}
          </span>
        )}
      </div>
      {!isLandscape && (
        expanded ? (
          <ChevronDown className="h-5 w-5 text-muted-foreground" />
        ) : (
          <ChevronUp className="h-5 w-5 text-muted-foreground" />
        )
      )}
    </button>
  )
}

export default function TimerPanel({ timers, instructionText, aiAvailable = false, isLandscape = false }: TimerPanelProps) {
  const [expanded, setExpanded] = useState(true)
  const [loadingTimerId, setLoadingTimerId] = useState<string | null>(null)

  const detectedTimes = instructionText ? detectTimes(instructionText) : []
  const showContent = isLandscape || expanded

  const handleAddTimer = async (id: string, fallbackLabel: string, duration: number) => {
    const durationMinutes = Math.ceil(duration / 60)

    if (aiAvailable && instructionText) {
      setLoadingTimerId(id)
      try {
        const response = await api.ai.timerName(instructionText, durationMinutes)
        timers.addTimer(response.label, duration)
      } catch {
        timers.addTimer(fallbackLabel, duration)
      } finally {
        setLoadingTimerId(null)
      }
    } else {
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
    <div
      className={cn(
        'flex flex-col bg-card',
        isLandscape
          ? 'min-h-0 flex-[2] overflow-hidden border-l border-border'
          : 'max-h-[45vh] shrink-0 border-t border-border',
      )}
    >
      <TimerPanelHeader
        expanded={showContent}
        timerCount={timers.timers.length}
        activeCount={activeTimerCount}
        isLandscape={isLandscape}
        onToggle={() => setExpanded(!expanded)}
      />
      {showContent && (
        <div
          className={cn(
            'space-y-4 px-4 pb-4',
            isLandscape && 'flex-1 overflow-y-auto',
          )}
        >
          <QuickTimerButtons
            quickTimers={QUICK_TIMERS}
            loadingTimerId={loadingTimerId}
            aiAvailable={aiAvailable}
            instructionText={instructionText}
            onAdd={handleAddQuickTimer}
          />
          <DetectedTimers
            detectedTimes={detectedTimes}
            loadingTimerId={loadingTimerId}
            formatTime={formatDetectedTime}
            onAdd={handleAddDetectedTimer}
          />
          <TimerList
            timers={timers.timers}
            onToggle={timers.toggleTimer}
            onReset={timers.resetTimer}
            onDelete={timers.deleteTimer}
          />
        </div>
      )}
    </div>
  )
}
