// Silent MP4 video (base64) - ~1KB, used as fallback for older browsers
// This is a minimal valid MP4 that plays silently, not a secret
const SILENT_VIDEO_BASE64 = // pragma: allowlist secret
  'data:video/mp4;base64,AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAAA' +
  'NBtZGF0AAACrgYF//+q3EXpvebZSLeWLNgg2SPu73gyNjQgLSBjb3JlIDE0MiByMjQ3OSBkZDc5' +
  'YTYxIC0gSC4yNjQvTVBFRy00IEFWQyBjb2RlYyAtIENvcHlsZWZ0IDIwMDMtMjAxNCAtIGh0dHA6' +
  'Ly93d3cudmlkZW9sYW4ub3JnL3gyNjQuaHRtbCAtIG9wdGlvbnM6IGNhYmFjPTEgcmVmPTMgZGVi' +
  'bG9jaz0xOjA6MCBhbmFseXNlPTB4MzoweDExMyBtZT1oZXggc3VibWU9NyBwc3k9MSBwc3lfcmQ9' +
  'MS4wMDowLjAwIG1peGVkX3JlZj0xIG1lX3JhbmdlPTE2IGNocm9tYV9tZT0xIHRyZWxsaXM9MDgg' +
  'OHg4ZGN0PTEgY3FtPTAgZGVhZHpvbmU9MjEsMTEgZmFzdF9wc2tpcD0xIGNocm9tYV9xcF9vZmZz' +
  'ZXQ9LTIgdGhyZWFkcz02IGxvb2thaGVhZF90aHJlYWRzPTEgc2xpY2VkX3RocmVhZHM9MCBucj0w' +
  'IGRlY2ltYXRlPTEgaW50ZXJsYWNlZD0wIGJsdXJheV9jb21wYXQ9MCBjb25zdHJhaW5lZF9pbnRy' +
  'YT0wIGJmcmFtZXM9MCB3ZWlnaHRwPTAga2V5aW50PTI1MCBrZXlpbnRfbWluPTI1IHNjZW5lY3V0' +
  'PTQwIGludHJhX3JlZnJlc2g9MCByY19sb29rYWhlYWQ9NDAgcmM9Y3JmIG1idHJlZT0xIGNyZj0y' +
  'My4wIHFjb21wPTAuNjAgcXBtaW49MCBxcG1heD02OSBxcHN0ZXA9NCBpcF9yYXRpbz0xLjQwIGFx' +
  'PTE6MS4wMACAAAAAwWWIhAAz//727L4FNf2f0JcRLMXaSnA+KqSAgHc0wAAAAwAAAwAAFgn0AAAA' +
  'AAIBAAADAAMAAAMAAAMAAFAAAAB4AAABpjgBAAZAAAABgQAAAEQQACAAAAAABIgYF//+l3EXpve' +
  'bZSLeWLNgg2SPu73gyNjQgLSBjb3JlIDE0MiByMjQ3OSBkZDc5YTYxIC0gSC4yNjQvTVBFRy00' +
  'IEFWQyBjb2RlYyAtIENvcHlsZWZ0IDIwMDMtMjAxNCAtIGh0dHA6Ly93d3cudmlkZW9sYW4ub3Jn' +
  'L3gyNjQuaHRtbCAtIG9wdGlvbnM6IGNhYmFjPTEgcmVmPTMAAAAUZnR5cGlzb20AAAIAaXNvbWlz' +
  'bzIAAAAIZnJlZQAAANhtZGF0AAACrgYF//+q3EXpvebZSLeWLNgg2SPu73gyAAAAFGZ0eXBpc29t' +
  'AAACAGlzb21pc28yAAAACGZyZWUAAADYbWRhdAAAAq4GBf//qtxF6b3m2Ui3lizYINkj7u94MgAA' +
  'AAhtb292AAAAbG12aGQAAAAAAAAAAAAAAAAAAAPoAAAAZAABAAABAAAAAAAAAAAAAAAAAQAAAAAAAA' +
  'AAAAAAAAAAAQAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAB' +
  'pHRyYWsAAABcdGtoZAAAAA8AAAAAAAAAAAAAAAEAAAAAAAAAZAAAAAAAAAAAAAAAAAAAAAABAAAAAA' +
  'AAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAJHbWRpYQAAACBtZGhkAAAA' +
  'AAAAAAAAAAAAAAA8AAAABQBVxAAAAAAALWhkbHIAAAAAAAAAAHZpZGUAAAAAAAAAAAAAAABWaWRl' +
  'b0hhbmRsZXIAAAAA3G1pbmYAAAAUdm1oZAAAAAEAAAAAAAAAAAAAACRkaW5mAAAAHGRyZWYAAAAA' +
  'AAAAAQAAAAx1cmwgAAAAAQAAAJxzdGJsAAAAmHN0c2QAAAAAAAAAAQAAAIhhdmMxAAAAAAAAAAEA' +
  'AAAAAAAAAAAAAAAAAAAAACgAIABIAAAASAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
  'AAAAAAAAAAAAGP//AAAAMWF2Y0MBZAAK/+EAGGdkAAqs2UHgloQAAAMABAAAAwAoPGDGWAEABmjr' +
  '48siwAAAABhzdHRzAAAAAAAAAAEAAAABAAAFAAAAABxzdHNjAAAAAAAAAAEAAAABAAAAAQAAAAEA' +
  'AAAUc3RzegAAAAAAAAL0AAAAAQAAABRzdGNvAAAAAAAAAAEAAAAwAAAAYnVkdGEAAABabWV0YQAA' +
  'AAAAAAAhaGRscgAAAAAAAAAAbWRpcmFwcGwAAAAAAAAAAAAAAAAtaWxzdAAAACWpdG9vAAAAHWRh' +
  'dGEAAAABAAAAAExhdmY1Ni40MC4xMDE='

/**
 * Creates a hidden video element for the wake lock video fallback.
 */
export function createSilentVideo(): HTMLVideoElement {
  const video = document.createElement('video')
  video.setAttribute('playsinline', '')
  video.setAttribute('muted', '')
  video.setAttribute('loop', '')
  video.muted = true
  video.src = SILENT_VIDEO_BASE64
  video.style.position = 'fixed'
  video.style.top = '-9999px'
  video.style.left = '-9999px'
  video.style.width = '1px'
  video.style.height = '1px'
  video.style.opacity = '0.01'
  return video
}

/**
 * Checks if the Screen Wake Lock API is available.
 */
export function isWakeLockSupported(): boolean {
  return 'wakeLock' in navigator
}

/**
 * Requests a native wake lock. Returns the sentinel on success, null on failure.
 */
export async function requestNativeWakeLock(): Promise<WakeLockSentinel | null> {
  if (!isWakeLockSupported()) return null
  try {
    return await navigator.wakeLock.request('screen')
  } catch {
    return null
  }
}

/**
 * Releases a wake lock sentinel, ignoring errors.
 */
export async function releaseNativeWakeLock(sentinel: WakeLockSentinel | null): Promise<void> {
  if (!sentinel) return
  try {
    await sentinel.release()
  } catch {
    // Ignore release errors
  }
}
