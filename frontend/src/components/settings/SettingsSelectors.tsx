import { Loader2, Play } from 'lucide-react'
import type { Source } from '../../api/client'
import useSourceTesting from '../../hooks/useSourceTesting'
import SelectorItem from './SelectorItem'

interface SettingsSelectorsProps {
  sources: Source[]
  onSourcesChange: (sources: Source[]) => void
}

export default function SettingsSelectors({
  sources,
  onSourcesChange,
}: SettingsSelectorsProps) {
  const { testingAll, handleTestAllSources } = useSourceTesting(onSourcesChange)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between rounded-lg border border-border bg-card p-4">
        <div>
          <h2 className="text-lg font-medium text-foreground">
            Search Source Selector Management
          </h2>
          <p className="text-sm text-muted-foreground">
            Edit CSS selectors and test source connectivity
          </p>
        </div>
        <button
          onClick={handleTestAllSources}
          disabled={testingAll}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {testingAll ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          Test All Sources
        </button>
      </div>

      <div className="space-y-3">
        {sources.map((source) => (
          <SelectorItem
            key={source.id}
            source={source}
            testingAll={testingAll}
            onSourcesChange={onSourcesChange}
            sources={sources}
          />
        ))}
      </div>
    </div>
  )
}
