import { useState } from 'react'
import { Check, Loader2, Play, CheckCircle, XCircle, HelpCircle } from 'lucide-react'
import { toast } from 'sonner'
import { api, type Source } from '../../api/client'

interface SettingsSelectorsProps {
  sources: Source[]
  onSourcesChange: (sources: Source[]) => void
}

export default function SettingsSelectors({
  sources,
  onSourcesChange,
}: SettingsSelectorsProps) {
  const [editingSourceId, setEditingSourceId] = useState<number | null>(null)
  const [editingSelectorValue, setEditingSelectorValue] = useState('')
  const [savingSelector, setSavingSelector] = useState(false)
  const [testingSourceId, setTestingSourceId] = useState<number | null>(null)
  const [testingAll, setTestingAll] = useState(false)

  const getSourceStatus = (source: Source): 'working' | 'broken' | 'untested' => {
    if (!source.last_validated_at) return 'untested'
    if (source.needs_attention || source.consecutive_failures >= 3) return 'broken'
    return 'working'
  }

  const formatRelativeTime = (dateStr: string | null): string => {
    if (!dateStr) return 'Never'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays}d ago`
  }

  const handleEditSelector = (source: Source) => {
    setEditingSourceId(source.id)
    setEditingSelectorValue(source.result_selector)
  }

  const handleCancelEditSelector = () => {
    setEditingSourceId(null)
    setEditingSelectorValue('')
  }

  const handleSaveSelector = async () => {
    if (editingSourceId === null) return

    setSavingSelector(true)
    try {
      const result = await api.sources.updateSelector(
        editingSourceId,
        editingSelectorValue
      )
      onSourcesChange(
        sources.map((s) =>
          s.id === editingSourceId
            ? { ...s, result_selector: result.result_selector }
            : s
        )
      )
      toast.success('Selector updated')
      setEditingSourceId(null)
      setEditingSelectorValue('')
    } catch (error) {
      console.error('Failed to update selector:', error)
      toast.error('Failed to update selector')
    } finally {
      setSavingSelector(false)
    }
  }

  const handleTestSource = async (sourceId: number) => {
    setTestingSourceId(sourceId)
    try {
      const result = await api.sources.test(sourceId)
      if (result.success) {
        toast.success(result.message)
      } else {
        toast.error(result.message)
      }
      // Refresh sources to update status
      const sourcesData = await api.sources.list()
      onSourcesChange(sourcesData)
    } catch (error) {
      console.error('Failed to test source:', error)
      toast.error('Failed to test source')
    } finally {
      setTestingSourceId(null)
    }
  }

  const handleTestAllSources = async () => {
    setTestingAll(true)
    try {
      const result = await api.sources.testAll()
      toast.success(
        `Tested ${result.tested} sources: ${result.passed} passed, ${result.failed} failed`
      )
      // Refresh sources
      const sourcesData = await api.sources.list()
      onSourcesChange(sourcesData)
    } catch (error) {
      console.error('Failed to test all sources:', error)
      toast.error('Failed to test all sources')
    } finally {
      setTestingAll(false)
    }
  }

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
        {sources.map((source) => {
          const status = getSourceStatus(source)
          const isEditing = editingSourceId === source.id
          const isTesting = testingSourceId === source.id

          return (
            <div
              key={source.id}
              className="rounded-lg border border-border bg-card p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-foreground">
                      {source.name}
                    </span>
                    {status === 'working' && (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    {status === 'broken' && (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    {status === 'untested' && (
                      <HelpCircle className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{source.host}</p>
                  {source.consecutive_failures >= 3 && (
                    <p className="mt-1 text-xs text-red-500">
                      Failed {source.consecutive_failures} times - auto-disabled
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    Last tested: {formatRelativeTime(source.last_validated_at)}
                  </span>
                  <button
                    onClick={() => handleTestSource(source.id)}
                    disabled={isTesting || testingAll}
                    className="flex items-center gap-1 rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isTesting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                    Test
                  </button>
                </div>
              </div>

              <div className="mt-3">
                <label className="mb-1 block text-xs font-medium text-muted-foreground">
                  CSS Selector
                </label>
                {isEditing ? (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={editingSelectorValue}
                      onChange={(e) => setEditingSelectorValue(e.target.value)}
                      className="flex-1 rounded-lg border border-border bg-input-background px-3 py-1.5 font-mono text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                    <button
                      onClick={handleCancelEditSelector}
                      className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveSelector}
                      disabled={savingSelector}
                      className="flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {savingSelector ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                      Save
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <code className="flex-1 rounded bg-muted px-3 py-1.5 font-mono text-sm text-foreground">
                      {source.result_selector || '(none)'}
                    </code>
                    <button
                      onClick={() => handleEditSelector(source)}
                      className="rounded-lg bg-primary/10 px-3 py-1.5 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
                    >
                      Edit
                    </button>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
