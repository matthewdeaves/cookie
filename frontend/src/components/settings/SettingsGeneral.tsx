import { useState } from 'react'
import { Key, Check, AlertCircle, Loader2, Github } from 'lucide-react'
import { toast } from 'sonner'
import { api, type AIStatus, type AIModel } from '../../api/client'
import { useAIStatus } from '../../contexts/AIStatusContext'
import { cn } from '../../lib/utils'

interface SettingsGeneralProps {
  aiStatus: AIStatus | null
  models: AIModel[]
  onAIStatusChange: (status: AIStatus) => void
  onModelsChange: (models: AIModel[]) => void
}

export default function SettingsGeneral({
  aiStatus,
  models,
  onAIStatusChange,
  onModelsChange,
}: SettingsGeneralProps) {
  const globalAIStatus = useAIStatus()
  const [apiKey, setApiKey] = useState('')
  const [testingKey, setTestingKey] = useState(false)
  const [savingKey, setSavingKey] = useState(false)

  const getModelName = (modelId: string) => {
    const model = models.find((m) => m.id === modelId)
    return model?.name || modelId
  }

  const handleTestApiKey = async () => {
    if (!apiKey.trim()) {
      toast.error('Please enter an API key')
      return
    }

    setTestingKey(true)
    try {
      const result = await api.ai.testApiKey(apiKey.trim())
      if (result.success) {
        toast.success(result.message)
      } else {
        toast.error(result.message)
      }
    } catch (error) {
      console.error('Failed to test API key:', error)
      toast.error('Failed to test API key')
    } finally {
      setTestingKey(false)
    }
  }

  const handleSaveApiKey = async () => {
    if (!apiKey.trim()) {
      toast.error('Please enter an API key')
      return
    }

    setSavingKey(true)
    try {
      const result = await api.ai.saveApiKey(apiKey.trim())
      if (result.success) {
        toast.success(result.message)
        setApiKey('')
        const statusData = await api.ai.status()
        onAIStatusChange(statusData)
        await globalAIStatus.refresh()
        const modelsData = await api.ai.models()
        onModelsChange(modelsData)
      } else {
        toast.error(result.message)
      }
    } catch (error) {
      console.error('Failed to save API key:', error)
      toast.error('Failed to save API key')
    } finally {
      setSavingKey(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* OpenRouter API */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="mb-4 text-lg font-medium text-foreground">OpenRouter API</h2>

        <div className="mb-4 flex items-center gap-2">
          <div
            className={cn(
              'h-2 w-2 rounded-full',
              aiStatus?.available
                ? 'bg-green-500'
                : aiStatus?.configured
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
            )}
          />
          <span className="text-sm text-muted-foreground">
            {aiStatus?.available
              ? 'Connected'
              : aiStatus?.configured
                ? 'Invalid key'
                : 'Not configured'}
          </span>
        </div>

        {aiStatus?.configured && !aiStatus?.valid && (
          <div className="mb-4 flex items-center gap-2 rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-3">
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-yellow-500" />
            <p className="text-sm text-yellow-600 dark:text-yellow-400">
              {aiStatus?.error ||
                'Your API key appears to be invalid or expired. Please update it.'}
            </p>
          </div>
        )}

        {aiStatus?.available && (
          <div className="mb-4 text-sm text-muted-foreground">
            Default model:{' '}
            <span className="font-medium text-foreground">
              {getModelName(aiStatus.default_model)}
            </span>
          </div>
        )}

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

      {/* About */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="mb-4 text-lg font-medium text-foreground">About</h2>
        <div className="space-y-2 text-sm text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>Version</span>
            <span className="font-medium text-foreground">1.0.0</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Source Code</span>
            <a
              href="https://github.com/matthewdeaves/cookie.git"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-primary hover:underline"
            >
              <Github className="h-4 w-4" />
              GitHub
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
