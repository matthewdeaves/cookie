import { Key, Check, Loader2 } from 'lucide-react'
import type { AIStatus, AIModel } from '../../api/client'
import { useAPIKeyHandlers } from '../../hooks/useAPIKeyHandlers'
import AIStatusDisplay from './AIStatusDisplay'

interface APIKeySectionProps {
  aiStatus: AIStatus | null
  models: AIModel[]
  onAIStatusChange: (status: AIStatus) => void
  onModelsChange: (models: AIModel[]) => void
}

export default function APIKeySection({
  aiStatus,
  models,
  onAIStatusChange,
  onModelsChange,
}: APIKeySectionProps) {
  const {
    apiKey,
    setApiKey,
    testingKey,
    savingKey,
    handleTestApiKey,
    handleSaveApiKey,
  } = useAPIKeyHandlers({ onAIStatusChange, onModelsChange })

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h2 className="mb-4 text-lg font-medium text-foreground">OpenRouter API</h2>

      <AIStatusDisplay aiStatus={aiStatus} models={models} />

      <div className="space-y-3">
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-foreground">
            {aiStatus?.available ? 'Update API Key' : 'API Key'}
          </span>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-or-v1-..."
            className="w-full rounded-lg border border-border bg-input-background px-3 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </label>

        <div className="flex gap-2">
          <button
            onClick={handleTestApiKey}
            disabled={testingKey || !apiKey.trim()}
            className="flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            {testingKey ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Check className="h-4 w-4" />
            )}
            Test Key
          </button>
          <button
            onClick={handleSaveApiKey}
            disabled={savingKey || !apiKey.trim()}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {savingKey ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Key className="h-4 w-4" />
            )}
            Save Key
          </button>
        </div>
      </div>

      <p className="mt-4 text-sm text-muted-foreground">
        Get your API key from{' '}
        <a
          href="https://openrouter.ai/keys"
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:underline"
        >
          openrouter.ai/keys
        </a>
      </p>
    </div>
  )
}
