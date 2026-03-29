import type { Source } from '../../api/client'
import useSourceToggle from '../../hooks/useSourceToggle'
import SourceItem from './SourceItem'

interface SettingsSourcesProps {
  sources: Source[]
  onSourcesChange: (sources: Source[]) => void
}

export default function SettingsSources({
  sources,
  onSourcesChange,
}: SettingsSourcesProps) {
  const { togglingSourceId, bulkToggling, handleToggleSource, handleBulkToggle } =
    useSourceToggle(sources, onSourcesChange)

  const enabledCount = sources.filter((s) => s.is_enabled).length

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between rounded-lg border border-border bg-card p-4">
        <div>
          <h2 className="text-lg font-medium text-foreground">Recipe Sources</h2>
          <p className="text-sm text-muted-foreground">
            {enabledCount} of {sources.length} sources currently enabled
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleBulkToggle(true)}
            disabled={bulkToggling || enabledCount === sources.length}
            className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            Enable All
          </button>
          <button
            onClick={() => handleBulkToggle(false)}
            disabled={bulkToggling || enabledCount === 0}
            className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            Disable All
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {sources.map((source) => (
          <SourceItem
            key={source.id}
            source={source}
            toggling={togglingSourceId === source.id}
            onToggle={handleToggleSource}
          />
        ))}
      </div>
    </div>
  )
}
