import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bot,
  AlertTriangle,
  Loader2,
  Globe,
  Code,
  Settings as SettingsIcon,
  Users,
  Key,
  Smartphone,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  api,
  type AIPrompt,
  type AIModel,
  type AIStatus,
  type Source,
  type ProfileWithStats,
} from '../api/client'
import { cn } from '../lib/utils'
import { useProfile } from '../contexts/ProfileContext'
import { useMode } from '../router'
import { useAuth } from '../contexts/AuthContext'
import NavHeader from '../components/NavHeader'
import {
  SettingsGeneral,
  SettingsPrompts,
  SettingsSources,
  SettingsSelectors,
  SettingsUsers,
  SettingsDanger,
} from '../components/settings'

type Tab = 'general' | 'prompts' | 'sources' | 'selectors' | 'users' | 'danger' | 'account'

function useIsAdmin(): boolean {
  const mode = useMode()
  if (mode === 'public' || mode === 'passkey') {
    // eslint-disable-next-line react-hooks/rules-of-hooks -- Safe: mode is stable after mount
    return useAuth().isAdmin
  }
  return true
}

export default function Settings() {
  const { profile } = useProfile()
  const currentProfileId = profile?.id
  const isAdmin = useIsAdmin()
  const mode = useMode()
  const navigate = useNavigate()

  const [activeTab, setActiveTab] = useState<Tab>('general')
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null)
  const [prompts, setPrompts] = useState<AIPrompt[]>([])
  const [models, setModels] = useState<AIModel[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [profiles, setProfiles] = useState<ProfileWithStats[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [statusData, promptsData, modelsData, sourcesData, profilesData] =
        await Promise.all([
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

  return (
    <div className="min-h-screen bg-background">
      <NavHeader />

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
            {mode === 'passkey' && (
              <button
                onClick={() => navigate('/passkeys')}
                className="border-b-2 border-transparent py-3 text-sm font-medium transition-colors whitespace-nowrap text-muted-foreground hover:text-foreground"
              >
                <span className="flex items-center gap-2">
                  <Key className="h-4 w-4" />
                  Passkeys
                </span>
              </button>
            )}
            {mode === 'passkey' && (
              <button
                onClick={() => navigate('/pair-device')}
                className="border-b-2 border-transparent py-3 text-sm font-medium transition-colors whitespace-nowrap text-muted-foreground hover:text-foreground"
              >
                <span className="flex items-center gap-2">
                  <Smartphone className="h-4 w-4" />
                  Pair Device
                </span>
              </button>
            )}
            {isAdmin && (
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
            )}
            {isAdmin && (
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
            )}
            {isAdmin && (
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
            )}
            {isAdmin && (
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
            )}
            {isAdmin && (
              <button
                onClick={() => setActiveTab('danger')}
                className={cn(
                  'border-b-2 py-3 text-sm font-medium transition-colors whitespace-nowrap',
                  activeTab === 'danger'
                    ? 'border-destructive text-destructive'
                    : 'border-transparent text-muted-foreground hover:text-destructive'
                )}
              >
                <span className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Danger Zone
                </span>
              </button>
            )}
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
            <SettingsGeneral
              aiStatus={aiStatus}
              models={models}
              onAIStatusChange={setAiStatus}
              onModelsChange={setModels}
            />
          ) : activeTab === 'prompts' ? (
            <SettingsPrompts
              aiStatus={aiStatus}
              prompts={prompts}
              models={models}
              onPromptsChange={setPrompts}
            />
          ) : activeTab === 'sources' ? (
            <SettingsSources sources={sources} onSourcesChange={setSources} />
          ) : activeTab === 'selectors' ? (
            <SettingsSelectors sources={sources} onSourcesChange={setSources} />
          ) : activeTab === 'users' ? (
            <SettingsUsers
              profiles={profiles}
              currentProfileId={currentProfileId}
              onProfilesChange={setProfiles}
            />
          ) : activeTab === 'danger' ? (
            <SettingsDanger />
          ) : null}
        </div>
      </main>
    </div>
  )
}
