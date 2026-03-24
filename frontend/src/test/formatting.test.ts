import { describe, it, expect } from 'vitest'
import { formatTime } from '../lib/formatting'

describe('formatTime', () => {
  it('returns null for null input', () => {
    expect(formatTime(null)).toBeNull()
  })

  it('returns null for undefined input', () => {
    expect(formatTime(undefined)).toBeNull()
  })

  it('returns null for zero', () => {
    expect(formatTime(0)).toBeNull()
  })

  it('formats minutes under 60 as "X min"', () => {
    expect(formatTime(1)).toBe('1 min')
    expect(formatTime(30)).toBe('30 min')
    expect(formatTime(59)).toBe('59 min')
  })

  it('formats exactly 60 minutes as "1h"', () => {
    expect(formatTime(60)).toBe('1h')
  })

  it('formats hours with remaining minutes as "Xh Ym"', () => {
    expect(formatTime(90)).toBe('1h 30m')
    expect(formatTime(150)).toBe('2h 30m')
    expect(formatTime(61)).toBe('1h 1m')
  })

  it('formats full hours as "Xh"', () => {
    expect(formatTime(120)).toBe('2h')
    expect(formatTime(180)).toBe('3h')
    expect(formatTime(240)).toBe('4h')
  })
})
