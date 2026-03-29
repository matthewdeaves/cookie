import { useState } from 'react'
import { toast } from 'sonner'
import { api, type Source } from '../api/client'

export default function useSourceToggle(
  sources: Source[],
  onSourcesChange: (sources: Source[]) => void
) {
  const [togglingSourceId, setTogglingSourceId] = useState<number | null>(null)
  const [bulkToggling, setBulkToggling] = useState(false)

  const handleToggleSource = async (sourceId: number) => {
    setTogglingSourceId(sourceId)
    try {
      const result = await api.sources.toggle(sourceId)
      onSourcesChange(
        sources.map((s) =>
          s.id === sourceId ? { ...s, is_enabled: result.is_enabled } : s
        )
      )
    } catch (error) {
      console.error('Failed to toggle source:', error)
      toast.error('Failed to toggle source')
    } finally {
      setTogglingSourceId(null)
    }
  }

  const handleBulkToggle = async (enable: boolean) => {
    setBulkToggling(true)
    try {
      await api.sources.bulkToggle(enable)
      onSourcesChange(sources.map((s) => ({ ...s, is_enabled: enable })))
      toast.success(enable ? 'All sources enabled' : 'All sources disabled')
    } catch (error) {
      console.error('Failed to bulk toggle sources:', error)
      toast.error('Failed to update sources')
    } finally {
      setBulkToggling(false)
    }
  }

  return { togglingSourceId, bulkToggling, handleToggleSource, handleBulkToggle }
}
