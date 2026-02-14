import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { toast } from 'sonner'
import { useAuth } from '../contexts/AuthContext'
import { useProfile } from '../contexts/ProfileContext'
import { cn } from '../lib/utils'

const PROFILE_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308',
  '#84cc16', '#22c55e', '#10b981', '#14b8a6',
  '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1',
  '#8b5cf6', '#a855f7', '#d946ef', '#ec4899',
]

export default function Register() {
  const navigate = useNavigate()
  const { settings, register } = useAuth()
  const { selectProfile } = useProfile()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [selectedColor, setSelectedColor] = useState(PROFILE_COLORS[11]) // Default to indigo
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateForm = (): string | null => {
    if (username.length < 3 || username.length > 30) {
      return 'Username must be 3-30 characters'
    }
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      return 'Username can only contain letters, numbers, and underscores'
    }
    if (password.length < 8) {
      return 'Password must be at least 8 characters'
    }
    // eslint-disable-next-line security/detect-possible-timing-attacks -- Form validation, not security-sensitive
    if (password !== passwordConfirm) {
      return 'Passwords do not match'
    }
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setLoading(true)

    try {
      const profile = await register(username, password, passwordConfirm, selectedColor)
      await selectProfile(profile)
      toast.success(`Welcome, ${profile.name}!`)
      navigate('/home')
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Registration failed')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-md text-center">
        {/* Title */}
        <h1 className="mb-2 text-4xl font-medium text-primary">
          {settings?.instance_name || 'Cookie'}
        </h1>
        <p className="mb-10 text-muted-foreground">Create your account</p>

        {/* Register form */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <form onSubmit={handleSubmit}>
            {error && (
              <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-destructive">
                {error}
              </div>
            )}

            <div className="mb-4">
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username (3-30 characters)"
                className="w-full rounded-lg border border-border bg-input-background px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                autoComplete="username"
                minLength={3}
                maxLength={30}
                pattern="[a-zA-Z0-9_]+"
                required
                autoFocus
              />
            </div>

            <div className="mb-4">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password (8+ characters)"
                className="w-full rounded-lg border border-border bg-input-background px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                autoComplete="new-password"
                minLength={8}
                required
              />
            </div>

            <div className="mb-4">
              <input
                type="password"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                placeholder="Confirm password"
                className="w-full rounded-lg border border-border bg-input-background px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                autoComplete="new-password"
                minLength={8}
                required
              />
            </div>

            {/* Color picker */}
            <div className="mb-6">
              <label className="mb-2 block text-sm text-muted-foreground">
                Choose an avatar color
              </label>
              <div className="flex flex-wrap justify-center gap-2">
                {PROFILE_COLORS.map((color) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => setSelectedColor(color)}
                    className={cn(
                      'h-10 w-10 rounded-full transition-transform hover:scale-110',
                      selectedColor === color && 'ring-2 ring-ring ring-offset-2 ring-offset-card'
                    )}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !username || !password || !passwordConfirm}
              className="w-full rounded-lg bg-primary px-4 py-3 text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <p className="mt-4 text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
