import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import {
  api,
  type AIPrompt,
  type AIModel,
  type AIStatus,
  type Source,
  type ProfileWithStats,
  type QuotaResponse,
} from '../api/client'

export interface SettingsData {
  aiStatus: AIStatus | null
  prompts: AIPrompt[]
  models: AIModel[]
  sources: Source[]
  profiles: ProfileWithStats[]
  quotaData: QuotaResponse | null
  loading: boolean
  setAiStatus: (status: AIStatus | null) => void
  setPrompts: (prompts: AIPrompt[]) => void
  setModels: (models: AIModel[]) => void
  setSources: (sources: Source[]) => void
  setProfiles: (profiles: ProfileWithStats[]) => void
  setQuotaData: (data: QuotaResponse | null) => void
}

export function useSettingsData(isAdmin: boolean): SettingsData {
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null)
  const [prompts, setPrompts] = useState<AIPrompt[]>([])
  const [models, setModels] = useState<AIModel[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [profiles, setProfiles] = useState<ProfileWithStats[]>([])
  const [quotaData, setQuotaData] = useState<QuotaResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [isAdmin])

  const loadData = async () => {
    try {
      if (isAdmin) {
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
      }

      // Load quotas separately — 404 in home mode is expected
      try {
        const quotas = await api.ai.quotas.get()
        setQuotaData(quotas)
      } catch {
        // Quotas not available (e.g. home mode) — ignore
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
      toast.error('Failed to load settings')
    } finally {
      setLoading(false)
    }
  }

  return {
    aiStatus,
    prompts,
    models,
    sources,
    profiles,
    quotaData,
    loading,
    setAiStatus,
    setPrompts,
    setModels,
    setSources,
    setProfiles,
    setQuotaData,
  }
}
