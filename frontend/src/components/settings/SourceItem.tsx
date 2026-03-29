import { Loader2, ToggleLeft, ToggleRight } from 'lucide-react'
import type { Source } from '../../api/client'
import { cn } from '../../lib/utils'

interface SourceItemProps {
  source: Source
  toggling: boolean
  onToggle: (sourceId: number) => void
}

export default function SourceItem({ source, toggling, onToggle }: SourceItemProps) {
  return (
    <div
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
        onClick={() => onToggle(source.id)}
        disabled={toggling}
        className="text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
      >
        {toggling ? (
          <Loader2 className="h-6 w-6 animate-spin" />
        ) : source.is_enabled ? (
          <ToggleRight className="h-8 w-8 text-primary" />
        ) : (
          <ToggleLeft className="h-8 w-8" />
        )}
      </button>
    </div>
  )
}
