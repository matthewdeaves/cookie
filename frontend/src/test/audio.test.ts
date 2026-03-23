import { describe, it, expect, vi, beforeEach } from 'vitest'


// Mock AudioContext
const mockResume = vi.fn(() => Promise.resolve())
const mockCreateBuffer = vi.fn(() => ({}))
const mockCreateBufferSource = vi.fn(() => ({
  buffer: null,
  connect: vi.fn(),
  start: vi.fn(),
}))
const mockCreateOscillator = vi.fn(() => ({
  type: 'sine',
  frequency: { setValueAtTime: vi.fn() },
  connect: vi.fn(),
  start: vi.fn(),
  stop: vi.fn(),
}))
const mockCreateGain = vi.fn(() => ({
  gain: {
    setValueAtTime: vi.fn(),
    linearRampToValueAtTime: vi.fn(),
  },
  connect: vi.fn(),
}))

class MockAudioContext {
  state = 'running'
  currentTime = 0
  destination = {}
  resume = mockResume
  createBuffer = mockCreateBuffer
  createBufferSource = mockCreateBufferSource
  createOscillator = mockCreateOscillator
  createGain = mockCreateGain
}

describe('audio', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset module to clear singleton state
    vi.resetModules()
    // Set up window.AudioContext
    Object.defineProperty(window, 'AudioContext', {
      value: MockAudioContext,
      writable: true,
      configurable: true,
    })
  })

  it('unlockAudio does not throw', async () => {
    const { unlockAudio } = await import('../lib/audio')
    expect(() => unlockAudio()).not.toThrow()
  })

  it('playTimerAlert does not throw', async () => {
    const { unlockAudio, playTimerAlert } = await import('../lib/audio')
    unlockAudio() // Initialize audio context
    expect(() => playTimerAlert()).not.toThrow()
  })

  it('unlockAudio creates buffer source', async () => {
    const { unlockAudio } = await import('../lib/audio')
    unlockAudio()
    expect(mockCreateBufferSource).toHaveBeenCalled()
  })

  it('unlockAudio is idempotent (second call is no-op)', async () => {
    const { unlockAudio } = await import('../lib/audio')
    unlockAudio()
    const callCount = mockCreateBufferSource.mock.calls.length
    unlockAudio()
    expect(mockCreateBufferSource.mock.calls.length).toBe(callCount)
  })

  it('playTimerAlert creates oscillators for tone pattern', async () => {
    const { unlockAudio, playTimerAlert } = await import('../lib/audio')
    unlockAudio()
    playTimerAlert()
    // Should create 3 oscillators (3 tones)
    expect(mockCreateOscillator).toHaveBeenCalledTimes(3)
  })

  it('handles missing AudioContext gracefully', async () => {
    Object.defineProperty(window, 'AudioContext', {
      value: undefined,
      writable: true,
      configurable: true,
    })
    // Also remove webkit fallback
    const win = window as unknown as Record<string, unknown>
    delete win.webkitAudioContext

    const { unlockAudio, playTimerAlert } = await import('../lib/audio')
    expect(() => unlockAudio()).not.toThrow()
    expect(() => playTimerAlert()).not.toThrow()
  })
})
