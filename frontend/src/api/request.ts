/**
 * HTTP transport shared by every API call: CSRF, error normalisation,
 * optional timeouts and transparent recovery of a lost home-mode session.
 */

const API_BASE = '/api'
const PROFILE_STORAGE_KEY = 'cookie_selected_profile_id'

/** Fired on `window` when a request is rejected with 401 and the session could not be restored. */
export const SESSION_LOST_EVENT = 'cookie:session-lost'

/** Error thrown for every failed API call. `status` is 0 for network failures and timeouts. */
export type ApiError = Error & {
  status: number
  body: Record<string, unknown> | null
  timedOut?: boolean
}

export interface RequestOptions extends RequestInit {
  /** Abort and fail with a timeout error after this many milliseconds. */
  timeoutMs?: number
}

function makeApiError(message: string, status: number, body: Record<string, unknown> | null = null): ApiError {
  const error = new Error(message) as ApiError
  error.status = status
  error.body = body
  return error
}

function getCsrfToken(): string {
  const value = '; ' + document.cookie
  const parts = value.split('; csrftoken=')
  if (parts.length === 2) return parts.pop()!.split(';').shift() || ''
  return ''
}

let sessionRestore: Promise<boolean> | null = null

function readStoredProfileId(): string | null {
  try {
    return localStorage.getItem(PROFILE_STORAGE_KEY)
  } catch {
    return null
  }
}

/**
 * Home mode keeps the chosen profile in the server session, which can expire or
 * be evicted (iOS clears cookies aggressively). The profile id is remembered in
 * localStorage, so quietly re-select it instead of failing the user's request.
 * Concurrent 401s share one restore attempt.
 */
function restoreHomeSession(): Promise<boolean> {
  if (sessionRestore) return sessionRestore
  const storedId = readStoredProfileId()
  if (!storedId || !/^\d+$/.test(storedId)) return Promise.resolve(false)
  sessionRestore = fetch(`${API_BASE}/profiles/${storedId}/select/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
  })
    .then((response) => response.ok)
    .catch(() => false)
    .finally(() => { sessionRestore = null })
  return sessionRestore
}

/** fetch() that turns network failures and timeouts into friendly ApiErrors. */
async function fetchWithTimeout(url: string, init: RequestInit, timeoutMs?: number): Promise<Response> {
  const controller = new AbortController()
  const callerSignal = init.signal
  const onCallerAbort = () => controller.abort()
  if (callerSignal) {
    if (callerSignal.aborted) controller.abort()
    else callerSignal.addEventListener('abort', onCallerAbort, { once: true })
  }
  let timedOut = false
  const timer = timeoutMs
    ? setTimeout(() => { timedOut = true; controller.abort() }, timeoutMs)
    : null

  try {
    return await fetch(url, { ...init, signal: controller.signal })
  } catch (err) {
    if (timedOut) {
      const error = makeApiError('The request took too long. Please try again.', 0)
      error.timedOut = true
      throw error
    }
    // Caller-initiated aborts propagate unchanged so they can be ignored.
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw makeApiError("Can't reach the server. Check your connection and try again.", 0)
  } finally {
    if (timer) clearTimeout(timer)
    callerSignal?.removeEventListener('abort', onCallerAbort)
  }
}

async function toApiError(response: Response): Promise<ApiError> {
  const errorText = await response.text()
  try {
    const errorBody = JSON.parse(errorText) as Record<string, unknown>
    const message = (errorBody.detail as string) || (errorBody.message as string)
    return makeApiError(message || `Request failed (${response.status})`, response.status, errorBody)
  } catch {
    // Non-JSON response (e.g. HTML error page) — never expose raw server
    // output to the user as it may leak internal details.
    return makeApiError(`Request failed (${response.status})`, response.status)
  }
}

async function send(endpoint: string, options: RequestOptions, retried: boolean): Promise<Response> {
  const { timeoutMs, ...init } = options
  const method = (init.method || 'GET').toUpperCase()
  const needsCsrf = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)

  const response = await fetchWithTimeout(
    `${API_BASE}${endpoint}`,
    {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(needsCsrf ? { 'X-CSRFToken': getCsrfToken() } : {}),
        ...init.headers,
      },
    },
    timeoutMs,
  )

  if (response.status === 401 && !endpoint.includes('/select/')) {
    if (!retried && (await restoreHomeSession())) {
      return send(endpoint, options, true)
    }
    window.dispatchEvent(new Event(SESSION_LOST_EVENT))
  }
  return response
}

export async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const response = await send(endpoint, options, false)
  if (!response.ok) throw await toApiError(response)
  // Handle 204 No Content
  if (response.status === 204) return null as T
  return response.json()
}
