import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import {
  api,
  type AIPrompt,
  type AIModel,
  type AIStatus,
  type Source,
  type ProfileWithStats,
} from '../api/client'

export interface SettingsData {
  aiStatus: AIStatus | null
  prompts: AIPrompt[]
  models: AIModel[]
  sources: Source[]
  profiles: ProfileWithStats[]
  loading: boolean
  setAiStatus: (status: AIStatus | null) => void
  setPrompts: (prompts: AIPrompt[]) => void
  setModels: (models: AIModel[]) => void
  setSources: (sources: Source[]) => void
  setProfiles: (profiles: ProfileWithStats[]) => void
}

export function useSettingsData(): SettingsData {
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

  return {
    aiStatus,
    prompts,
    models,
    sources,
    profiles,
    loading,
    setAiStatus,
    setPrompts,
    setModels,
    setSources,
    setProfiles,
  }
}
