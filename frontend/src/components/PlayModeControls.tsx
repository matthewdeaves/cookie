import { cn } from '../lib/utils'

interface PlayModeControlsProps {
  currentStep: number
  totalSteps: number
  onPrevious: () => void
  onNext: () => void
}

export default function PlayModeControls({
  currentStep,
  totalSteps,
  onPrevious,
  onNext,
}: PlayModeControlsProps) {
  const isFirst = currentStep === 0
  const isLast = currentStep === totalSteps - 1

  return (
    <div className="flex shrink-0 gap-3 px-4 pb-4">
      <button
        onClick={onPrevious}
        disabled={isFirst}
        className={cn(
          'flex h-14 flex-1 items-center justify-center gap-2 rounded-xl text-base font-semibold transition-colors',
          isFirst
            ? 'bg-muted text-muted-foreground opacity-25'
            : 'bg-muted text-foreground active:bg-muted/70',
        )}
      >
        <span className="text-lg leading-none" aria-hidden="true">&larr;</span>
        Previous
      </button>

      <button
        onClick={onNext}
        disabled={isLast}
        className={cn(
          'flex h-14 flex-1 items-center justify-center gap-2 rounded-xl text-base font-semibold transition-colors',
          isLast
            ? 'bg-primary text-primary-foreground opacity-25'
            : 'bg-primary text-primary-foreground active:bg-primary/80',
        )}
      >
        Next
        <span className="text-lg leading-none" aria-hidden="true">&rarr;</span>
      </button>
    </div>
  )
}
