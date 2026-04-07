import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { PasskeyCredential } from '../api/types'
import {
  prepareRegistrationOptions,
  serializeRegistrationCredential,
} from '../lib/webauthn'

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

interface PasskeyCardProps {
  credential: PasskeyCredential
  onDelete: (id: number) => void
}

interface PasskeyListProps {
  credentials: PasskeyCredential[]
  error: string
  adding: boolean
  onAdd: () => void
  onDelete: (id: number) => void
  onBack: () => void
}

function PasskeyList({ credentials, error, adding, onAdd, onDelete, onBack }: PasskeyListProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground">Manage Passkeys</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {credentials.length} passkey{credentials.length !== 1 ? 's' : ''} registered
          </p>
        </div>

        {error && (
          <div role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-300">
            {error}
          </div>
        )}

        <div className="space-y-3">
          {credentials.map((cred) => (
            <PasskeyCard key={cred.id} credential={cred} onDelete={onDelete} />
          ))}
        </div>

        <button
          onClick={onAdd}
          disabled={adding}
          className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50"
        >
          {adding ? 'Adding passkey...' : 'Add Passkey'}
        </button>

        <div className="text-center">
          <button
            onClick={onBack}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Go back
          </button>
        </div>
      </div>
    </div>
  )
}

function PasskeyCard({ credential, onDelete }: PasskeyCardProps) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-input bg-background p-4">
      <div>
        <div className="text-sm font-medium text-foreground">
          Passkey #{credential.id}
        </div>
        <div className="text-xs text-muted-foreground">
          Added {formatDate(credential.created_at)}
        </div>
        <div className="text-xs text-muted-foreground">
          Last used: {formatDate(credential.last_used_at)}
        </div>
      </div>
      {credential.is_deletable && (
        <button
          onClick={() => onDelete(credential.id)}
          className="rounded-md px-3 py-1 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
        >
          Delete
        </button>
      )}
    </div>
  )
}

export default function PasskeyManage() {
  const navigate = useNavigate()
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
    let cancelled = false
    ;(async () => {
      try {
        const data = await api.passkey.listCredentials()
        if (!cancelled) setCredentials(data.credentials)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load passkeys')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [])

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
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return (
    <PasskeyList
      credentials={credentials}
      error={error}
      adding={adding}
      onAdd={handleAdd}
      onDelete={handleDelete}
      onBack={() => navigate(-1)}
    />
  )
}
