import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import {
  prepareRegistrationOptions,
  serializeRegistrationCredential,
} from '../lib/webauthn'
import { useAuth } from '../contexts/AuthContext'

export default function PasskeyRegister() {
  const navigate = useNavigate()
  const { refreshSession } = useAuth()
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const webauthnSupported = typeof window !== 'undefined' && !!window.PublicKeyCredential

  async function handleRegister() {
    setError('')
    setSubmitting(true)

    try {
      const options = await api.passkey.registerOptions()
      const publicKeyOptions = prepareRegistrationOptions(options)

      const credential = await navigator.credentials.create({
        publicKey: publicKeyOptions,
      })

      if (!credential) {
        setError('Registration was cancelled.')
        return
      }

      await api.passkey.registerVerify(
        serializeRegistrationCredential(credential as PublicKeyCredential)
      )

      await refreshSession()
      navigate('/home')
    } catch (err) {
      if (err instanceof DOMException && err.name === 'NotAllowedError') {
        setError('Registration was cancelled.')
      } else {
        setError(err instanceof Error ? err.message : 'Registration failed')
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
          <p className="mt-1 text-sm text-muted-foreground">
            Create your account with a passkey
          </p>
        </div>

        {error && (
          <div role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-300">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {webauthnSupported ? (
            <>
              <p className="text-center text-sm text-muted-foreground">
                No username, email, or password needed. Your device's biometrics (Face ID, Touch ID, or
                PIN) will be your login.
              </p>

              <button
                onClick={handleRegister}
                disabled={submitting}
                className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50"
              >
                {submitting ? 'Creating account...' : 'Create Account'}
              </button>
            </>
          ) : (
            <p className="text-center text-sm text-muted-foreground">
              Your browser does not support passkeys. Please use a modern browser or pair this device
              using a code from another device.
            </p>
          )}
        </div>

        <div className="text-center text-sm text-muted-foreground">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-primary hover:underline">
              Sign In
            </Link>
          </p>
        </div>

        <div className="text-center">
          <a href="/privacy/" className="text-xs text-muted-foreground hover:text-foreground hover:underline">
            Privacy Policy
          </a>
        </div>
      </div>
    </div>
  )
}
