import { useState, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Register() {
  const { register } = useAuth()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [email, setEmail] = useState('')
  const [privacyAccepted, setPrivacyAccepted] = useState(false)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({})
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setFieldErrors({})
    setSubmitting(true)

    // Client-side validation
    if (password !== passwordConfirm) {
      setFieldErrors({ password_confirm: ['Passwords do not match'] })
      setSubmitting(false)
      return
    }

    try {
      const message = await register({
        username,
        password,
        password_confirm: passwordConfirm,
        email,
        privacy_accepted: privacyAccepted,
      })
      setSuccess(message)
    } catch (err) {
      const apiError = err as Error & { body?: Record<string, unknown> }
      const body = apiError.body
      if (body?.errors) {
        setFieldErrors(body.errors as Record<string, string[]>)
      } else if (body?.error) {
        setError(body.error as string)
      } else {
        setError(apiError.message || 'Registration failed')
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-4">
        <div className="w-full max-w-sm space-y-6 text-center">
          <h1 className="text-3xl font-bold text-foreground">Cookie</h1>
          <div className="rounded-md bg-green-50 p-4 text-green-800 dark:bg-green-900/20 dark:text-green-300">
            <p className="font-medium">Check your email</p>
            <p className="mt-1 text-sm">{success}</p>
          </div>
          <Link to="/login" className="inline-block text-sm font-medium text-primary hover:underline">
            Back to login
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-foreground">Cookie</h1>
          <p className="mt-1 text-sm text-muted-foreground">Create your account</p>
        </div>

        {error && (
          <div className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-foreground">
              Username
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {fieldErrors.username?.map((msg, i) => (
              <p key={i} className="mt-1 text-xs text-red-600">{msg}</p>
            ))}
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-foreground">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <p className="mt-1 text-xs text-muted-foreground">Used only for verification. Never stored.</p>
            {fieldErrors.email?.map((msg, i) => (
              <p key={i} className="mt-1 text-xs text-red-600">{msg}</p>
            ))}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-foreground">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {fieldErrors.password?.map((msg, i) => (
              <p key={i} className="mt-1 text-xs text-red-600">{msg}</p>
            ))}
          </div>

          <div>
            <label htmlFor="password_confirm" className="block text-sm font-medium text-foreground">
              Confirm password
            </label>
            <input
              id="password_confirm"
              type="password"
              autoComplete="new-password"
              required
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {fieldErrors.password_confirm?.map((msg, i) => (
              <p key={i} className="mt-1 text-xs text-red-600">{msg}</p>
            ))}
          </div>

          <div className="flex items-start gap-2">
            <input
              id="privacy"
              type="checkbox"
              checked={privacyAccepted}
              onChange={(e) => setPrivacyAccepted(e.target.checked)}
              className="mt-1 h-4 w-4 rounded border-input"
            />
            <label htmlFor="privacy" className="text-sm text-muted-foreground">
              I have read and accept the{' '}
              <a href="/privacy/" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                privacy policy
              </a>
            </label>
          </div>
          {fieldErrors.privacy_accepted?.map((msg, i) => (
            <p key={i} className="text-xs text-red-600">{msg}</p>
          ))}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50"
          >
            {submitting ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
