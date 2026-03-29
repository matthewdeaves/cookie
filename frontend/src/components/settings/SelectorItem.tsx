import { useState } from 'react'
import { Check, Loader2, Play, CheckCircle, XCircle, HelpCircle } from 'lucide-react'
import { toast } from 'sonner'
import { api, type Source } from '../../api/client'

interface SelectorItemProps {
  source: Source
  testingAll: boolean
  onSourcesChange: (sources: Source[]) => void
  sources: Source[]
}

function getSourceStatus(source: Source): 'working' | 'broken' | 'untested' {
  if (!source.last_validated_at) return 'untested'
  if (source.needs_attention || source.consecutive_failures >= 3) return 'broken'
  return 'working'
}

function formatRelativeTime(dateStr: string | null): string {
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

function StatusIcon({ status }: { status: 'working' | 'broken' | 'untested' }) {
  if (status === 'working') return <CheckCircle className="h-4 w-4 text-green-500" />
  if (status === 'broken') return <XCircle className="h-4 w-4 text-red-500" />
  return <HelpCircle className="h-4 w-4 text-muted-foreground" />
}

function SelectorItemHeader({
  source,
  testing,
  testingAll,
  onTest,
}: {
  source: Source
  testing: boolean
  testingAll: boolean
  onTest: () => void
}) {
  const status = getSourceStatus(source)

  return (
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-foreground">{source.name}</span>
          <StatusIcon status={status} />
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
          onClick={onTest}
          disabled={testing || testingAll}
          className="flex items-center gap-1 rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
        >
          {testing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          Test
        </button>
      </div>
    </div>
  )
}

function SelectorEditor({
  selectorValue,
  saving,
  currentSelector,
  isEditing,
  onValueChange,
  onEdit,
  onSave,
  onCancel,
}: {
  selectorValue: string
  saving: boolean
  currentSelector: string
  isEditing: boolean
  onValueChange: (value: string) => void
  onEdit: () => void
  onSave: () => void
  onCancel: () => void
}) {
  return (
    <div className="mt-3">
      <label className="mb-1 block text-xs font-medium text-muted-foreground">
        CSS Selector
      </label>
      {isEditing ? (
        <div className="flex gap-2">
          <input
            type="text"
            value={selectorValue}
            onChange={(e) => onValueChange(e.target.value)}
            className="flex-1 rounded-lg border border-border bg-input-background px-3 py-1.5 font-mono text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <button
            onClick={onCancel}
            className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted"
          >
            Cancel
          </button>
          <button
            onClick={onSave}
            disabled={saving}
            className="flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? (
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
            {currentSelector || '(none)'}
          </code>
          <button
            onClick={onEdit}
            className="rounded-lg bg-primary/10 px-3 py-1.5 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
          >
            Edit
          </button>
        </div>
      )}
    </div>
  )
}

export default function SelectorItem({
  source,
  testingAll,
  onSourcesChange,
  sources,
}: SelectorItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [selectorValue, setSelectorValue] = useState('')
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)

  const handleEdit = () => {
    setIsEditing(true)
    setSelectorValue(source.result_selector)
  }

  const handleCancel = () => {
    setIsEditing(false)
    setSelectorValue('')
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const result = await api.sources.updateSelector(source.id, selectorValue)
      onSourcesChange(
        sources.map((s) =>
          s.id === source.id
            ? { ...s, result_selector: result.result_selector }
            : s
        )
      )
      toast.success('Selector updated')
      setIsEditing(false)
      setSelectorValue('')
    } catch (error) {
      console.error('Failed to update selector:', error)
      toast.error('Failed to update selector')
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    try {
      const result = await api.sources.test(source.id)
      if (result.success) {
        toast.success(result.message)
      } else {
        toast.error(result.message)
      }
      const sourcesData = await api.sources.list()
      onSourcesChange(sourcesData)
    } catch (error) {
      console.error('Failed to test source:', error)
      toast.error('Failed to test source')
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <SelectorItemHeader
        source={source}
        testing={testing}
        testingAll={testingAll}
        onTest={handleTest}
      />
      <SelectorEditor
        selectorValue={selectorValue}
        saving={saving}
        currentSelector={source.result_selector}
        isEditing={isEditing}
        onValueChange={setSelectorValue}
        onEdit={handleEdit}
        onSave={handleSave}
        onCancel={handleCancel}
      />
    </div>
  )
}
