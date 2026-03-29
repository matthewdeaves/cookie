import usePasskeys from '../../hooks/usePasskeys'
import PasskeyItem from './PasskeyItem'

export default function SettingsPasskeys() {
  const { credentials, loading, error, adding, handleAdd, handleDelete } = usePasskeys()

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
            <PasskeyItem
              key={cred.id}
              id={cred.id}
              createdAt={cred.created_at}
              lastUsedAt={cred.last_used_at}
              isDeletable={cred.is_deletable}
              onDelete={handleDelete}
            />
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
