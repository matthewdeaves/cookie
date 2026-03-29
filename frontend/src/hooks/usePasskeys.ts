import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import type { PasskeyCredential } from '../api/types'
import {
  prepareRegistrationOptions,
  serializeRegistrationCredential,
} from '../lib/webauthn'

export default function usePasskeys() {
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

  return { credentials, loading, error, adding, handleAdd, handleDelete }
}
