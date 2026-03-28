import { useState, useEffect, useCallback } from 'react'
import { api } from '../../api/client'
import type { PasskeyCredential } from '../../api/types'
import {
  prepareRegistrationOptions,
  serializeRegistrationCredential,
} from '../../lib/webauthn'

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Never'
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function SettingsPasskeys() {
  const [credentials, setCredentials] = useState<PasskeyCredential[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [adding, setAdding] = useState(false)

  const loadCredentials = useCallback(async () => {
    try {
      const data = await api.passkey.listCredentials()
      setCredentials(data.credentials)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load passkeys')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCredentials()
  }, [loadCredentials])

  async function handleAdd() {
    setError('')
    setAdding(true)

    try {
      const options = await api.passkey.addCredentialOptions()
      const publicKeyOptions = prepareRegistrationOptions(options)

      const credential = await navigator.credentials.create({
        publicKey: publicKeyOptions,
      })

      if (!credential) {
        setError('Adding passkey was cancelled.')
        return
      }

      await api.passkey.addCredentialVerify(
        serializeRegistrationCredential(credential as PublicKeyCredential)
      )

      await loadCredentials()
    } catch (err) {
      if (err instanceof DOMException && err.name === 'NotAllowedError') {
        setError('Adding passkey was cancelled.')
      } else {
        setError(err instanceof Error ? err.message : 'Failed to add passkey')
      }
    } finally {
      setAdding(false)
    }
  }

  async function handleDelete(credentialId: number) {
    if (!window.confirm('Are you sure you want to delete this passkey? This cannot be undone.')) {
      return
    }
    setError('')
    try {
      await api.passkey.deleteCredential(credentialId)
      await loadCredentials()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete passkey')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="mb-1 text-lg font-medium text-foreground">Manage Passkeys</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          {credentials.length} passkey{credentials.length !== 1 ? 's' : ''} registered
        </p>

        {error && (
          <div role="alert" className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-300">
            {error}
          </div>
        )}

        <div className="space-y-3">
          {credentials.map((cred) => (
            <div
              key={cred.id}
              className="flex items-center justify-between rounded-lg border border-input bg-background p-4"
            >
              <div>
                <div className="text-sm font-medium text-foreground">
                  Passkey #{cred.id}
                </div>
                <div className="text-xs text-muted-foreground">
                  Added {formatDate(cred.created_at)}
                </div>
                <div className="text-xs text-muted-foreground">
                  Last used: {formatDate(cred.last_used_at)}
                </div>
              </div>
              {cred.is_deletable && (
                <button
                  onClick={() => handleDelete(cred.id)}
                  className="rounded-md px-3 py-1 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                >
                  Delete
                </button>
              )}
            </div>
          ))}
        </div>

        <button
          onClick={handleAdd}
          disabled={adding}
          className="mt-4 w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50"
        >
          {adding ? 'Adding passkey...' : 'Add Passkey'}
        </button>
      </div>
    </div>
  )
}
