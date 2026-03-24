/**
 * Tests for Legacy utility functions (ES5, iOS 9 compatible)
 *
 * These tests verify the Cookie.utils and Cookie.TimeDetect modules
 * that are used in the legacy frontend.
 */
import { describe, it, expect, beforeAll } from 'vitest'
import fs from 'fs'
import path from 'path'
import { JSDOM } from 'jsdom'

// Load the legacy scripts from the legacy frontend
const legacyJsDir = path.resolve(__dirname, '../../../apps/legacy/static/legacy/js')
const utilsCode = fs.readFileSync(
  path.join(legacyJsDir, 'utils.js'),
  'utf-8'
)
const timeDetectCode = fs.readFileSync(
  path.join(legacyJsDir, 'time-detect.js'),
  'utf-8'
)

// Extend window interface for Cookie namespace
declare global {
  interface Window {
    Cookie: {
      utils: {
        escapeHtml: (str: string) => string
        formatTime: (minutes: number | null | undefined) => string | null
        truncate: (str: string, length: number) => string
        formatNumber: (num: number | null | undefined) => string
        escapeSelector: (str: string) => string
        formatRelativeTime: (dateStr: string | null) => string
        formatDate: (dateStr: string | null) => string
        parseDate: (dateStr: string | null) => Date
        showElement: (el: HTMLElement | null) => void
        hideElement: (el: HTMLElement | null) => void
      }
      TimeDetect: {
        detect: (text: string) => number[]
        format: (seconds: number) => string
        hasTime: (text: string) => boolean
      }
    }
  }
}

describe('Cookie.utils', () => {
  let dom: JSDOM
  let window: Window

  beforeAll(() => {
    // Create a fresh JSDOM instance and load scripts
    dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
      runScripts: 'dangerously',
    })
    window = dom.window as unknown as Window

    // Execute the legacy scripts in the jsdom context
    const script1 = dom.window.document.createElement('script')
    script1.textContent = utilsCode
    dom.window.document.body.appendChild(script1)

    const script2 = dom.window.document.createElement('script')
    script2.textContent = timeDetectCode
    dom.window.document.body.appendChild(script2)
  })

  describe('escapeHtml', () => {
    it('escapes HTML special characters', () => {
      expect(window.Cookie.utils.escapeHtml('<script>alert("xss")</script>')).toBe(
        '&lt;script&gt;alert("xss")&lt;/script&gt;'
      )
    })

    it('escapes ampersands', () => {
      expect(window.Cookie.utils.escapeHtml('foo & bar')).toBe('foo &amp; bar')
    })

    it('returns empty string for falsy input', () => {
      expect(window.Cookie.utils.escapeHtml('')).toBe('')
      expect(window.Cookie.utils.escapeHtml(null as unknown as string)).toBe('')
    })

    it('handles normal text unchanged', () => {
      expect(window.Cookie.utils.escapeHtml('Hello World')).toBe('Hello World')
    })
  })

  describe('formatTime', () => {
    it('formats minutes under 60', () => {
      expect(window.Cookie.utils.formatTime(45)).toBe('45 min')
      expect(window.Cookie.utils.formatTime(1)).toBe('1 min')
    })

    it('formats hours without remainder', () => {
      expect(window.Cookie.utils.formatTime(60)).toBe('1h')
      expect(window.Cookie.utils.formatTime(120)).toBe('2h')
    })

    it('formats hours with remainder', () => {
      expect(window.Cookie.utils.formatTime(90)).toBe('1h 30m')
      expect(window.Cookie.utils.formatTime(150)).toBe('2h 30m')
    })

    it('returns null for falsy input', () => {
      expect(window.Cookie.utils.formatTime(0)).toBe(null)
      expect(window.Cookie.utils.formatTime(null)).toBe(null)
      expect(window.Cookie.utils.formatTime(undefined)).toBe(null)
    })

    it('handles string input by parsing as integer', () => {
      expect(window.Cookie.utils.formatTime('45' as unknown as number)).toBe('45 min')
    })
  })

  describe('truncate', () => {
    it('truncates long strings with ellipsis', () => {
      expect(window.Cookie.utils.truncate('Hello World', 5)).toBe('Hello...')
    })

    it('returns short strings unchanged', () => {
      expect(window.Cookie.utils.truncate('Hi', 10)).toBe('Hi')
    })

    it('returns empty string for falsy input', () => {
      expect(window.Cookie.utils.truncate('', 10)).toBe('')
      expect(window.Cookie.utils.truncate(null as unknown as string, 10)).toBe('')
    })
  })

  describe('formatNumber', () => {
    it('formats thousands with commas', () => {
      expect(window.Cookie.utils.formatNumber(1234567)).toBe('1,234,567')
      expect(window.Cookie.utils.formatNumber(1000)).toBe('1,000')
    })

    it('handles small numbers without commas', () => {
      expect(window.Cookie.utils.formatNumber(999)).toBe('999')
      expect(window.Cookie.utils.formatNumber(0)).toBe('0')
    })

    it('returns empty string for falsy input (except 0)', () => {
      expect(window.Cookie.utils.formatNumber(null)).toBe('')
      expect(window.Cookie.utils.formatNumber(undefined)).toBe('')
    })
  })

  describe('escapeSelector', () => {
    it('escapes CSS special characters', () => {
      expect(window.Cookie.utils.escapeSelector('foo[bar]')).toBe('foo\\[bar\\]')
      expect(window.Cookie.utils.escapeSelector('a.b#c')).toBe('a\\.b\\#c')
    })

    it('handles strings without special characters', () => {
      expect(window.Cookie.utils.escapeSelector('hello-world_123')).toBe('hello-world_123')
    })

    it('returns empty string for falsy input', () => {
      expect(window.Cookie.utils.escapeSelector('')).toBe('')
    })
  })

  describe('parseDate', () => {
    it('parses ISO date strings', () => {
      const date = window.Cookie.utils.parseDate('2026-01-15T10:30:00.000Z')
      // Check it's a valid date by verifying getTime exists and returns a number
      expect(typeof date.getTime).toBe('function')
      expect(isNaN(date.getTime())).toBe(false)
      expect(date.getFullYear()).toBe(2026)
      expect(date.getMonth()).toBe(0) // January
      expect(date.getDate()).toBe(15)
    })

    it('handles dates with timezone offset', () => {
      const date = window.Cookie.utils.parseDate('2026-01-09T09:18:29.135626+00:00')
      // Check it's a valid date object
      expect(typeof date.getTime).toBe('function')
      expect(isNaN(date.getTime())).toBe(false)
    })

    it('returns invalid date for null input', () => {
      const date = window.Cookie.utils.parseDate(null)
      expect(isNaN(date.getTime())).toBe(true)
    })
  })

  describe('showElement / hideElement', () => {
    it('removes hidden class when showing', () => {
      const el = dom.window.document.createElement('div')
      el.classList.add('hidden')
      window.Cookie.utils.showElement(el)
      expect(el.classList.contains('hidden')).toBe(false)
    })

    it('adds hidden class when hiding', () => {
      const el = dom.window.document.createElement('div')
      window.Cookie.utils.hideElement(el)
      expect(el.classList.contains('hidden')).toBe(true)
    })

    it('handles null elements gracefully', () => {
      // Should not throw
      expect(() => window.Cookie.utils.showElement(null)).not.toThrow()
      expect(() => window.Cookie.utils.hideElement(null)).not.toThrow()
    })
  })
})

describe('Cookie.TimeDetect', () => {
  let dom: JSDOM
  let window: Window

  beforeAll(() => {
    dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
      runScripts: 'dangerously',
    })
    window = dom.window as unknown as Window

    const script1 = dom.window.document.createElement('script')
    script1.textContent = utilsCode
    dom.window.document.body.appendChild(script1)

    const script2 = dom.window.document.createElement('script')
    script2.textContent = timeDetectCode
    dom.window.document.body.appendChild(script2)
  })

  describe('detect', () => {
    it('detects minutes in various formats', () => {
      expect(window.Cookie.TimeDetect.detect('15 minutes')).toEqual([900])
      expect(window.Cookie.TimeDetect.detect('15 min')).toEqual([900])
      expect(window.Cookie.TimeDetect.detect('15m')).toEqual([900])
    })

    it('detects hours in various formats', () => {
      expect(window.Cookie.TimeDetect.detect('2 hours')).toEqual([7200])
      expect(window.Cookie.TimeDetect.detect('2 hr')).toEqual([7200])
      expect(window.Cookie.TimeDetect.detect('2h')).toEqual([7200])
    })

    it('detects seconds in various formats', () => {
      expect(window.Cookie.TimeDetect.detect('30 seconds')).toEqual([30])
      expect(window.Cookie.TimeDetect.detect('30 sec')).toEqual([30])
      expect(window.Cookie.TimeDetect.detect('30s')).toEqual([30])
    })

    it('detects multiple time mentions', () => {
      const times = window.Cookie.TimeDetect.detect('Cook for 2 hours and rest for 15 minutes')
      expect(times).toContain(7200)
      expect(times).toContain(900)
    })

    it('returns empty array for text without times', () => {
      expect(window.Cookie.TimeDetect.detect('No time here')).toEqual([])
      expect(window.Cookie.TimeDetect.detect('')).toEqual([])
    })

    it('returns empty array for null input', () => {
      expect(window.Cookie.TimeDetect.detect(null as unknown as string)).toEqual([])
    })
  })

  describe('format', () => {
    it('formats seconds only', () => {
      expect(window.Cookie.TimeDetect.format(30)).toBe('30 sec')
    })

    it('formats minutes only', () => {
      expect(window.Cookie.TimeDetect.format(300)).toBe('5 min')
    })

    it('formats minutes and seconds', () => {
      expect(window.Cookie.TimeDetect.format(330)).toBe('5m 30s')
    })

    it('formats hours only', () => {
      expect(window.Cookie.TimeDetect.format(7200)).toBe('2h')
    })

    it('formats hours and minutes', () => {
      expect(window.Cookie.TimeDetect.format(7500)).toBe('2h 5m')
    })
  })

  describe('hasTime', () => {
    it('returns true when time is present', () => {
      expect(window.Cookie.TimeDetect.hasTime('Cook for 15 minutes')).toBe(true)
    })

    it('returns false when no time is present', () => {
      expect(window.Cookie.TimeDetect.hasTime('No time here')).toBe(false)
    })
  })
})
