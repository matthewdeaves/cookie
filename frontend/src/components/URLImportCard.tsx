import { Link as LinkIcon, Loader2 } from 'lucide-react'

interface URLImportCardProps {
  url: string
  importing: boolean
  onImport: (url: string) => void
}

export default function URLImportCard({
  url,
  importing,
  onImport,
}: URLImportCardProps) {
  return (
    <div className="mb-8 rounded-xl border border-border bg-card p-6">
      <div className="flex items-start gap-4">
        <div className="rounded-full bg-primary/10 p-3">
          <LinkIcon className="h-6 w-6 text-primary" />
        </div>
        <div className="flex-1">
          <h2 className="mb-1 font-medium text-card-foreground">
            Import Recipe from URL
          </h2>
          <p className="mb-4 text-sm text-muted-foreground line-clamp-1">
            {url}
          </p>
          <button
            onClick={() => onImport(url)}
            disabled={importing}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
          >
            {importing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Importing...
              </>
            ) : (
              'Import Recipe'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
