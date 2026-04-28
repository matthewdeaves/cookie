import { RefreshCw } from 'lucide-react'
import { usePullToRefresh } from '../hooks/usePullToRefresh'

export default function PullToRefresh() {
  const { pullDistance, isPulling, isReleasing, threshold } = usePullToRefresh()

  if (!isPulling && !isReleasing) return null

  const progress = Math.min(1, pullDistance / threshold)
  const willRefresh = pullDistance >= threshold
  const translateY = isReleasing ? 24 : Math.min(pullDistance * 0.6, 48)

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-x-0 top-0 z-50 flex justify-center"
      style={{ transform: `translateY(${translateY}px)`, transition: isReleasing ? 'transform 80ms ease-out' : 'none' }}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-background/95 shadow-md backdrop-blur">
        <RefreshCw
          className={isReleasing ? 'h-5 w-5 animate-spin text-primary' : 'h-5 w-5 text-foreground/70'}
          style={{ transform: isReleasing ? undefined : `rotate(${progress * 270}deg)`, opacity: 0.5 + progress * 0.5 }}
        />
      </div>
      <span className="sr-only">{willRefresh ? 'Release to refresh' : 'Pull to refresh'}</span>
    </div>
  )
}
