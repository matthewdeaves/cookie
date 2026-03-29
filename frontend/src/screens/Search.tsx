import { useState, useCallback } from 'react'
import { Loader2, Search as SearchIcon } from 'lucide-react'
import { type SearchResult } from '../api/client'
import NavHeader from '../components/NavHeader'
import SourceFilterChips from '../components/SourceFilterChips'
import URLImportCard from '../components/URLImportCard'
import { useSearch } from '../hooks/useSearch'

export default function Search() {
  const search = useSearch()

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <NavHeader />
      <main className="flex-1 px-4 py-6">
        <div className="mx-auto max-w-4xl">
          <SearchForm
            searchInput={search.searchInput}
            setSearchInput={search.setSearchInput}
            onSubmit={search.handleSearchSubmit}
          />
          <SearchContent {...search} />
        </div>
      </main>
    </div>
  )
}

function SearchForm({ searchInput, setSearchInput, onSubmit }: {
  searchInput: string
  setSearchInput: (v: string) => void
  onSubmit: (e: React.FormEvent) => void
}) {
  return (
    <form onSubmit={onSubmit} className="mb-6">
      <div className="relative">
        <SearchIcon className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search recipes or paste a URL..."
          className="w-full rounded-xl border border-border bg-input-background py-3 pl-12 pr-4 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
    </form>
  )
}

function SearchContent({ query, results, hasMore, sites, selectedSource, setSelectedSource, loading, loadingMore, importing, isUrl, handleLoadMore, handleImport }: ReturnType<typeof useSearch>) {
  if (isUrl) {
    return <URLImportCard url={query} importing={importing === query} onImport={handleImport} />
  }

  const allSourcesCount = Object.values(sites).reduce((sum, n) => sum + n, 0)

  return (
    <>
      {!loading && (
        <p className="mb-4 text-sm text-muted-foreground">
          {allSourcesCount} {allSourcesCount === 1 ? 'result' : 'results'} found
        </p>
      )}
      <SourceFilterChips sites={sites} selectedSource={selectedSource} onSelectSource={setSelectedSource} />
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : results.length > 0 ? (
        <SearchResults results={results} hasMore={hasMore} loadingMore={loadingMore} importing={importing} onLoadMore={handleLoadMore} onImport={handleImport} />
      ) : (
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-muted-foreground">No recipes found for "{query}"</p>
        </div>
      )}
    </>
  )
}

function SearchResults({ results, hasMore, loadingMore, importing, onLoadMore, onImport }: {
  results: SearchResult[]
  hasMore: boolean
  loadingMore: boolean
  importing: string | null
  onLoadMore: () => void
  onImport: (url: string) => void
}) {
  return (
    <>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {results.map((result, index) => (
          <SearchResultCard key={`${result.url}-${index}`} result={result} onImport={onImport} importing={importing === result.url} />
        ))}
      </div>
      <div className="mt-8 flex justify-center">
        {hasMore ? (
          <button onClick={onLoadMore} disabled={loadingMore} className="inline-flex items-center gap-2 rounded-lg bg-muted px-6 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted/80 disabled:opacity-50">
            {loadingMore ? (<><Loader2 className="h-4 w-4 animate-spin" />Loading...</>) : 'Load More'}
          </button>
        ) : (
          <p className="text-sm text-muted-foreground">End of results</p>
        )}
      </div>
    </>
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
  const imageUrl = result.cached_image_url || result.image_url
  const [imgError, setImgError] = useState(false)

  const handleImgError = useCallback(() => {
    setImgError(true)
  }, [])

  return (
    <div className="group flex flex-col overflow-hidden rounded-lg bg-card shadow-sm transition-all hover:shadow-md">
      {/* Image */}
      <div className="relative aspect-[4/3] overflow-hidden bg-muted">
        {imageUrl && !imgError ? (
          <img
            src={imageUrl}
            alt={result.title}
            loading="lazy"
            onError={handleImgError}
            className="h-full w-full object-cover transition-transform group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-muted px-3 text-center text-sm font-medium text-muted-foreground">
            {result.title}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex flex-1 flex-col p-3">
        <h3 className="mb-1 line-clamp-2 text-sm font-medium text-card-foreground">
          {result.title}
        </h3>
        <p className="mb-2 text-xs text-muted-foreground">
          <a href={result.url} target="_blank" rel="noopener noreferrer" className="underline decoration-muted-foreground/50 underline-offset-2">{result.host}</a>
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
          className="mt-auto w-full rounded-md bg-primary/10 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/20 disabled:opacity-50"
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
