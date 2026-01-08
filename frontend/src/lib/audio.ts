/**
 * Audio utilities for timer completion alerts using Web Audio API
 * Uses programmatic tone generation (no external audio files needed)
 */

// Singleton AudioContext - created lazily on first use
let audioContext: AudioContext | null = null

// Track if audio has been unlocked (iOS requires user interaction)
let audioUnlocked = false

/**
 * Get or create the AudioContext singleton
 * Uses webkitAudioContext fallback for older Safari
 */
function getAudioContext(): AudioContext | null {
  if (audioContext) {
    return audioContext
  }

  try {
    const AudioContextClass =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext

    if (AudioContextClass) {
      audioContext = new AudioContextClass()
      return audioContext
    }
  } catch {
    // Web Audio API not supported
  }

  return null
}

/**
 * Unlock audio playback on iOS/Safari
 * Must be called from a user interaction event (click, touch)
 * Plays a silent buffer to enable future audio playback
 */
export function unlockAudio(): void {
  if (audioUnlocked) {
    return
  }

  const ctx = getAudioContext()
  if (!ctx) {
    return
  }

  // Resume suspended context (Chrome autoplay policy)
  if (ctx.state === 'suspended') {
    ctx.resume().catch(() => {
      // Ignore resume errors
    })
  }

  // Play a silent buffer to unlock iOS audio
  try {
    const buffer = ctx.createBuffer(1, 1, 22050)
    const source = ctx.createBufferSource()
    source.buffer = buffer
    source.connect(ctx.destination)
    source.start(0)
    audioUnlocked = true
  } catch {
    // Silent fail - audio may still work
  }
}

/**
 * Play a pleasant beep tone for timer completion
 * Generates a two-tone alert sound using Web Audio API
 */
export function playTimerAlert(): void {
  const ctx = getAudioContext()
  if (!ctx) {
    return
  }

  // Resume context if suspended
  if (ctx.state === 'suspended') {
    ctx.resume().catch(() => {})
  }

  try {
    const now = ctx.currentTime

    // Create a pleasant two-tone beep pattern
    // First beep: higher pitch
    playTone(ctx, 880, now, 0.15) // A5
    // Short pause
    // Second beep: same pitch
    playTone(ctx, 880, now + 0.2, 0.15) // A5
    // Third beep: lower pitch (confirmation)
    playTone(ctx, 660, now + 0.45, 0.25) // E5
  } catch {
    // Audio playback failed - silent fail
  }
}

/**
 * Play a single tone at the specified frequency
 */
function playTone(
  ctx: AudioContext,
  frequency: number,
  startTime: number,
  duration: number
): void {
  // Create oscillator for the tone
  const oscillator = ctx.createOscillator()
  oscillator.type = 'sine'
  oscillator.frequency.setValueAtTime(frequency, startTime)

  // Create gain node for volume envelope (prevents clicks)
  const gainNode = ctx.createGain()
  gainNode.gain.setValueAtTime(0, startTime)
  // Quick attack
  gainNode.gain.linearRampToValueAtTime(0.3, startTime + 0.01)
  // Sustain
  gainNode.gain.setValueAtTime(0.3, startTime + duration - 0.05)
  // Quick release (prevents click)
  gainNode.gain.linearRampToValueAtTime(0, startTime + duration)

  // Connect oscillator -> gain -> output
  oscillator.connect(gainNode)
  gainNode.connect(ctx.destination)

  // Schedule playback
  oscillator.start(startTime)
  oscillator.stop(startTime + duration)
}
