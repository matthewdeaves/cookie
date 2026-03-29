import { Github, Moon, Sun } from 'lucide-react'
import type { AIStatus, AIModel } from '../../api/client'
import { useProfile } from '../../contexts/ProfileContext'
import { useVersion } from '../../router'
import { cn } from '../../lib/utils'
import APIKeySection from './APIKeySection'

interface SettingsGeneralProps {
  aiStatus: AIStatus | null
  models: AIModel[]
  onAIStatusChange: (status: AIStatus) => void
  onModelsChange: (models: AIModel[]) => void
  isAdmin: boolean
}

export default function SettingsGeneral({
  aiStatus,
  models,
  onAIStatusChange,
  onModelsChange,
  isAdmin,
}: SettingsGeneralProps) {
  const { theme, toggleTheme } = useProfile()
  const version = useVersion()

  return (
    <div className="space-y-6">
      {/* Preferences */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="mb-4 text-lg font-medium text-foreground">Preferences</h2>

        {/* Theme toggle */}
        <div className="mb-4">
          <label className="mb-2 block text-sm font-medium text-foreground">Theme</label>
          <div className="flex gap-2">
            <button
              onClick={() => theme !== 'light' && toggleTheme()}
              className={cn(
                'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors',
                theme === 'light'
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border bg-background text-foreground hover:bg-muted'
              )}
            >
              <Sun className="h-4 w-4" />
              Light
            </button>
            <button
              onClick={() => theme !== 'dark' && toggleTheme()}
              className={cn(
                'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors',
                theme === 'dark'
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border bg-background text-foreground hover:bg-muted'
              )}
            >
              <Moon className="h-4 w-4" />
              Dark
            </button>
          </div>
        </div>

        {/* Unit preference hidden until fully implemented */}
      </div>

      {/* OpenRouter API — admin only */}
      {isAdmin && <APIKeySection
        aiStatus={aiStatus}
        models={models}
        onAIStatusChange={onAIStatusChange}
        onModelsChange={onModelsChange}
      />}

      {/* About */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="mb-4 text-lg font-medium text-foreground">About</h2>
        <div className="space-y-2 text-sm text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>Version</span>
            <span className="font-medium text-foreground">{version}</span>
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
