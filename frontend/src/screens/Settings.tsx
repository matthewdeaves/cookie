import { useState, useEffect } from 'react'
import { ArrowLeft, Key, Bot, Check, X, ChevronDown, ChevronUp, AlertCircle, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  api,
  type AIPrompt,
  type AIModel,
  type AIStatus,
} from '../api/client'
import { cn } from '../lib/utils'
import { useAIStatus } from '../contexts/AIStatusContext'

interface SettingsProps {
  onBack: () => void
}

type Tab = 'api' | 'prompts'

export default function Settings({ onBack }: SettingsProps) {
  const [activeTab, setActiveTab] = useState<Tab>('api')
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null)
  const [prompts, setPrompts] = useState<AIPrompt[]>([])
  const [models, setModels] = useState<AIModel[]>([])
  const [loading, setLoading] = useState(true)
  const globalAIStatus = useAIStatus()

  // API Key state
  const [apiKey, setApiKey] = useState('')
  const [testingKey, setTestingKey] = useState(false)
  const [savingKey, setSavingKey] = useState(false)

  // Editing state
  const [editingPromptType, setEditingPromptType] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<{
    system_prompt: string
    user_prompt_template: string
    model: string
    is_active: boolean
  } | null>(null)
  const [savingPrompt, setSavingPrompt] = useState(false)

  // Expanded prompts for viewing
  const [expandedPrompts, setExpandedPrompts] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [statusData, promptsData, modelsData] = await Promise.all([
        api.ai.status(),
        api.ai.prompts.list(),
        api.ai.models(),
      ])
      setAiStatus(statusData)
      setPrompts(promptsData)
      setModels(modelsData)
    } catch (error) {
      console.error('Failed to load AI settings:', error)
      toast.error('Failed to load AI settings')
    } finally {
      setLoading(false)
    }
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
        // Reload local status
        const statusData = await api.ai.status()
        setAiStatus(statusData)
        // Also refresh global AI status context
        await globalAIStatus.refresh()
        // Reload models list (may have been empty if no key before)
        const modelsData = await api.ai.models()
        setModels(modelsData)
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

  const handleEditPrompt = (prompt: AIPrompt) => {
    setEditingPromptType(prompt.prompt_type)
    setEditForm({
      system_prompt: prompt.system_prompt,
      user_prompt_template: prompt.user_prompt_template,
      model: prompt.model,
      is_active: prompt.is_active,
    })
  }

  const handleCancelEdit = () => {
    setEditingPromptType(null)
    setEditForm(null)
  }

  const handleSavePrompt = async () => {
    if (!editingPromptType || !editForm) return

    setSavingPrompt(true)
    try {
      const updated = await api.ai.prompts.update(editingPromptType, editForm)
      setPrompts(prompts.map(p =>
        p.prompt_type === editingPromptType ? updated : p
      ))
      toast.success('Prompt saved successfully')
      setEditingPromptType(null)
      setEditForm(null)
    } catch (error) {
      console.error('Failed to save prompt:', error)
      // Try to parse error message from server
      let errorMessage = 'Failed to save prompt'
      if (error instanceof Error) {
        try {
          const parsed = JSON.parse(error.message)
          if (parsed.message) {
            errorMessage = parsed.message
          }
        } catch {
          // Not JSON, use generic message
        }
      }
      toast.error(errorMessage)
    } finally {
      setSavingPrompt(false)
    }
  }

  const toggleExpandPrompt = (promptType: string) => {
    setExpandedPrompts(prev => {
      const next = new Set(prev)
      if (next.has(promptType)) {
        next.delete(promptType)
      } else {
        next.add(promptType)
      }
      return next
    })
  }

  const getModelName = (modelId: string) => {
    const model = models.find(m => m.id === modelId)
    return model?.name || modelId
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="flex items-center gap-4 border-b border-border px-4 py-3">
        <button
          onClick={onBack}
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="text-xl font-medium text-foreground">Settings</h1>
      </header>

      {/* Tab navigation */}
      <div className="border-b border-border px-4">
        <div className="mx-auto max-w-4xl">
          <div className="flex gap-6">
            <button
              onClick={() => setActiveTab('api')}
              className={cn(
                'border-b-2 py-3 text-sm font-medium transition-colors',
                activeTab === 'api'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              )}
            >
              <span className="flex items-center gap-2">
                <Key className="h-4 w-4" />
                API Settings
              </span>
            </button>
            <button
              onClick={() => setActiveTab('prompts')}
              className={cn(
                'border-b-2 py-3 text-sm font-medium transition-colors',
                activeTab === 'prompts'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              )}
            >
              <span className="flex items-center gap-2">
                <Bot className="h-4 w-4" />
                AI Prompts
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="px-4 py-6">
        <div className="mx-auto max-w-4xl">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <span className="text-muted-foreground">Loading...</span>
            </div>
          ) : activeTab === 'api' ? (
            <div className="space-y-6">
              {/* API Status */}
              <div className="rounded-lg border border-border bg-card p-4">
                <h2 className="mb-4 text-lg font-medium text-foreground">OpenRouter API</h2>

                <div className="mb-4 flex items-center gap-2">
                  <div
                    className={cn(
                      'h-2 w-2 rounded-full',
                      aiStatus?.available ? 'bg-green-500' : aiStatus?.configured ? 'bg-yellow-500' : 'bg-red-500'
                    )}
                  />
                  <span className="text-sm text-muted-foreground">
                    {aiStatus?.available ? 'Connected' : aiStatus?.configured ? 'Invalid key' : 'Not configured'}
                  </span>
                </div>

                {aiStatus?.configured && !aiStatus?.valid && (
                  <div className="mb-4 flex items-center gap-2 rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-3">
                    <AlertCircle className="h-5 w-5 flex-shrink-0 text-yellow-500" />
                    <p className="text-sm text-yellow-600 dark:text-yellow-400">
                      {aiStatus?.error || 'Your API key appears to be invalid or expired. Please update it.'}
                    </p>
                  </div>
                )}

                {aiStatus?.available && (
                  <div className="mb-4 text-sm text-muted-foreground">
                    Default model: <span className="font-medium text-foreground">{getModelName(aiStatus.default_model)}</span>
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
            </div>
          ) : (
            <div className="space-y-4">
              {/* Prompts header */}
              <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-4">
                <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" />
                <div>
                  <h2 className="font-medium text-foreground">AI Prompts Configuration</h2>
                  <p className="text-sm text-muted-foreground">
                    Customize the prompts used for AI features. Each prompt has a system prompt that sets the AI's behavior
                    and a user prompt template that includes placeholders for dynamic content.
                  </p>
                </div>
              </div>

              {!aiStatus?.available && (
                <div className="flex items-center gap-3 rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-4">
                  <AlertCircle className="h-5 w-5 text-yellow-500" />
                  <p className="text-sm text-yellow-600 dark:text-yellow-400">
                    Configure your OpenRouter API key in the API Settings tab to enable AI features.
                  </p>
                </div>
              )}

              {/* Prompt cards */}
              {prompts.map((prompt) => {
                const isEditing = editingPromptType === prompt.prompt_type
                const isExpanded = expandedPrompts.has(prompt.prompt_type)

                return (
                  <div
                    key={prompt.prompt_type}
                    className="rounded-lg border border-border bg-card"
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between p-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-foreground">{prompt.name}</h3>
                          {!prompt.is_active && (
                            <span className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                              Disabled
                            </span>
                          )}
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">{prompt.description}</p>
                        <div className="mt-2 flex items-center gap-2">
                          <span className="rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                            {getModelName(prompt.model)}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {!isEditing && (
                          <>
                            <button
                              onClick={() => toggleExpandPrompt(prompt.prompt_type)}
                              className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                              aria-label={isExpanded ? 'Collapse' : 'Expand'}
                            >
                              {isExpanded ? (
                                <ChevronUp className="h-5 w-5" />
                              ) : (
                                <ChevronDown className="h-5 w-5" />
                              )}
                            </button>
                            <button
                              onClick={() => handleEditPrompt(prompt)}
                              className="rounded-lg bg-primary/10 px-3 py-1.5 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
                            >
                              Edit
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Expanded view (read-only) */}
                    {isExpanded && !isEditing && (
                      <div className="border-t border-border px-4 py-4">
                        <div className="space-y-4">
                          <div>
                            <label className="mb-1 block text-sm font-medium text-muted-foreground">
                              System Prompt
                            </label>
                            <pre className="whitespace-pre-wrap rounded-lg bg-muted p-3 text-sm text-foreground">
                              {prompt.system_prompt}
                            </pre>
                          </div>
                          <div>
                            <label className="mb-1 block text-sm font-medium text-muted-foreground">
                              User Prompt Template
                            </label>
                            <pre className="whitespace-pre-wrap rounded-lg bg-muted p-3 text-sm text-foreground">
                              {prompt.user_prompt_template}
                            </pre>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Edit form */}
                    {isEditing && editForm && (
                      <div className="border-t border-border px-4 py-4">
                        <div className="space-y-4">
                          <div>
                            <label className="mb-1 block text-sm font-medium text-foreground">
                              System Prompt
                            </label>
                            <textarea
                              value={editForm.system_prompt}
                              onChange={(e) => setEditForm({ ...editForm, system_prompt: e.target.value })}
                              rows={6}
                              className="w-full rounded-lg border border-border bg-input-background px-3 py-2 font-mono text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                            />
                          </div>
                          <div>
                            <label className="mb-1 block text-sm font-medium text-foreground">
                              User Prompt Template
                            </label>
                            <textarea
                              value={editForm.user_prompt_template}
                              onChange={(e) => setEditForm({ ...editForm, user_prompt_template: e.target.value })}
                              rows={4}
                              className="w-full rounded-lg border border-border bg-input-background px-3 py-2 font-mono text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                            />
                            <p className="mt-1 text-xs text-muted-foreground">
                              Use {'{placeholders}'} for dynamic content
                            </p>
                          </div>
                          <div className="flex gap-4">
                            <div className="flex-1">
                              <label className="mb-1 block text-sm font-medium text-foreground">
                                Model
                              </label>
                              <select
                                value={editForm.model}
                                onChange={(e) => setEditForm({ ...editForm, model: e.target.value })}
                                className="w-full rounded-lg border border-border bg-input-background px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                              >
                                {models.map((model) => (
                                  <option key={model.id} value={model.id}>
                                    {model.name}
                                  </option>
                                ))}
                              </select>
                            </div>
                            <div>
                              <label className="mb-1 block text-sm font-medium text-foreground">
                                Status
                              </label>
                              <button
                                onClick={() => setEditForm({ ...editForm, is_active: !editForm.is_active })}
                                className={cn(
                                  'rounded-lg px-4 py-2 text-sm font-medium transition-colors',
                                  editForm.is_active
                                    ? 'bg-green-500/10 text-green-600 hover:bg-green-500/20 dark:text-green-400'
                                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                                )}
                              >
                                {editForm.is_active ? 'Active' : 'Disabled'}
                              </button>
                            </div>
                          </div>
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={handleCancelEdit}
                              className="flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                            >
                              <X className="h-4 w-4" />
                              Cancel
                            </button>
                            <button
                              onClick={handleSavePrompt}
                              disabled={savingPrompt}
                              className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              {savingPrompt ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Check className="h-4 w-4" />
                              )}
                              Save Changes
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
