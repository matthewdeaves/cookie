import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import {
  prepareAuthenticationOptions,
  serializeAuthenticationCredential,
} from '../lib/webauthn'
import { useAuth } from '../contexts/AuthContext'

export default function PasskeyLogin() {
  const navigate = useNavigate()
  const { refreshSession } = useAuth()
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const webauthnSupported = typeof window !== 'undefined' && !!window.PublicKeyCredential

  async function handleLogin() {
    setError('')
    setSubmitting(true)

    try {
      const options = await api.passkey.loginOptions()

      if (options && 'no_credentials' in options) {
        setError('No accounts exist yet. Create an account first.')
        return
      }

      const publicKeyOptions = prepareAuthenticationOptions(options)

      const credential = await navigator.credentials.get({
        publicKey: publicKeyOptions,
      })

      if (!credential) {
        setError('Sign in was cancelled.')
        return
      }

      await api.passkey.loginVerify(
        serializeAuthenticationCredential(credential as PublicKeyCredential)
      )

      await refreshSession()
      navigate('/home')
    } catch (err) {
      if (err instanceof DOMException && err.name === 'NotAllowedError') {
        setError('Sign in was cancelled.')
      } else {
        setError(err instanceof Error ? err.message : 'Sign in failed')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-foreground">Cookie</h1>
          <p className="mt-1 text-sm text-muted-foreground">Sign in with your passkey</p>
        </div>

        {error && (
          <div role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-300">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {webauthnSupported ? (
            <button
              onClick={handleLogin}
              disabled={submitting}
              className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting ? 'Signing in...' : 'Sign In'}
            </button>
          ) : (
            <p className="text-center text-sm text-muted-foreground">
              Your browser does not support passkeys. Please use a modern browser or pair this device
              using a code from another device.
            </p>
          )}
        </div>

        <div className="text-center text-sm text-muted-foreground">
          <p>
            Don't have an account?{' '}
            <Link to="/register" className="font-medium text-primary hover:underline">
              Create Account
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
