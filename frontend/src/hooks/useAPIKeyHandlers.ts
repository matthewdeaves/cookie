import { useState } from 'react'
import { toast } from 'sonner'
import { api, type AIStatus, type AIModel } from '../api/client'
import { useAIStatus } from '../contexts/AIStatusContext'

interface UseAPIKeyHandlersOptions {
  onAIStatusChange: (status: AIStatus) => void
  onModelsChange: (models: AIModel[]) => void
}

interface UseAPIKeyHandlersReturn {
  apiKey: string
  setApiKey: (key: string) => void
  testingKey: boolean
  savingKey: boolean
  handleTestApiKey: () => Promise<void>
  handleSaveApiKey: () => Promise<void>
}

export function useAPIKeyHandlers({
  onAIStatusChange,
  onModelsChange,
}: UseAPIKeyHandlersOptions): UseAPIKeyHandlersReturn {
  const globalAIStatus = useAIStatus()
  const [apiKey, setApiKey] = useState('')
  const [testingKey, setTestingKey] = useState(false)
  const [savingKey, setSavingKey] = useState(false)

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
        onAIStatusChange(statusData)
        await globalAIStatus.refresh()
        const modelsData = await api.ai.models()
        onModelsChange(modelsData)
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

  return {
    apiKey,
    setApiKey,
    testingKey,
    savingKey,
    handleTestApiKey,
    handleSaveApiKey,
  }
}
