import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { api, type SearchResponse, type SearchResult } from '../api/client'

export interface UseSearchReturn {
  query: string
  searchInput: string
  setSearchInput: (value: string) => void
  results: SearchResult[]
  hasMore: boolean
  sites: Record<string, number>
  selectedSource: string | null
  setSelectedSource: (source: string | null) => void
  loading: boolean
  loadingMore: boolean
  importing: string | null
  /** Why the first page of results could not be loaded (null when it loaded fine). */
  error: string | null
  /** Hosts that did not answer; the results may be incomplete. */
  failedSources: string[]
  retry: () => void
  handleSearchSubmit: (e: React.FormEvent) => void | Promise<void>
  handleLoadMore: () => void
  handleImport: (url: string) => Promise<void>
}

async function fetchSearchResults(
  query: string,
  selectedSource: string | null,
  pageNum: number,
  signal?: AbortSignal,
) {
  const sources = selectedSource || undefined
  return api.recipes.search(query, sources, pageNum, signal)
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

/** Turn a failed search request into a sentence that is safe and useful to show. */
function describeSearchError(error: unknown): string {
  const status = (error as { status?: number } | null)?.status
  const message = error instanceof Error ? error.message : ''
  if (status === 429 || status === 503) return message
  if (status === 0) return message || "Can't reach the server. Check your connection and try again."
  return 'The search did not complete. Please try again.'
}

async function importRecipe(url: string) {
  const recipe = await api.recipes.scrape(url)
  await api.history.record(recipe.id)
  return recipe
}

function useSearchState(query: string) {
  const [searchInput, setSearchInput] = useState(query)
  const [results, setResults] = useState<SearchResult[]>([])
  const [, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [sites, setSites] = useState<Record<string, number>>({})
  const [selectedSource, setSelectedSource] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [importing, setImporting] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [failedSources, setFailedSources] = useState<string[]>([])
  const [reloadKey, setReloadKey] = useState(0)
  return { searchInput, setSearchInput, results, setResults, setTotal, page, setPage, hasMore, setHasMore, sites, setSites, selectedSource, setSelectedSource, loading, setLoading, loadingMore, setLoadingMore, importing, setImporting, error, setError, failedSources, setFailedSources, reloadKey, setReloadKey }
}

export function useSearch(): UseSearchReturn {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const query = searchParams.get('q') || ''
  const state = useSearchState(query)
  const { selectedSource, setSelectedSource, setResults, setSites, setTotal, setHasMore, setPage, setLoading, setLoadingMore, setImporting, setSearchInput, setError, setFailedSources, reloadKey, setReloadKey } = state

  useEffect(() => {
    setSearchInput(query)
  }, [query, setSearchInput])

  const prevQueryRef = useRef(query)
  // Signal of the current query's search; "load more" shares it so a late page
  // can never be appended to the results of a newer query.
  const abortRef = useRef<AbortController | null>(null)

  const applySearchResponse = (response: SearchResponse, pageNum: number, reset: boolean) => {
    setError(null)
    if (reset) {
      setResults(response.results)
      setSites(response.sites)
      setFailedSources(response.failed_sources ?? [])
    } else {
      setResults((prev) => [...prev, ...response.results])
    }
    setTotal(response.total)
    setHasMore(response.has_more)
    setPage(pageNum)
  }

  const searchRecipes = async (pageNum: number, reset: boolean = false, signal?: AbortSignal) => {
    try {
      const response = await fetchSearchResults(query, selectedSource, pageNum, signal)
      if (!signal?.aborted) applySearchResponse(response, pageNum, reset)
    } catch (error) {
      if (!signal?.aborted && !isAbortError(error)) {
        console.error('Search failed:', error)
        // First page: the screen shows an error panel with a retry button, so
        // a failed search can never be mistaken for "no recipes found".
        if (reset) setError(describeSearchError(error))
        else toast.error(describeSearchError(error))
      }
    } finally {
      if (!signal?.aborted) {
        setLoading(false)
        setLoadingMore(false)
      }
    }
  }

  useEffect(() => {
    if (!query) {
      navigate('/home')
      return
    }
    const abortController = new AbortController()
    abortRef.current = abortController
    setResults([])
    setPage(1)
    setSites({})
    setError(null)
    setFailedSources([])
    setLoading(true)
    if (prevQueryRef.current !== query) {
      setSelectedSource(null)
      prevQueryRef.current = query
    }
    searchRecipes(1, true, abortController.signal)
    return () => { abortController.abort() }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- navigate and searchRecipes are stable, only re-run when query or filter changes
  }, [query, selectedSource, reloadKey])

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = state.searchInput.trim()
    if (!trimmed || state.importing) return
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      state.setImporting(trimmed)
      try {
        const recipe = await importRecipe(trimmed)
        toast.success(`Imported: ${recipe.title}`)
        navigate(`/recipe/${recipe.id}`)
      } catch (err) {
        const msg = err instanceof Error ? err.message : null
        toast.error(msg || 'Could not import recipe from that URL. Try a different link.')
      } finally {
        state.setImporting(null)
      }
      return
    }
    if (trimmed !== query) {
      navigate(`/search?q=${encodeURIComponent(trimmed)}`)
    } else if (!state.loading) {
      // Same query submitted again: treat it as "search again".
      setReloadKey((k) => k + 1)
    }
  }

  const retry = () => setReloadKey((k) => k + 1)

  const handleLoadMore = () => {
    if (state.loadingMore) return
    setLoadingMore(true)
    searchRecipes(state.page + 1, false, abortRef.current?.signal)
  }

  const handleImport = async (url: string) => {
    if (state.importing) return
    setImporting(url)
    try {
      const recipe = await importRecipe(url)
      toast.success(`Imported: ${recipe.title}`)
      navigate(`/recipe/${recipe.id}`)
    } catch (err) {
      const msg = err instanceof Error ? err.message : null
      toast.error(msg || 'Could not import recipe from that URL. Try a different link.')
    } finally { setImporting(null) }
  }

  return {
    query,
    searchInput: state.searchInput,
    setSearchInput: state.setSearchInput,
    results: state.results,
    hasMore: state.hasMore,
    sites: state.sites,
    selectedSource: state.selectedSource,
    setSelectedSource: state.setSelectedSource,
    loading: state.loading,
    loadingMore: state.loadingMore,
    importing: state.importing,
    error: state.error,
    failedSources: state.failedSources,
    retry,
    handleSearchSubmit,
    handleLoadMore,
    handleImport,
  }
}
