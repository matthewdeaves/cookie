import { useState, useCallback, useEffect } from 'react'
import { X, ChevronLeft, ChevronRight } from 'lucide-react'
import { toast } from 'sonner'
import type { RecipeDetail } from '../api/client'
import { useTimers } from '../hooks/useTimers'
import TimerPanel from '../components/TimerPanel'
import { cn } from '../lib/utils'
import { unlockAudio, playTimerAlert } from '../lib/audio'

interface PlayModeProps {
  recipe: RecipeDetail
  onExit: () => void
}

export default function PlayMode({ recipe, onExit }: PlayModeProps) {
  const [currentStep, setCurrentStep] = useState(0)

  // Get instructions array
  const instructions =
    recipe.instructions.length > 0
      ? recipe.instructions
      : recipe.instructions_text
        ? recipe.instructions_text.split('\n').filter((s) => s.trim())
        : []

  const totalSteps = instructions.length

  // Timer completion handler
  const handleTimerComplete = useCallback(
    (timer: { label: string }) => {
      // Play audio alert
      playTimerAlert()

      // Show toast notification
      toast.success(`Timer complete: ${timer.label}`, {
        duration: 10000,
      })

      // Show browser notification (may include system sound)
      try {
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification('Timer Complete!', {
            body: timer.label,
            icon: '/favicon.ico',
          })
        }
      } catch {
        // Notification not supported or blocked
      }
    },
    []
  )

  const timers = useTimers(handleTimerComplete)

  // Request notification permission and unlock audio on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
    // Unlock audio for iOS (requires user interaction context)
    // This works because entering Play Mode requires a button click
    unlockAudio()
  }, [])

  const currentInstruction = instructions[currentStep] || ''
  const progress = totalSteps > 0 ? ((currentStep + 1) / totalSteps) * 100 : 0

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        handlePrevious()
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        handleNext()
      } else if (e.key === 'Escape') {
        onExit()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentStep, totalSteps, onExit])

  if (totalSteps === 0) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
        <p className="mb-4 text-center text-muted-foreground">
          No instructions available for this recipe.
        </p>
        <button
          onClick={onExit}
          className="rounded-lg bg-primary px-4 py-2 text-primary-foreground"
        >
          Exit
        </button>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Header with progress */}
      <div className="relative border-b border-border">
        {/* Progress bar */}
        <div className="h-1 bg-muted">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Header content */}
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex-1">
            <h1 className="line-clamp-1 text-sm font-medium text-foreground">
              {recipe.title}
            </h1>
            <p className="text-xs text-muted-foreground">
              Step {currentStep + 1} of {totalSteps}
            </p>
          </div>

          <button
            onClick={onExit}
            className="rounded-full bg-muted p-2 text-muted-foreground transition-colors hover:bg-muted/80"
            aria-label="Exit play mode"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex flex-1 flex-col">
        {/* Instruction display */}
        <div className="flex flex-1 items-center justify-center p-6">
          <div className="max-w-2xl text-center">
            {/* Step number */}
            <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-xl font-bold text-primary-foreground">
              {currentStep + 1}
            </div>

            {/* Instruction text */}
            <p className="text-xl leading-relaxed text-foreground sm:text-2xl">
              {currentInstruction}
            </p>
          </div>
        </div>

        {/* Navigation buttons */}
        <div className="flex items-center justify-between border-t border-border px-4 py-4">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className={cn(
              'flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-colors',
              currentStep === 0
                ? 'text-muted-foreground opacity-50'
                : 'bg-muted text-foreground hover:bg-muted/80'
            )}
          >
            <ChevronLeft className="h-5 w-5" />
            Previous
          </button>

          {/* Step indicators */}
          <div className="hidden gap-1.5 sm:flex">
            {instructions.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentStep(idx)}
                className={cn(
                  'h-2 w-2 rounded-full transition-all',
                  idx === currentStep
                    ? 'w-6 bg-primary'
                    : idx < currentStep
                      ? 'bg-primary/50'
                      : 'bg-muted'
                )}
                aria-label={`Go to step ${idx + 1}`}
              />
            ))}
          </div>

          <button
            onClick={handleNext}
            disabled={currentStep === totalSteps - 1}
            className={cn(
              'flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-colors',
              currentStep === totalSteps - 1
                ? 'text-muted-foreground opacity-50'
                : 'bg-primary text-primary-foreground hover:bg-primary/90'
            )}
          >
            Next
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>

        {/* Timer panel */}
        <TimerPanel timers={timers} instructionText={currentInstruction} />
      </div>
    </div>
  )
}
