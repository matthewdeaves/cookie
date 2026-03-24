import { useState } from 'react'
import {
  AlertCircle,
  Check,
  X,
  ChevronDown,
  ChevronUp,
  Loader2,
} from 'lucide-react'
import { toast } from 'sonner'
import { api, type AIPrompt, type AIModel, type AIStatus } from '../../api/client'
import { cn } from '../../lib/utils'

interface SettingsPromptsProps {
  aiStatus: AIStatus | null
  prompts: AIPrompt[]
  models: AIModel[]
  onPromptsChange: (prompts: AIPrompt[]) => void
}

export default function SettingsPrompts({
  aiStatus,
  prompts,
  models,
  onPromptsChange,
}: SettingsPromptsProps) {
  const [editingPromptType, setEditingPromptType] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<{
    system_prompt: string
    user_prompt_template: string
    model: string
    is_active: boolean
  } | null>(null)
  const [savingPrompt, setSavingPrompt] = useState(false)
  const [expandedPrompts, setExpandedPrompts] = useState<Set<string>>(new Set())

  const getModelName = (modelId: string) => {
    const model = models.find((m) => m.id === modelId)
    return model?.name || modelId
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
      onPromptsChange(
        prompts.map((p) => (p.prompt_type === editingPromptType ? updated : p))
      )
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
    setExpandedPrompts((prev) => {
      const next = new Set(prev)
      if (next.has(promptType)) {
        next.delete(promptType)
      } else {
        next.add(promptType)
      }
      return next
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-4">
        <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" />
        <div>
          <h2 className="font-medium text-foreground">AI Prompts Configuration</h2>
          <p className="text-sm text-muted-foreground">
            Customize the prompts used for AI features. Each prompt has a system
            prompt that sets the AI's behavior and a user prompt template that
            includes placeholders for dynamic content.
          </p>
        </div>
      </div>

      {!aiStatus?.available && (
        <div className="flex items-center gap-3 rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-4">
          <AlertCircle className="h-5 w-5 text-yellow-500" />
          <p className="text-sm text-yellow-600 dark:text-yellow-400">
            Configure your OpenRouter API key in the General tab to enable AI
            features.
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
                <p className="mt-1 text-sm text-muted-foreground">
                  {prompt.description}
                </p>
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

            {isEditing && editForm && (
              <div className="border-t border-border px-4 py-4">
                <div className="space-y-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-foreground">
                      System Prompt
                    </label>
                    <textarea
                      value={editForm.system_prompt}
                      onChange={(e) =>
                        setEditForm({ ...editForm, system_prompt: e.target.value })
                      }
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
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          user_prompt_template: e.target.value,
                        })
                      }
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
                        onChange={(e) =>
                          setEditForm({ ...editForm, model: e.target.value })
                        }
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
                        onClick={() =>
                          setEditForm({ ...editForm, is_active: !editForm.is_active })
                        }
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
  )
}
