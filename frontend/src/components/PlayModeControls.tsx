import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '../lib/utils'

interface PlayModeControlsProps {
  currentStep: number
  totalSteps: number
  instructions: string[]
  onPrevious: () => void
  onNext: () => void
  onStepSelect: (idx: number) => void
}

export default function PlayModeControls({
  currentStep,
  totalSteps,
  instructions,
  onPrevious,
  onNext,
  onStepSelect,
}: PlayModeControlsProps) {
  return (
    <div className="flex items-center justify-between border-t border-border px-4 py-4">
      <button
        onClick={onPrevious}
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
            onClick={() => onStepSelect(idx)}
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
        onClick={onNext}
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
  )
}
