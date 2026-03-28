import { useState, FormEvent } from 'react'
import { api } from '../api/client'

export default function DeviceCodeEntry() {
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      await api.device.authorize(code)
      setSuccess(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authorization failed')
    } finally {
      setSubmitting(false)
    }
  }

  if (success) {
    return (
      <div className="rounded-md bg-green-50 p-4 text-center text-sm text-green-800 dark:bg-green-900/20 dark:text-green-300">
        Device authorized successfully! The other device should now be connected.
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-300">
          {error}
        </div>
      )}

      <div>
        <label htmlFor="device-code" className="block text-sm font-medium text-foreground">
          Enter the code shown on the other device
        </label>
        <input
          id="device-code"
          type="text"
          maxLength={6}
          required
          autoComplete="off"
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          placeholder="ABC123"
          className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-center font-mono text-2xl tracking-widest text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </div>

      <button
        type="submit"
        disabled={submitting || code.length < 6}
        className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50"
      >
        {submitting ? 'Authorizing...' : 'Authorize Device'}
      </button>
    </form>
  )
}
