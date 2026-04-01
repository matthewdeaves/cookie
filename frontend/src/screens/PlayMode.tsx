import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { X } from 'lucide-react'
import { type RecipeDetail } from '../api/client'
import { useTimers } from '../hooks/useTimers'
import { useWakeLock } from '../hooks/useWakeLock'
import { usePlayModeData, useTimerComplete, getInstructions } from '../hooks/usePlayModeData'
import TimerPanel from '../components/TimerPanel'
import InstructionDisplay from '../components/InstructionDisplay'
import PlayModeControls from '../components/PlayModeControls'
import { unlockAudio } from '../lib/audio'
import { LoadingSpinner } from '../components/Skeletons'
import { cn } from '../lib/utils'

export default function PlayMode() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const recipeId = Number(id)

  const { recipe, loading, aiAvailable } = usePlayModeData(recipeId)
  const [currentStep, setCurrentStep] = useState(0)
  const isLandscape = useIsLandscape()

  const handleTimerComplete = useTimerComplete()
  const timers = useTimers(handleTimerComplete)
  useWakeLock()
  useNotificationSetup()

  const instructions = getInstructions(recipe)
  const totalSteps = instructions.length
  const currentInstruction = instructions[currentStep] || ''
  const progress = totalSteps > 0 ? ((currentStep + 1) / totalSteps) * 100 : 0

  const handlePrevious = () => {
    if (currentStep > 0) setCurrentStep(currentStep - 1)
  }
  const handleNext = () => {
    if (currentStep < totalSteps - 1) setCurrentStep(currentStep + 1)
  }
  const handleExit = () => navigate(-1)

  useKeyboardNav(handlePrevious, handleNext, handleExit, currentStep, totalSteps)

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <LoadingSpinner className="min-h-screen" />
      </div>
    )
  }

  if (!recipe || totalSteps === 0) {
    return <PlayModeEmpty hasRecipe={!!recipe} onExit={handleExit} />
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <PlayModeHeader recipe={recipe} currentStep={currentStep} totalSteps={totalSteps} progress={progress} onExit={handleExit} />
      <div className={cn('flex min-h-0 flex-1 overflow-hidden', isLandscape ? 'flex-row' : 'flex-col')}>
        <div className={cn('flex flex-col', isLandscape ? 'min-w-0 flex-[3]' : 'flex-1')}>
          <InstructionDisplay currentStep={currentStep} currentInstruction={currentInstruction} />
          <PlayModeControls
            currentStep={currentStep}
            totalSteps={totalSteps}
            onPrevious={handlePrevious}
            onNext={handleNext}
          />
        </div>
        <TimerPanel timers={timers} instructionText={currentInstruction} aiAvailable={aiAvailable} isLandscape={isLandscape} />
      </div>
    </div>
  )
}

function useNotificationSetup() {
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
    unlockAudio()
  }, [])
}

function useKeyboardNav(
  onPrevious: () => void,
  onNext: () => void,
  onExit: () => void,
  currentStep: number,
  totalSteps: number,
) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') onPrevious()
      else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') onNext()
      else if (e.key === 'Escape') onExit()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- handlers use currentStep/totalSteps from closure, re-bind when they change
  }, [currentStep, totalSteps])
}

function PlayModeEmpty({ hasRecipe, onExit }: { hasRecipe: boolean; onExit: () => void }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      <p className="mb-4 text-center text-muted-foreground">
        {hasRecipe ? 'No instructions available for this recipe.' : 'Recipe not found.'}
      </p>
      <button onClick={onExit} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">
        {hasRecipe ? 'Exit' : 'Go Back'}
      </button>
    </div>
  )
}

function getIsLandscape() {
  return typeof window !== 'undefined' && typeof window.matchMedia === 'function' && window.matchMedia('(orientation: landscape) and (min-width: 700px)').matches
}

function useIsLandscape() {
  const [isLandscape, setIsLandscape] = useState(getIsLandscape)
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return
    const mq = window.matchMedia('(orientation: landscape) and (min-width: 700px)')
    const handler = (e: MediaQueryListEvent) => setIsLandscape(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])
  return isLandscape
}

function PlayModeHeader({
  recipe,
  currentStep,
  totalSteps,
  progress,
  onExit,
}: {
  recipe: RecipeDetail
  currentStep: number
  totalSteps: number
  progress: number
  onExit: () => void
}) {
  return (
    <div className="relative shrink-0 border-b border-border">
      <div className="h-1 bg-muted">
        <div className="h-full bg-primary transition-all duration-300" style={{ width: `${progress}%` }} />
      </div>
      <div className="flex items-center justify-between px-4 py-2.5">
        <div className="min-w-0 flex-1">
          <h1 className="line-clamp-1 text-sm font-semibold text-foreground">{recipe.title}</h1>
          <p className="text-xs text-muted-foreground">Step {currentStep + 1} of {totalSteps}</p>
        </div>
        <button onClick={onExit} className="ml-3 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground transition-colors hover:bg-muted/80" aria-label="Exit play mode">
          <X className="h-5 w-5" />
        </button>
      </div>
    </div>
  )
}
