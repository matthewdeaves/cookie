import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { api, type SearchResult } from '../api/client'

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
  return { searchInput, setSearchInput, results, setResults, setTotal, page, setPage, hasMore, setHasMore, sites, setSites, selectedSource, setSelectedSource, loading, setLoading, loadingMore, setLoadingMore, importing, setImporting }
}

export function useSearch(): UseSearchReturn {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const query = searchParams.get('q') || ''
  const state = useSearchState(query)
  const { selectedSource, setSelectedSource, setResults, setSites, setTotal, setHasMore, setPage, setLoading, setLoadingMore, setImporting, setSearchInput } = state

  useEffect(() => {
    setSearchInput(query)
  }, [query, setSearchInput])

  const prevQueryRef = useRef(query)

  const applySearchResponse = (response: { results: SearchResult[]; sites: Record<string, number>; total: number; has_more: boolean }, pageNum: number, reset: boolean) => {
    if (reset) {
      setResults(response.results)
      setSites(response.sites)
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
        toast.error('Search failed. Please try again.')
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
    setResults([])
    setPage(1)
    setSites({})
    setLoading(true)
    if (prevQueryRef.current !== query) {
      setSelectedSource(null)
      prevQueryRef.current = query
    }
    searchRecipes(1, true, abortController.signal)
    return () => { abortController.abort() }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- navigate and searchRecipes are stable, only re-run when query or filter changes
  }, [query, selectedSource])

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = state.searchInput.trim()
    if (!trimmed) return
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
    }
  }

  const handleLoadMore = () => {
    setLoadingMore(true)
    searchRecipes(state.page + 1, false)
  }

  const handleImport = async (url: string) => {
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
    handleSearchSubmit,
    handleLoadMore,
    handleImport,
  }
}
