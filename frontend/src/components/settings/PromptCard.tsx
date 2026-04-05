import { useState } from 'react'
import {
  Check,
  X,
  ChevronDown,
  ChevronUp,
  Loader2,
} from 'lucide-react'
import { toast } from 'sonner'
import { api, type AIPrompt, type AIModel } from '../../api/client'
import { cn } from '../../lib/utils'

interface PromptEditForm {
  system_prompt: string
  user_prompt_template: string
  model: string
  is_active: boolean
}

interface PromptCardProps {
  prompt: AIPrompt
  models: AIModel[]
  onPromptUpdated: (updated: AIPrompt) => void
}

function PromptCardHeader({
  prompt,
  modelName,
}: {
  prompt: AIPrompt
  modelName: string
}) {
  return (
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
          {modelName}
        </span>
      </div>
    </div>
  )
}

function PromptReadOnlyView({ prompt }: { prompt: AIPrompt }) {
  return (
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
  )
}

function PromptModelControls({
  editForm,
  models,
  onFormChange,
}: {
  editForm: PromptEditForm
  models: AIModel[]
  onFormChange: (form: PromptEditForm) => void
}) {
  return (
    <div className="flex gap-4">
      <div className="flex-1">
        <label className="mb-1 block text-sm font-medium text-foreground">
          Model
        </label>
        <select
          value={editForm.model}
          onChange={(e) =>
            onFormChange({ ...editForm, model: e.target.value })
          }
          className="w-full rounded-lg border border-border bg-input-background px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {models.length === 0 && (
            <option value={editForm.model}>{editForm.model}</option>
          )}
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
            onFormChange({ ...editForm, is_active: !editForm.is_active })
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
  )
}

function PromptEditActions({
  saving,
  onSave,
  onCancel,
}: {
  saving: boolean
  onSave: () => void
  onCancel: () => void
}) {
  return (
    <div className="flex justify-end gap-2">
      <button
        onClick={onCancel}
        className="flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
      >
        <X className="h-4 w-4" />
        Cancel
      </button>
      <button
        onClick={onSave}
        disabled={saving}
        className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {saving ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Check className="h-4 w-4" />
        )}
        Save Changes
      </button>
    </div>
  )
}

function PromptEditView({
  editForm,
  models,
  saving,
  onFormChange,
  onSave,
  onCancel,
}: {
  editForm: PromptEditForm
  models: AIModel[]
  saving: boolean
  onFormChange: (form: PromptEditForm) => void
  onSave: () => void
  onCancel: () => void
}) {
  return (
    <div className="border-t border-border px-4 py-4">
      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">
            System Prompt
          </label>
          <textarea
            value={editForm.system_prompt}
            onChange={(e) =>
              onFormChange({ ...editForm, system_prompt: e.target.value })
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
              onFormChange({
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
        <PromptModelControls
          editForm={editForm}
          models={models}
          onFormChange={onFormChange}
        />
        <PromptEditActions saving={saving} onSave={onSave} onCancel={onCancel} />
      </div>
    </div>
  )
}

export default function PromptCard({ prompt, models, onPromptUpdated }: PromptCardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [editForm, setEditForm] = useState<PromptEditForm | null>(null)
  const [saving, setSaving] = useState(false)

  const modelName = models.find((m) => m.id === prompt.model)?.name || prompt.model

  const handleEdit = () => {
    setIsEditing(true)
    setEditForm({
      system_prompt: prompt.system_prompt,
      user_prompt_template: prompt.user_prompt_template,
      model: prompt.model,
      is_active: prompt.is_active,
    })
  }

  const handleCancel = () => {
    setIsEditing(false)
    setEditForm(null)
  }

  const handleSave = async () => {
    if (!editForm) return
    setSaving(true)
    try {
      const updated = await api.ai.prompts.update(prompt.prompt_type, editForm)
      onPromptUpdated(updated)
      toast.success('Prompt saved successfully')
      setIsEditing(false)
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
      setSaving(false)
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="flex items-center justify-between p-4">
        <PromptCardHeader prompt={prompt} modelName={modelName} />
        <div className="flex items-center gap-2">
          {!isEditing && (
            <>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
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
                onClick={handleEdit}
                className="rounded-lg bg-primary/10 px-3 py-1.5 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
              >
                Edit
              </button>
            </>
          )}
        </div>
      </div>

      {isExpanded && !isEditing && <PromptReadOnlyView prompt={prompt} />}

      {isEditing && editForm && (
        <PromptEditView
          editForm={editForm}
          models={models}
          saving={saving}
          onFormChange={setEditForm}
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}
    </div>
  )
}
