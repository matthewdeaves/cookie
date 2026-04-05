import { useState, type ReactNode } from 'react'
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
import { useProfile } from '../contexts/ProfileContext'
import { useMode } from '../router'
import { useOptionalAuth } from '../contexts/AuthContext'
import { useSettingsData } from '../hooks/useSettingsData'
import NavHeader from '../components/NavHeader'
import DeviceCodeEntry from '../components/DeviceCodeEntry'
import SettingsPasskeys from '../components/settings/SettingsPasskeys'
import {
  SettingsGeneral,
  SettingsPrompts,
  SettingsSources,
  SettingsSelectors,
  SettingsUsers,
  SettingsDanger,
} from '../components/settings'
import SettingsTabNav, { type TabConfig } from './components/SettingsTabNav'

type Tab = 'general' | 'passkeys' | 'pair-device' | 'prompts' | 'sources' | 'selectors' | 'users' | 'danger'

function useIsAdmin(): boolean {
  const mode = useMode()
  const auth = useOptionalAuth()
  if (mode === 'passkey') {
    return auth?.isAdmin ?? false
  }
  return true
}

function buildTabConfig(mode: string, isAdmin: boolean): TabConfig<Tab>[] {
  return [
    { id: 'general', label: 'General', icon: SettingsIcon, visible: true },
    { id: 'passkeys', label: 'Passkeys', icon: Key, visible: mode === 'passkey' },
    { id: 'pair-device', label: 'Pair Device', icon: Smartphone, visible: mode === 'passkey' },
    { id: 'prompts', label: 'AI Prompts', icon: Bot, visible: isAdmin },
    { id: 'sources', label: 'Sources', icon: Globe, visible: isAdmin },
    { id: 'selectors', label: 'Selectors', icon: Code, visible: isAdmin },
    { id: 'users', label: 'Users', icon: Users, visible: isAdmin },
    { id: 'danger', label: 'Danger Zone', icon: AlertTriangle, visible: isAdmin, variant: 'destructive' as const },
  ]
}

function PairDeviceContent() {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="mb-4 text-lg font-medium text-foreground">Pair a Device</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Enter the code shown on the device you want to pair
        </p>
        <DeviceCodeEntry />
      </div>
    </div>
  )
}

export default function Settings() {
  const { profile } = useProfile()
  const currentProfileId = profile?.id
  const isAdmin = useIsAdmin()
  const mode = useMode()
  const data = useSettingsData(isAdmin)

  const [activeTab, setActiveTab] = useState<Tab>('general')

  const tabs = buildTabConfig(mode, isAdmin)

  const tabContent: Record<Tab, () => ReactNode> = {
    general: () => (
      <SettingsGeneral
        aiStatus={data.aiStatus}
        models={data.models}
        onAIStatusChange={data.setAiStatus}
        onModelsChange={data.setModels}
        isAdmin={isAdmin}
        quotaData={data.quotaData}
        onQuotaSave={(limits) => {
          if (data.quotaData) data.setQuotaData({ ...data.quotaData, limits })
        }}
      />
    ),
    passkeys: () => <SettingsPasskeys />,
    'pair-device': () => <PairDeviceContent />,
    prompts: () => (
      <SettingsPrompts
        aiStatus={data.aiStatus}
        prompts={data.prompts}
        models={data.models}
        onPromptsChange={data.setPrompts}
      />
    ),
    sources: () => <SettingsSources sources={data.sources} onSourcesChange={data.setSources} />,
    selectors: () => <SettingsSelectors sources={data.sources} onSourcesChange={data.setSources} />,
    users: () => (
      <SettingsUsers
        profiles={data.profiles}
        currentProfileId={currentProfileId}
        onProfilesChange={data.setProfiles}
      />
    ),
    danger: () => <SettingsDanger />,
  }

  const renderContent = tabContent[activeTab]
  const isAdminTab = ['prompts', 'sources', 'selectors', 'users', 'danger'].includes(activeTab)
  const content = (!isAdminTab || isAdmin) ? renderContent() : null

  return (
    <div className="min-h-screen bg-background">
      <NavHeader />

      <SettingsTabNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="px-4 py-6">
        <div className="mx-auto max-w-4xl">
          {data.loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : content}
        </div>
      </main>
    </div>
  )
}
