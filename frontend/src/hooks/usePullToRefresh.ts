import { useEffect, useRef, useState } from 'react'

const PULL_THRESHOLD = 70
const ACTIVATION_DISTANCE = 10
const MAX_PULL = PULL_THRESHOLD * 1.6

function isAtTop(): boolean {
  return window.scrollY <= 0 && document.documentElement.scrollTop <= 0
}

// If the user starts the gesture inside an internal scroller that is not at
// scrollTop 0, we must not hijack it for refresh — scrolling within the
// scroller stays a normal scroll.
function hasScrolledScrollableAncestor(target: Element | null): boolean {
  let node: Element | null = target
  while (node && node !== document.body && node !== document.documentElement) {
    const style = window.getComputedStyle(node)
    const overflowY = style.overflowY
    if ((overflowY === 'auto' || overflowY === 'scroll') && node.scrollHeight > node.clientHeight) {
      if (node.scrollTop > 0) return true
    }
    node = node.parentElement
  }
  return false
}

export interface PullToRefreshState {
  pullDistance: number
  isPulling: boolean
  isReleasing: boolean
  threshold: number
}

export function usePullToRefresh(): PullToRefreshState {
  const [pullDistance, setPullDistance] = useState(0)
  const [isPulling, setIsPulling] = useState(false)
  const [isReleasing, setIsReleasing] = useState(false)

  const startYRef = useRef<number | null>(null)
  const distanceRef = useRef(0)
  const pullingRef = useRef(false)

  useEffect(() => {
    function reset() {
      startYRef.current = null
      distanceRef.current = 0
      pullingRef.current = false
      setPullDistance(0)
      setIsPulling(false)
    }

    function onTouchStart(e: TouchEvent) {
      if (e.touches.length !== 1) return
      if (!isAtTop()) return
      const target = e.target as Element | null
      if (!target) return
      if (target.closest('input, textarea, select, [contenteditable="true"], [data-no-ptr]')) return
      if (hasScrolledScrollableAncestor(target)) return
      startYRef.current = e.touches[0].clientY
    }

    function onTouchMove(e: TouchEvent) {
      if (startYRef.current === null) return
      if (e.touches.length !== 1) {
        reset()
        return
      }
      const dy = e.touches[0].clientY - startYRef.current
      if (dy <= 0) {
        reset()
        return
      }
      if (dy < ACTIVATION_DISTANCE) return
      // Block native rubber-band so the indicator owns the gesture.
      if (e.cancelable) e.preventDefault()
      const visible = Math.min(dy, MAX_PULL)
      distanceRef.current = visible
      pullingRef.current = true
      setPullDistance(visible)
      setIsPulling(true)
    }

    function onTouchEnd() {
      if (pullingRef.current && distanceRef.current >= PULL_THRESHOLD) {
        // Show the "releasing" state briefly so the user gets visual confirmation
        // before the page reloads. setTimeout lets React paint one frame.
        setIsReleasing(true)
        setTimeout(() => window.location.reload(), 80)
        return
      }
      reset()
    }

    document.addEventListener('touchstart', onTouchStart, { passive: true })
    document.addEventListener('touchmove', onTouchMove, { passive: false })
    document.addEventListener('touchend', onTouchEnd, { passive: true })
    document.addEventListener('touchcancel', reset, { passive: true })

    return () => {
      document.removeEventListener('touchstart', onTouchStart)
      document.removeEventListener('touchmove', onTouchMove as EventListener)
      document.removeEventListener('touchend', onTouchEnd)
      document.removeEventListener('touchcancel', reset as EventListener)
    }
  }, [])

  return { pullDistance, isPulling, isReleasing, threshold: PULL_THRESHOLD }
}
