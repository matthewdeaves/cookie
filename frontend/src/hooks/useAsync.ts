import { useState, useCallback } from 'react'

export interface AsyncState<T> {
  loading: boolean
  error: Error | null
  data: T | null
}

export interface UseAsyncReturn<T> extends AsyncState<T> {
  execute: (promise: Promise<T>) => Promise<T>
  reset: () => void
}

/**
 * Hook for managing async operation state (loading, error, data).
 *
 * Provides a standardized pattern for handling async operations,
 * replacing the common useState trio of loading/error/data.
 *
 * @example
 * const { loading, error, data, execute } = useAsync<Recipe[]>()
 *
 * const loadRecipes = async () => {
 *   await execute(api.recipes.list())
 * }
 *
 * if (loading) return <Spinner />
 * if (error) return <ErrorMessage error={error} />
 * return <RecipeList recipes={data} />
 */
export function useAsync<T>(): UseAsyncReturn<T> {
  const [state, setState] = useState<AsyncState<T>>({
    loading: false,
    error: null,
    data: null,
  })

  const execute = useCallback(async (promise: Promise<T>): Promise<T> => {
    setState({ loading: true, error: null, data: null })
    try {
      const data = await promise
      setState({ loading: false, error: null, data })
      return data
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error))
      setState({ loading: false, error: err, data: null })
      throw error
    }
  }, [])

  const reset = useCallback(() => {
    setState({ loading: false, error: null, data: null })
  }, [])

  return { ...state, execute, reset }
}

/**
 * Hook variant that preserves previous data during loading.
 *
 * Useful for refresh/pagination where you want to show stale data
 * while new data loads.
 *
 * @example
 * const { loading, data, execute } = useAsyncWithStaleData<Recipe[]>()
 *
 * // `data` retains previous value during reload
 * const refresh = () => execute(api.recipes.list())
 */
export function useAsyncWithStaleData<T>(): UseAsyncReturn<T> {
  const [state, setState] = useState<AsyncState<T>>({
    loading: false,
    error: null,
    data: null,
  })

  const execute = useCallback(async (promise: Promise<T>): Promise<T> => {
    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const data = await promise
      setState({ loading: false, error: null, data })
      return data
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error))
      setState((prev) => ({ ...prev, loading: false, error: err }))
      throw error
    }
  }, [])

  const reset = useCallback(() => {
    setState({ loading: false, error: null, data: null })
  }, [])

  return { ...state, execute, reset }
}
