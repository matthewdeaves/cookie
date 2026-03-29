import { cn } from '../lib/utils'

interface SourceFilterChipsProps {
  sites: Record<string, number>
  selectedSource: string | null
  onSelectSource: (source: string | null) => void
}

export default function SourceFilterChips({
  sites,
  selectedSource,
  onSelectSource,
}: SourceFilterChipsProps) {
  const sortedSites = Object.entries(sites).sort(([, a], [, b]) => b - a)
  const allSourcesCount = Object.values(sites).reduce((sum, n) => sum + n, 0)

  if (sortedSites.length === 0) return null

  return (
    <div className="mb-6 flex flex-wrap gap-2">
      <button
        onClick={() => onSelectSource(null)}
        className={cn(
          'rounded-full px-3 py-1.5 text-sm font-medium transition-colors',
          selectedSource === null
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted text-muted-foreground hover:bg-muted/80'
        )}
      >
        All Sources ({allSourcesCount})
      </button>
      {sortedSites.map(([site, count]) => (
        <button
          key={site}
          onClick={() => onSelectSource(site)}
          className={cn(
            'rounded-full px-3 py-1.5 text-sm font-medium transition-colors',
            selectedSource === site
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:bg-muted/80'
          )}
        >
          {site} ({count})
        </button>
      ))}
    </div>
  )
}
