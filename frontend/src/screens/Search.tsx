import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, Link as LinkIcon, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { api, type SearchResult } from '../api/client'
import { cn } from '../lib/utils'

export default function Search() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const query = searchParams.get('q') || ''

  const [results, setResults] = useState<SearchResult[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [sites, setSites] = useState<Record<string, number>>({})
  const [selectedSource, setSelectedSource] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [importing, setImporting] = useState<string | null>(null)

  // Detect if query is a URL
  const isUrl = /^https?:\/\//i.test(query.trim())

  useEffect(() => {
    if (!query) {
      navigate('/home')
      return
    }
    // Reset state when query or source filter changes
    setResults([])
    setPage(1)
    setLoading(true)
    searchRecipes(1, true)
  }, [query, selectedSource])

  const searchRecipes = async (pageNum: number, reset: boolean = false) => {
    try {
      const sources = selectedSource || undefined
      const response = await api.recipes.search(query, sources, pageNum)

      if (reset) {
        setResults(response.results)
        setSites(response.sites)
      } else {
        setResults((prev) => [...prev, ...response.results])
      }

      setTotal(response.total)
      setHasMore(response.has_more)
      setPage(pageNum)
    } catch (error) {
      console.error('Search failed:', error)
      toast.error('Search failed. Please try again.')
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  const handleLoadMore = () => {
    setLoadingMore(true)
    searchRecipes(page + 1, false)
  }

  const handleSourceFilter = (source: string | null) => {
    setSelectedSource(source)
  }

  const handleImport = async (url: string) => {
    setImporting(url)
    try {
      const recipe = await api.recipes.scrape(url)
      toast.success(`Imported: ${recipe.title}`)
      // Record in history
      await api.history.record(recipe.id)
      // Navigate to recipe detail
      navigate(`/recipe/${recipe.id}`)
    } catch (error) {
      console.error('Failed to import recipe:', error)
      const message = error instanceof Error ? error.message : 'Failed to import recipe'
      toast.error(message)
    } finally {
      setImporting(null)
    }
  }

  const handleBack = () => {
    navigate('/home')
  }

  // Sort sites by count descending for filter chips
  const sortedSites = Object.entries(sites).sort(([, a], [, b]) => b - a)
  const allSourcesCount = Object.values(sites).reduce((sum, n) => sum + n, 0)

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Header with breadcrumb */}
      <header className="border-b border-border px-4 py-3">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-5 w-5" />
          <span>Back to Home</span>
        </button>
      </header>

      <main className="flex-1 px-4 py-6">
        <div className="mx-auto max-w-4xl">
          {/* Query info */}
          <div className="mb-6">
            <h1 className="mb-1 text-xl font-medium text-foreground">
              {isUrl ? 'Import Recipe' : `Search: "${query}"`}
            </h1>
            {!isUrl && !loading && (
              <p className="text-sm text-muted-foreground">
                {total} {total === 1 ? 'result' : 'results'} found
              </p>
            )}
          </div>

          {/* URL Import Card */}
          {isUrl && (
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
                    {query}
                  </p>
                  <button
                    onClick={() => handleImport(query)}
                    disabled={!!importing}
                    className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                  >
                    {importing === query ? (
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
          )}

          {/* Source filter chips */}
          {!isUrl && sortedSites.length > 0 && (
            <div className="mb-6 flex flex-wrap gap-2">
              <button
                onClick={() => handleSourceFilter(null)}
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
                  onClick={() => handleSourceFilter(site)}
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
          )}

          {/* Loading state */}
          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          )}

          {/* Results grid */}
          {!loading && !isUrl && results.length > 0 && (
            <>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                {results.map((result, index) => (
                  <SearchResultCard
                    key={`${result.url}-${index}`}
                    result={result}
                    onImport={handleImport}
                    importing={importing === result.url}
                  />
                ))}
              </div>

              {/* Load more / End of results */}
              <div className="mt-8 flex justify-center">
                {hasMore ? (
                  <button
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                    className="inline-flex items-center gap-2 rounded-lg bg-muted px-6 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted/80 disabled:opacity-50"
                  >
                    {loadingMore ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      'Load More'
                    )}
                  </button>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    End of results
                  </p>
                )}
              </div>
            </>
          )}

          {/* Empty state */}
          {!loading && !isUrl && results.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12">
              <p className="text-muted-foreground">
                No recipes found for "{query}"
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

interface SearchResultCardProps {
  result: SearchResult
  onImport: (url: string) => void
  importing: boolean
}

function SearchResultCard({
  result,
  onImport,
  importing,
}: SearchResultCardProps) {
  // Prefer cached image, fallback to external
  const imageUrl = result.cached_image_url || result.image_url

  return (
    <div className="group overflow-hidden rounded-lg bg-card shadow-sm transition-all hover:shadow-md">
      {/* Image */}
      <div className="relative aspect-[4/3] overflow-hidden bg-muted">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={result.title}
            className="h-full w-full object-cover transition-transform group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground">
            No image
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-3">
        <h3 className="mb-1 line-clamp-2 text-sm font-medium text-card-foreground">
          {result.title}
        </h3>
        <p className="mb-2 text-xs text-muted-foreground">
          {result.host}
          {result.rating_count && (
            <span> · {result.rating_count.toLocaleString()} Ratings</span>
          )}
        </p>
        {result.description && (
          <p className="mb-3 line-clamp-2 text-xs text-muted-foreground">
            {result.description}
          </p>
        )}
        <button
          onClick={() => onImport(result.url)}
          disabled={importing}
          className="w-full rounded-md bg-primary/10 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/20 disabled:opacity-50"
        >
          {importing ? (
            <span className="inline-flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              Importing...
            </span>
          ) : (
            'Import'
          )}
        </button>
      </div>
    </div>
  )
}
