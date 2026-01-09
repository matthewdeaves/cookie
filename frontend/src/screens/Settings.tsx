import { useState, useEffect } from 'react'
import {
  ArrowLeft,
  Key,
  Bot,
  Check,
  X,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  AlertTriangle,
  Loader2,
  Globe,
  Code,
  Settings as SettingsIcon,
  Github,
  ToggleLeft,
  ToggleRight,
  CheckCircle,
  XCircle,
  HelpCircle,
  Play,
  Users,
  Trash2,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  api,
  type AIPrompt,
  type AIModel,
  type AIStatus,
  type Source,
  type ProfileWithStats,
  type DeletionPreview,
} from '../api/client'
import { cn } from '../lib/utils'
import { useAIStatus } from '../contexts/AIStatusContext'

interface SettingsProps {
  onBack: () => void
  currentProfileId?: number | null
}

type Tab = 'general' | 'prompts' | 'sources' | 'selectors' | 'users'

export default function Settings({ onBack, currentProfileId }: SettingsProps) {
  const [activeTab, setActiveTab] = useState<Tab>('general')
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null)
  const [prompts, setPrompts] = useState<AIPrompt[]>([])
  const [models, setModels] = useState<AIModel[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const globalAIStatus = useAIStatus()

  // Users tab state
  const [profiles, setProfiles] = useState<ProfileWithStats[]>([])
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deletePreview, setDeletePreview] = useState<DeletionPreview | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)

  // API Key state
  const [apiKey, setApiKey] = useState('')
  const [testingKey, setTestingKey] = useState(false)
  const [savingKey, setSavingKey] = useState(false)

  // Editing state for prompts
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

  // Sources state
  const [togglingSourceId, setTogglingSourceId] = useState<number | null>(null)
  const [bulkToggling, setBulkToggling] = useState(false)

  // Selectors state
  const [editingSourceId, setEditingSourceId] = useState<number | null>(null)
  const [editingSelectorValue, setEditingSelectorValue] = useState('')
  const [savingSelector, setSavingSelector] = useState(false)
  const [testingSourceId, setTestingSourceId] = useState<number | null>(null)
  const [testingAll, setTestingAll] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [statusData, promptsData, modelsData, sourcesData, profilesData] = await Promise.all([
        api.ai.status(),
        api.ai.prompts.list(),
        api.ai.models(),
        api.sources.list(),
        api.profiles.list(),
      ])
      setAiStatus(statusData)
      setPrompts(promptsData)
      setModels(modelsData)
      setSources(sourcesData)
      setProfiles(profilesData)
    } catch (error) {
      console.error('Failed to load settings:', error)
      toast.error('Failed to load settings')
    } finally {
      setLoading(false)
    }
  }

  // API Key handlers
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
        setAiStatus(statusData)
        await globalAIStatus.refresh()
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

  // Prompt handlers
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
      let errorMessage = 'Failed to save prompt'
      if (error instanceof Error) {
        try {
          const parsed = JSON.parse(error.message)
          if (parsed.message) {
            errorMessage = parsed.message
          }
        } catch {
          // Not JSON
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

  // Source handlers
  const handleToggleSource = async (sourceId: number) => {
    setTogglingSourceId(sourceId)
    try {
      const result = await api.sources.toggle(sourceId)
      setSources(sources.map(s =>
        s.id === sourceId ? { ...s, is_enabled: result.is_enabled } : s
      ))
    } catch (error) {
      console.error('Failed to toggle source:', error)
      toast.error('Failed to toggle source')
    } finally {
      setTogglingSourceId(null)
    }
  }

  const handleBulkToggle = async (enable: boolean) => {
    setBulkToggling(true)
    try {
      await api.sources.bulkToggle(enable)
      setSources(sources.map(s => ({ ...s, is_enabled: enable })))
      toast.success(enable ? 'All sources enabled' : 'All sources disabled')
    } catch (error) {
      console.error('Failed to bulk toggle sources:', error)
      toast.error('Failed to update sources')
    } finally {
      setBulkToggling(false)
    }
  }

  // Selector handlers
  const handleEditSelector = (source: Source) => {
    setEditingSourceId(source.id)
    setEditingSelectorValue(source.result_selector)
  }

  const handleCancelEditSelector = () => {
    setEditingSourceId(null)
    setEditingSelectorValue('')
  }

  const handleSaveSelector = async () => {
    if (editingSourceId === null) return

    setSavingSelector(true)
    try {
      const result = await api.sources.updateSelector(editingSourceId, editingSelectorValue)
      setSources(sources.map(s =>
        s.id === editingSourceId ? { ...s, result_selector: result.result_selector } : s
      ))
      toast.success('Selector updated')
      setEditingSourceId(null)
      setEditingSelectorValue('')
    } catch (error) {
      console.error('Failed to update selector:', error)
      toast.error('Failed to update selector')
    } finally {
      setSavingSelector(false)
    }
  }

  const handleTestSource = async (sourceId: number) => {
    setTestingSourceId(sourceId)
    try {
      const result = await api.sources.test(sourceId)
      if (result.success) {
        toast.success(result.message)
        // Refresh sources to update status
        const sourcesData = await api.sources.list()
        setSources(sourcesData)
      } else {
        toast.error(result.message)
        const sourcesData = await api.sources.list()
        setSources(sourcesData)
      }
    } catch (error) {
      console.error('Failed to test source:', error)
      toast.error('Failed to test source')
    } finally {
      setTestingSourceId(null)
    }
  }

  const handleTestAllSources = async () => {
    setTestingAll(true)
    try {
      const result = await api.sources.testAll()
      toast.success(`Tested ${result.tested} sources: ${result.passed} passed, ${result.failed} failed`)
      // Refresh sources
      const sourcesData = await api.sources.list()
      setSources(sourcesData)
    } catch (error) {
      console.error('Failed to test all sources:', error)
      toast.error('Failed to test all sources')
    } finally {
      setTestingAll(false)
    }
  }

  const getModelName = (modelId: string) => {
    const model = models.find(m => m.id === modelId)
    return model?.name || modelId
  }

  const getSourceStatus = (source: Source): 'working' | 'broken' | 'untested' => {
    if (!source.last_validated_at) return 'untested'
    if (source.needs_attention || source.consecutive_failures >= 3) return 'broken'
    return 'working'
  }

  const formatRelativeTime = (dateStr: string | null): string => {
    if (!dateStr) return 'Never'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays}d ago`
  }

  // Profile deletion handlers
  const handleDeleteClick = async (profileId: number) => {
    try {
      const preview = await api.profiles.deletionPreview(profileId)
      setDeletePreview(preview)
      setDeletingId(profileId)
      setShowDeleteModal(true)
    } catch (error) {
      console.error('Failed to load deletion preview:', error)
      toast.error('Failed to load profile info')
    }
  }

  const handleConfirmDelete = async () => {
    if (!deletingId) return

    setDeleting(true)
    try {
      await api.profiles.delete(deletingId)
      setProfiles(profiles.filter(p => p.id !== deletingId))
      toast.success('Profile deleted successfully')
      setShowDeleteModal(false)
      setDeletePreview(null)
      setDeletingId(null)
    } catch (error) {
      console.error('Failed to delete profile:', error)
      toast.error('Failed to delete profile')
    } finally {
      setDeleting(false)
    }
  }

  const handleCancelDelete = () => {
    setShowDeleteModal(false)
    setDeletePreview(null)
    setDeletingId(null)
  }

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString()
  }

  const enabledCount = sources.filter(s => s.is_enabled).length

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
          <div className="flex gap-4 overflow-x-auto">
            <button
              onClick={() => setActiveTab('general')}
              className={cn(
                'border-b-2 py-3 text-sm font-medium transition-colors whitespace-nowrap',
                activeTab === 'general'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              )}
            >
              <span className="flex items-center gap-2">
                <SettingsIcon className="h-4 w-4" />
                General
              </span>
            </button>
            <button
              onClick={() => setActiveTab('prompts')}
              className={cn(
                'border-b-2 py-3 text-sm font-medium transition-colors whitespace-nowrap',
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
            <button
              onClick={() => setActiveTab('sources')}
              className={cn(
                'border-b-2 py-3 text-sm font-medium transition-colors whitespace-nowrap',
                activeTab === 'sources'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              )}
            >
              <span className="flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Sources
              </span>
            </button>
            <button
              onClick={() => setActiveTab('selectors')}
              className={cn(
                'border-b-2 py-3 text-sm font-medium transition-colors whitespace-nowrap',
                activeTab === 'selectors'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              )}
            >
              <span className="flex items-center gap-2">
                <Code className="h-4 w-4" />
                Selectors
              </span>
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={cn(
                'border-b-2 py-3 text-sm font-medium transition-colors whitespace-nowrap',
                activeTab === 'users'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              )}
            >
              <span className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                Users
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
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : activeTab === 'general' ? (
            /* General Tab */
            <div className="space-y-6">
              {/* OpenRouter API */}
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
          ) : activeTab === 'prompts' ? (
            /* AI Prompts Tab */
            <div className="space-y-4">
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
                    Configure your OpenRouter API key in the General tab to enable AI features.
                  </p>
                </div>
              )}

              {prompts.map((prompt) => {
                const isEditing = editingPromptType === prompt.prompt_type
                const isExpanded = expandedPrompts.has(prompt.prompt_type)

                return (
                  <div
                    key={prompt.prompt_type}
                    className="rounded-lg border border-border bg-card"
                  >
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
                              {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
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

                    {isExpanded && !isEditing && (
                      <div className="border-t border-border px-4 py-4">
                        <div className="space-y-4">
                          <div>
                            <label className="mb-1 block text-sm font-medium text-muted-foreground">System Prompt</label>
                            <pre className="whitespace-pre-wrap rounded-lg bg-muted p-3 text-sm text-foreground">
                              {prompt.system_prompt}
                            </pre>
                          </div>
                          <div>
                            <label className="mb-1 block text-sm font-medium text-muted-foreground">User Prompt Template</label>
                            <pre className="whitespace-pre-wrap rounded-lg bg-muted p-3 text-sm text-foreground">
                              {prompt.user_prompt_template}
                            </pre>
                          </div>
                        </div>
                      </div>
                    )}

                    {isEditing && editForm && (
                      <div className="border-t border-border px-4 py-4">
                        <div className="space-y-4">
                          <div>
                            <label className="mb-1 block text-sm font-medium text-foreground">System Prompt</label>
                            <textarea
                              value={editForm.system_prompt}
                              onChange={(e) => setEditForm({ ...editForm, system_prompt: e.target.value })}
                              rows={6}
                              className="w-full rounded-lg border border-border bg-input-background px-3 py-2 font-mono text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                            />
                          </div>
                          <div>
                            <label className="mb-1 block text-sm font-medium text-foreground">User Prompt Template</label>
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
                              <label className="mb-1 block text-sm font-medium text-foreground">Model</label>
                              <select
                                value={editForm.model}
                                onChange={(e) => setEditForm({ ...editForm, model: e.target.value })}
                                className="w-full rounded-lg border border-border bg-input-background px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                              >
                                {models.map((model) => (
                                  <option key={model.id} value={model.id}>{model.name}</option>
                                ))}
                              </select>
                            </div>
                            <div>
                              <label className="mb-1 block text-sm font-medium text-foreground">Status</label>
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
                              {savingPrompt ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
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
          ) : activeTab === 'sources' ? (
            /* Sources Tab */
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border border-border bg-card p-4">
                <div>
                  <h2 className="text-lg font-medium text-foreground">Recipe Sources</h2>
                  <p className="text-sm text-muted-foreground">
                    {enabledCount} of {sources.length} sources currently enabled
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleBulkToggle(true)}
                    disabled={bulkToggling || enabledCount === sources.length}
                    className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Enable All
                  </button>
                  <button
                    onClick={() => handleBulkToggle(false)}
                    disabled={bulkToggling || enabledCount === 0}
                    className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Disable All
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                {sources.map((source) => (
                  <div
                    key={source.id}
                    className={cn(
                      'flex items-center justify-between rounded-lg border p-4 transition-colors',
                      source.is_enabled ? 'border-border bg-card' : 'border-border/50 bg-muted/30'
                    )}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-foreground">{source.name}</span>
                        {source.is_enabled && (
                          <span className="rounded bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-600 dark:text-green-400">
                            Active
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{source.host}</p>
                    </div>
                    <button
                      onClick={() => handleToggleSource(source.id)}
                      disabled={togglingSourceId === source.id}
                      className="text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
                    >
                      {togglingSourceId === source.id ? (
                        <Loader2 className="h-6 w-6 animate-spin" />
                      ) : source.is_enabled ? (
                        <ToggleRight className="h-8 w-8 text-primary" />
                      ) : (
                        <ToggleLeft className="h-8 w-8" />
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : activeTab === 'selectors' ? (
            /* Selectors Tab */
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border border-border bg-card p-4">
                <div>
                  <h2 className="text-lg font-medium text-foreground">Search Source Selector Management</h2>
                  <p className="text-sm text-muted-foreground">
                    Edit CSS selectors and test source connectivity
                  </p>
                </div>
                <button
                  onClick={handleTestAllSources}
                  disabled={testingAll}
                  className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {testingAll ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  Test All Sources
                </button>
              </div>

              <div className="space-y-3">
                {sources.map((source) => {
                  const status = getSourceStatus(source)
                  const isEditing = editingSourceId === source.id
                  const isTesting = testingSourceId === source.id

                  return (
                    <div
                      key={source.id}
                      className="rounded-lg border border-border bg-card p-4"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-foreground">{source.name}</span>
                            {status === 'working' && (
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            )}
                            {status === 'broken' && (
                              <XCircle className="h-4 w-4 text-red-500" />
                            )}
                            {status === 'untested' && (
                              <HelpCircle className="h-4 w-4 text-muted-foreground" />
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">{source.host}</p>
                          {source.consecutive_failures >= 3 && (
                            <p className="mt-1 text-xs text-red-500">
                              Failed {source.consecutive_failures} times - auto-disabled
                            </p>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">
                            Last tested: {formatRelativeTime(source.last_validated_at)}
                          </span>
                          <button
                            onClick={() => handleTestSource(source.id)}
                            disabled={isTesting || testingAll}
                            className="flex items-center gap-1 rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {isTesting ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Play className="h-4 w-4" />
                            )}
                            Test
                          </button>
                        </div>
                      </div>

                      <div className="mt-3">
                        <label className="mb-1 block text-xs font-medium text-muted-foreground">CSS Selector</label>
                        {isEditing ? (
                          <div className="flex gap-2">
                            <input
                              type="text"
                              value={editingSelectorValue}
                              onChange={(e) => setEditingSelectorValue(e.target.value)}
                              className="flex-1 rounded-lg border border-border bg-input-background px-3 py-1.5 font-mono text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                            />
                            <button
                              onClick={handleCancelEditSelector}
                              className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={handleSaveSelector}
                              disabled={savingSelector}
                              className="flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              {savingSelector ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                              Save
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <code className="flex-1 rounded bg-muted px-3 py-1.5 font-mono text-sm text-foreground">
                              {source.result_selector || '(none)'}
                            </code>
                            <button
                              onClick={() => handleEditSelector(source)}
                              className="rounded-lg bg-primary/10 px-3 py-1.5 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
                            >
                              Edit
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ) : activeTab === 'users' ? (
            /* Users Tab */
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-medium text-foreground">User Management</h2>
                  <p className="text-sm text-muted-foreground">
                    Manage user profiles and their data
                  </p>
                </div>
                <span className="text-sm text-muted-foreground">
                  {profiles.length} profile{profiles.length !== 1 ? 's' : ''}
                </span>
              </div>

              <div className="space-y-3">
                {profiles.map((profile) => {
                  const isCurrent = profile.id === currentProfileId

                  return (
                    <div
                      key={profile.id}
                      className="flex items-center justify-between rounded-lg border border-border bg-card p-4"
                    >
                      <div className="flex items-center gap-3">
                        {/* Avatar */}
                        <div
                          className="h-10 w-10 rounded-full"
                          style={{ backgroundColor: profile.avatar_color }}
                        />
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-foreground">{profile.name}</span>
                            {isCurrent && (
                              <span className="rounded bg-primary/10 px-2 py-0.5 text-xs text-primary">
                                Current
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Created {formatDate(profile.created_at)}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {profile.stats.favorites} favorites · {profile.stats.collections} collections · {profile.stats.remixes} remixes
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={() => handleDeleteClick(profile.id)}
                        disabled={isCurrent}
                        className={cn(
                          'rounded p-2 transition-colors',
                          isCurrent
                            ? 'cursor-not-allowed text-muted-foreground/50'
                            : 'text-muted-foreground hover:bg-destructive/10 hover:text-destructive'
                        )}
                        title={isCurrent ? 'Cannot delete current profile' : 'Delete profile'}
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                  )
                })}
              </div>
            </div>
          ) : null}
        </div>
      </main>

      {/* Delete Profile Modal */}
      {showDeleteModal && deletePreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={handleCancelDelete}
          />
          <div className="relative w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
            <div className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              <h3 className="text-lg font-medium">Delete Profile?</h3>
            </div>

            <div className="mt-4 space-y-4">
              {/* Profile info */}
              <div className="flex items-center gap-3">
                <div
                  className="h-12 w-12 rounded-full"
                  style={{ backgroundColor: deletePreview.profile.avatar_color }}
                />
                <div>
                  <div className="font-medium text-foreground">{deletePreview.profile.name}</div>
                  <div className="text-sm text-muted-foreground">
                    Created {formatDate(deletePreview.profile.created_at)}
                  </div>
                </div>
              </div>

              {/* Data summary */}
              <div className="rounded-lg border border-border bg-muted/50 p-3">
                <div className="mb-2 text-sm font-medium text-foreground">Data to be deleted:</div>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  {deletePreview.data_to_delete.remixes > 0 && (
                    <li>• {deletePreview.data_to_delete.remixes} remixed recipe{deletePreview.data_to_delete.remixes !== 1 ? 's' : ''} ({deletePreview.data_to_delete.remix_images} images)</li>
                  )}
                  {deletePreview.data_to_delete.favorites > 0 && (
                    <li>• {deletePreview.data_to_delete.favorites} favorite{deletePreview.data_to_delete.favorites !== 1 ? 's' : ''}</li>
                  )}
                  {deletePreview.data_to_delete.collections > 0 && (
                    <li>• {deletePreview.data_to_delete.collections} collection{deletePreview.data_to_delete.collections !== 1 ? 's' : ''} ({deletePreview.data_to_delete.collection_items} items)</li>
                  )}
                  {deletePreview.data_to_delete.view_history > 0 && (
                    <li>• {deletePreview.data_to_delete.view_history} view history entries</li>
                  )}
                  {(deletePreview.data_to_delete.scaling_cache > 0 || deletePreview.data_to_delete.discover_cache > 0) && (
                    <li>• Cached AI data</li>
                  )}
                  {deletePreview.data_to_delete.remixes === 0 &&
                   deletePreview.data_to_delete.favorites === 0 &&
                   deletePreview.data_to_delete.collections === 0 &&
                   deletePreview.data_to_delete.view_history === 0 &&
                   deletePreview.data_to_delete.scaling_cache === 0 &&
                   deletePreview.data_to_delete.discover_cache === 0 && (
                    <li>• No associated data</li>
                  )}
                </ul>
              </div>

              {/* Warning */}
              <div className="text-sm text-destructive">
                This action cannot be undone. All data will be permanently deleted.
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={handleCancelDelete}
                className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={deleting}
                className="flex items-center gap-2 rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground transition-colors hover:bg-destructive/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {deleting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                Delete Profile
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
