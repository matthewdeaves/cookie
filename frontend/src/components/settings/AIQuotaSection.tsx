import { useState, useEffect } from 'react'
import { Loader2, Save } from 'lucide-react'
import { toast } from 'sonner'
import { api, type QuotaResponse, type QuotaLimits } from '../../api/client'

const FEATURE_LABELS: { key: keyof QuotaLimits; label: string }[] = [
  { key: 'remix', label: 'Remixes' },
  { key: 'remix_suggestions', label: 'Remix Suggestions' },
  { key: 'scale', label: 'Scaling' },
  { key: 'tips', label: 'Tips' },
  { key: 'discover', label: 'Discover' },
  { key: 'timer', label: 'Timer Naming' },
]

interface AIQuotaSectionProps {
  quotaData: QuotaResponse | null
  onSave: (limits: QuotaLimits) => void
}

export default function AIQuotaSection({ quotaData, onSave }: AIQuotaSectionProps) {
  const defaultLimits: QuotaLimits = { remix: 0, remix_suggestions: 0, scale: 0, tips: 0, discover: 0, timer: 0 }
  const [limits, setLimits] = useState<QuotaLimits>(
    quotaData?.limits ?? defaultLimits,
  )
  const [saving, setSaving] = useState(false)

  // Sync limits when quotaData loads from parent
  useEffect(() => {
    if (!quotaData?.limits) return
    const id = requestAnimationFrame(() => setLimits(quotaData.limits))
    return () => cancelAnimationFrame(id)
  }, [quotaData?.limits])

  const handleChange = (key: keyof QuotaLimits, value: string) => {
    const num = parseInt(value, 10)
    if (!isNaN(num) && num >= 0) setLimits((prev) => ({ ...prev, [key]: num }))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await api.ai.quotas.update(limits)
      onSave(updated.limits)
      toast.success('Quota limits saved')
    } catch {
      toast.error('Failed to save quota limits')
    } finally {
      setSaving(false)
    }
  }

  if (!quotaData) return null

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h2 className="mb-4 text-lg font-medium text-foreground">AI Daily Limits</h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {FEATURE_LABELS.map(({ key, label }) => (
          <label key={key} className="block">
            <span className="mb-1 block text-sm font-medium text-foreground">{label}</span>
            <input
              type="number"
              min={0}
              value={limits[key]}
              onChange={(e) => handleChange(key, e.target.value)}
              className="w-full rounded-lg border border-border bg-input-background px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </label>
        ))}
      </div>
      <button
        onClick={handleSave}
        disabled={saving}
        className="mt-4 flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
        Save Limits
      </button>
    </div>
  )
}
