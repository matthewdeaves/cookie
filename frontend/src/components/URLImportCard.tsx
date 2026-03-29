import { ArrowDownToLine, Globe, Loader2 } from 'lucide-react'

interface URLImportCardProps {
  url: string
  importing: boolean
  onImport: (url: string) => void
}

function extractDomain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

function extractPath(url: string): string {
  try {
    const parsed = new URL(url)
    const path = decodeURIComponent(parsed.pathname)
    return path === '/' ? '' : path
  } catch {
    return ''
  }
}

export default function URLImportCard({
  url,
  importing,
  onImport,
}: URLImportCardProps) {
  const domain = extractDomain(url)
  const path = extractPath(url)

  return (
    <div className="mx-auto max-w-lg">
      <div className="rounded-2xl border border-border bg-card overflow-hidden">
        <div className="flex flex-col items-center px-6 pt-8 pb-6 text-center">
          <div className="mb-4 rounded-full bg-primary/10 p-4">
            <Globe className="h-8 w-8 text-primary" />
          </div>
          <h2 className="mb-1 text-lg font-medium text-card-foreground">
            Import from {domain}
          </h2>
          {path && (
            <p className="mb-1 max-w-full text-sm text-muted-foreground break-all leading-relaxed">
              {path}
            </p>
          )}
        </div>

        <div className="px-6 pb-6">
          <button
            onClick={() => onImport(url)}
            disabled={importing}
            className="flex w-full items-center justify-center gap-2.5 rounded-xl bg-primary px-5 py-3.5 text-base font-medium text-primary-foreground transition-all hover:bg-primary/90 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100"
          >
            {importing ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <ArrowDownToLine className="h-5 w-5" />
                Import Recipe
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
