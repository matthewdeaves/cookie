import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAsync, useAsyncWithStaleData } from '../hooks/useAsync'

describe('useAsync', () => {
  it('starts with initial state', () => {
    const { result } = renderHook(() => useAsync<string>())

    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.data).toBeNull()
  })

  it('sets loading to true during execution', async () => {
    const { result } = renderHook(() => useAsync<string>())

    let resolvePromise: (value: string) => void
    const promise = new Promise<string>((resolve) => {
      resolvePromise = resolve
    })

    act(() => {
      result.current.execute(promise)
    })

    expect(result.current.loading).toBe(true)
    expect(result.current.error).toBeNull()
    expect(result.current.data).toBeNull()

    await act(async () => {
      resolvePromise('result')
    })
  })

  it('sets data on successful execution', async () => {
    const { result } = renderHook(() => useAsync<string>())

    await act(async () => {
      await result.current.execute(Promise.resolve('success'))
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.data).toBe('success')
  })

  it('sets error on failed execution', async () => {
    const { result } = renderHook(() => useAsync<string>())

    await act(async () => {
      try {
        await result.current.execute(Promise.reject(new Error('failed')))
      } catch {
        // Expected
      }
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.error).toEqual(new Error('failed'))
    expect(result.current.data).toBeNull()
  })

  it('converts non-Error rejections to Error objects', async () => {
    const { result } = renderHook(() => useAsync<string>())

    await act(async () => {
      try {
        await result.current.execute(Promise.reject('string error'))
      } catch {
        // Expected
      }
    })

    expect(result.current.error).toBeInstanceOf(Error)
    expect(result.current.error?.message).toBe('string error')
  })

  it('rethrows the error from execute', async () => {
    const { result } = renderHook(() => useAsync<string>())

    await expect(
      act(async () => {
        await result.current.execute(Promise.reject(new Error('test error')))
      })
    ).rejects.toThrow('test error')
  })

  it('returns data from execute on success', async () => {
    const { result } = renderHook(() => useAsync<string>())

    let returnedData: string | undefined

    await act(async () => {
      returnedData = await result.current.execute(Promise.resolve('return value'))
    })

    expect(returnedData).toBe('return value')
  })

  it('clears previous data when starting new execution', async () => {
    const { result } = renderHook(() => useAsync<string>())

    // First execution
    await act(async () => {
      await result.current.execute(Promise.resolve('first'))
    })

    expect(result.current.data).toBe('first')

    // Start second execution
    let resolvePromise: (value: string) => void
    const promise = new Promise<string>((resolve) => {
      resolvePromise = resolve
    })

    act(() => {
      result.current.execute(promise)
    })

    // Data should be cleared during loading
    expect(result.current.data).toBeNull()

    await act(async () => {
      resolvePromise('second')
    })
  })

  it('clears previous error when starting new execution', async () => {
    const { result } = renderHook(() => useAsync<string>())

    // First execution fails
    await act(async () => {
      try {
        await result.current.execute(Promise.reject(new Error('failed')))
      } catch {
        // Expected
      }
    })

    expect(result.current.error).not.toBeNull()

    // Second execution starts
    let resolvePromise: (value: string) => void
    const promise = new Promise<string>((resolve) => {
      resolvePromise = resolve
    })

    act(() => {
      result.current.execute(promise)
    })

    // Error should be cleared during loading
    expect(result.current.error).toBeNull()

    await act(async () => {
      resolvePromise('success')
    })
  })

  it('reset() clears all state', async () => {
    const { result } = renderHook(() => useAsync<string>())

    // Execute successfully
    await act(async () => {
      await result.current.execute(Promise.resolve('data'))
    })

    expect(result.current.data).toBe('data')

    // Reset
    act(() => {
      result.current.reset()
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.data).toBeNull()
  })
})

describe('useAsyncWithStaleData', () => {
  it('preserves previous data during loading', async () => {
    const { result } = renderHook(() => useAsyncWithStaleData<string>())

    // First execution
    await act(async () => {
      await result.current.execute(Promise.resolve('first'))
    })

    expect(result.current.data).toBe('first')

    // Start second execution
    let resolvePromise: (value: string) => void
    const promise = new Promise<string>((resolve) => {
      resolvePromise = resolve
    })

    act(() => {
      result.current.execute(promise)
    })

    // Data should be preserved during loading
    expect(result.current.loading).toBe(true)
    expect(result.current.data).toBe('first')

    await act(async () => {
      resolvePromise('second')
    })

    expect(result.current.data).toBe('second')
  })

  it('preserves previous data on error', async () => {
    const { result } = renderHook(() => useAsyncWithStaleData<string>())

    // First execution succeeds
    await act(async () => {
      await result.current.execute(Promise.resolve('initial'))
    })

    expect(result.current.data).toBe('initial')

    // Second execution fails
    await act(async () => {
      try {
        await result.current.execute(Promise.reject(new Error('failed')))
      } catch {
        // Expected
      }
    })

    // Data should be preserved even after error
    expect(result.current.data).toBe('initial')
    expect(result.current.error).not.toBeNull()
  })

  it('clears previous error on new execution', async () => {
    const { result } = renderHook(() => useAsyncWithStaleData<string>())

    // First execution fails
    await act(async () => {
      try {
        await result.current.execute(Promise.reject(new Error('failed')))
      } catch {
        // Expected
      }
    })

    expect(result.current.error).not.toBeNull()

    // Second execution starts
    let resolvePromise: (value: string) => void
    const promise = new Promise<string>((resolve) => {
      resolvePromise = resolve
    })

    act(() => {
      result.current.execute(promise)
    })

    // Error should be cleared during loading
    expect(result.current.error).toBeNull()

    await act(async () => {
      resolvePromise('success')
    })
  })

  it('reset() clears all state including stale data', async () => {
    const { result } = renderHook(() => useAsyncWithStaleData<string>())

    await act(async () => {
      await result.current.execute(Promise.resolve('data'))
    })

    act(() => {
      result.current.reset()
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.data).toBeNull()
  })
})
