import { useState } from 'react'
import { Loader2, ToggleLeft, ToggleRight } from 'lucide-react'
import { toast } from 'sonner'
import { api, type Source } from '../../api/client'
import { cn } from '../../lib/utils'

interface SettingsSourcesProps {
  sources: Source[]
  onSourcesChange: (sources: Source[]) => void
}

export default function SettingsSources({
  sources,
  onSourcesChange,
}: SettingsSourcesProps) {
  const [togglingSourceId, setTogglingSourceId] = useState<number | null>(null)
  const [bulkToggling, setBulkToggling] = useState(false)

  const enabledCount = sources.filter((s) => s.is_enabled).length

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
          <div
            key={source.id}
            className={cn(
              'flex items-center justify-between rounded-lg border p-4 transition-colors',
              source.is_enabled
                ? 'border-border bg-card'
                : 'border-border/50 bg-muted/30'
            )}
          >
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-foreground">{source.name}</span>
                {source.is_enabled && (
                  <span className="rounded bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-600 dark:text-green-400">
                    Active
                  </span>
                )}
              </div>
              <p className="text-sm text-muted-foreground">{source.host}</p>
            </div>
            <button
              onClick={() => handleToggleSource(source.id)}
              disabled={togglingSourceId === source.id}
              className="text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
            >
              {togglingSourceId === source.id ? (
                <Loader2 className="h-6 w-6 animate-spin" />
              ) : source.is_enabled ? (
                <ToggleRight className="h-8 w-8 text-primary" />
              ) : (
                <ToggleLeft className="h-8 w-8" />
              )}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
