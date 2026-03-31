import type { QuotaResponse, QuotaLimits } from '../../api/client'

const FEATURE_LABELS: { key: keyof QuotaLimits; label: string }[] = [
  { key: 'remix', label: 'Remixes' },
  { key: 'remix_suggestions', label: 'Remix Suggestions' },
  { key: 'scale', label: 'Scaling' },
  { key: 'tips', label: 'Tips' },
  { key: 'discover', label: 'Discover' },
  { key: 'timer', label: 'Timer Naming' },
]

function formatResetTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
}

interface AIUsageSectionProps {
  quotaData: QuotaResponse | null
}

export default function AIUsageSection({ quotaData }: AIUsageSectionProps) {
  if (!quotaData) return null

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-4 flex items-center gap-2">
        <h2 className="text-lg font-medium text-foreground">AI Usage</h2>
        {quotaData.unlimited && (
          <span className="rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
            Unlimited
          </span>
        )}
      </div>

      {quotaData.unlimited ? (
        <p className="text-sm text-muted-foreground">
          This profile has unlimited AI usage.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {FEATURE_LABELS.map(({ key, label }) => (
              <div key={key} className="text-sm">
                <span className="text-muted-foreground">{label}: </span>
                <span className="font-medium text-foreground">
                  {quotaData.usage[key]}/{quotaData.limits[key]}
                </span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            Resets at {formatResetTime(quotaData.resets_at)}
          </p>
        </>
      )}
    </div>
  )
}
