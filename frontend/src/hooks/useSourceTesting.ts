import { useState } from 'react'
import { toast } from 'sonner'
import { api, type Source } from '../api/client'

export default function useSourceTesting(
  onSourcesChange: (sources: Source[]) => void
) {
  const [testingAll, setTestingAll] = useState(false)

  const handleTestAllSources = async () => {
    setTestingAll(true)
    try {
      const result = await api.sources.testAll()
      toast.success(
        `Tested ${result.tested} sources: ${result.passed} passed, ${result.failed} failed`
      )
      const sourcesData = await api.sources.list()
      onSourcesChange(sourcesData)
    } catch (error) {
      console.error('Failed to test all sources:', error)
      toast.error('Failed to test all sources')
    } finally {
      setTestingAll(false)
    }
  }

  return { testingAll, handleTestAllSources }
}
