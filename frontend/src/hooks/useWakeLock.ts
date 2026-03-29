import { useEffect, useRef, useCallback } from 'react'
import {
  createSilentVideo,
  requestNativeWakeLock,
  releaseNativeWakeLock,
} from './wakeLockUtils'

/**
 * useWakeLock - Prevents the screen from locking while active
 *
 * Uses the Screen Wake Lock API (iOS 16.4+, Chrome 84+) with a silent video
 * fallback for older browsers.
 *
 * @param enabled - Whether wake lock should be active (default: true)
 */
export function useWakeLock(enabled: boolean = true): void {
  const wakeLockRef = useRef<WakeLockSentinel | null>(null)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const usingFallbackRef = useRef(false)

  const startVideoFallback = useCallback(() => {
    if (videoRef.current) return
    const video = createSilentVideo()
    document.body.appendChild(video)
    videoRef.current = video
    video.play().catch(() => {})
    usingFallbackRef.current = true
  }, [])

  const stopVideoFallback = useCallback(() => {
    if (videoRef.current) {
      videoRef.current.pause()
      videoRef.current.remove()
      videoRef.current = null
    }
    usingFallbackRef.current = false
  }, [])

  useEffect(() => {
    if (!enabled) {
      releaseNativeWakeLock(wakeLockRef.current)
      wakeLockRef.current = null
      stopVideoFallback()
      return
    }

    let mounted = true

    const enableWakeLock = async () => {
      const sentinel = await requestNativeWakeLock()
      if (sentinel) {
        wakeLockRef.current = sentinel
        sentinel.addEventListener('release', () => {
          wakeLockRef.current = null
        })
      } else if (mounted) {
        startVideoFallback()
      }
    }

    enableWakeLock()

    const handleVisibilityChange = async () => {
      if (document.visibilityState === 'visible' && mounted && enabled) {
        if (!usingFallbackRef.current) {
          const sentinel = await requestNativeWakeLock()
          if (sentinel) {
            wakeLockRef.current = sentinel
            sentinel.addEventListener('release', () => {
              wakeLockRef.current = null
            })
          }
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      mounted = false
      releaseNativeWakeLock(wakeLockRef.current)
      wakeLockRef.current = null
      stopVideoFallback()
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [enabled, startVideoFallback, stopVideoFallback])
}
