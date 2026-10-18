// When the phone or iPad comes back after being locked or backgrounded for a few minutes, the page on screen is
// out of date and timers were frozen. Reload it once so nobody has to hit refresh. Never while cooking (the
// timers and the screen wake lock live in the page), typing, or with a dialog open.
const AWAY_MS = 3 * 60 * 1000

export function installStaleReload(): void {
  let hiddenAt: number | null = null
  const busy = (): boolean => {
    if (/\/play(\/|$)/.test(location.pathname)) return true
    const a = document.activeElement
    if (a && /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)) return true
    return !!document.querySelector('[role="dialog"], [aria-modal="true"]')
  }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      hiddenAt = Date.now()
      return
    }
    const away = hiddenAt === null ? 0 : Date.now() - hiddenAt
    hiddenAt = null
    if (away >= AWAY_MS && !busy()) location.reload()
  })
}
