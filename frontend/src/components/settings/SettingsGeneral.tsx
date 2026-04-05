import { ExternalLink, Moon, Sun } from 'lucide-react'
import type { AIStatus, AIModel, QuotaResponse, QuotaLimits } from '../../api/client'
import { useProfile } from '../../contexts/ProfileContext'
import { useMode, useVersion } from '../../router'
import { useOptionalAuth } from '../../contexts/AuthContext'
import { cn } from '../../lib/utils'
import APIKeySection from './APIKeySection'
import AIQuotaSection from './AIQuotaSection'
import AIUsageSection from './AIUsageSection'
import DeleteAccountSection from './DeleteAccountSection'

interface SettingsGeneralProps {
  aiStatus: AIStatus | null
  models: AIModel[]
  onAIStatusChange: (status: AIStatus) => void
  onModelsChange: (models: AIModel[]) => void
  isAdmin: boolean
  quotaData: QuotaResponse | null
  onQuotaSave: (limits: QuotaLimits) => void
}

export default function SettingsGeneral({
  aiStatus,
  models,
  onAIStatusChange,
  onModelsChange,
  isAdmin,
  quotaData,
  onQuotaSave,
}: SettingsGeneralProps) {
  const { profile, theme, toggleTheme } = useProfile()
  const auth = useOptionalAuth()
  const logout = auth?.logout
  const mode = useMode()
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

      {/* AI Quota Limits — admin only */}
      {isAdmin && <AIQuotaSection quotaData={quotaData} onSave={onQuotaSave} />}

      {/* AI Usage — all users */}
      <AIUsageSection quotaData={quotaData} />

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
              <ExternalLink className="h-4 w-4" />
              GitHub
            </a>
          </div>
        </div>
      </div>

      {/* Delete account — passkey mode, non-admin users */}
      {mode === 'passkey' && !isAdmin && profile && (
        <DeleteAccountSection profileId={profile.id} onDeleted={logout!} />
      )}
    </div>
  )
}
