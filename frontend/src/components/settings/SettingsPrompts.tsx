import { AlertCircle } from 'lucide-react'
import type { AIPrompt, AIModel, AIStatus } from '../../api/client'
import PromptCard from './PromptCard'

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
  const handlePromptUpdated = (updated: AIPrompt) => {
    onPromptsChange(
      prompts.map((p) => (p.prompt_type === updated.prompt_type ? updated : p))
    )
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

      {prompts.map((prompt) => (
        <PromptCard
          key={prompt.prompt_type}
          prompt={prompt}
          models={models}
          onPromptUpdated={handlePromptUpdated}
        />
      ))}
    </div>
  )
}
