import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { api } from '../api/client'

// Mock fetch globally
const mockFetch = vi.fn()
globalThis.fetch = mockFetch

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('profiles', () => {
    it('lists profiles', async () => {
      const profiles = [
        { id: 1, name: 'Alice', avatar_color: '#d97850', theme: 'light', unit_preference: 'us' },
        { id: 2, name: 'Bob', avatar_color: '#8fae6f', theme: 'dark', unit_preference: 'metric' },
      ]
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(profiles),
      })

      const result = await api.profiles.list()

      expect(mockFetch).toHaveBeenCalledWith('/api/profiles/', expect.objectContaining({
        headers: { 'Content-Type': 'application/json' },
      }))
      expect(result).toEqual(profiles)
    })

    it('creates a profile', async () => {
      const newProfile = { name: 'Charlie', avatar_color: '#6b9dad' }
      const createdProfile = { id: 3, ...newProfile, theme: 'light', unit_preference: 'us' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(createdProfile),
      })

      const result = await api.profiles.create(newProfile)

      expect(mockFetch).toHaveBeenCalledWith('/api/profiles/', expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(newProfile),
      }))
      expect(result).toEqual(createdProfile)
    })

    it('selects a profile', async () => {
      const profile = { id: 1, name: 'Alice', avatar_color: '#d97850', theme: 'light', unit_preference: 'us' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(profile),
      })

      const result = await api.profiles.select(1)

      expect(mockFetch).toHaveBeenCalledWith('/api/profiles/1/select/', expect.objectContaining({
        method: 'POST',
      }))
      expect(result).toEqual(profile)
    })

    it('updates a profile', async () => {
      const updatedProfile = { id: 1, name: 'Alice', avatar_color: '#d97850', theme: 'dark', unit_preference: 'us' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(updatedProfile),
      })

      const result = await api.profiles.update(1, { name: 'Alice', avatar_color: '#d97850', theme: 'dark' })

      expect(mockFetch).toHaveBeenCalledWith('/api/profiles/1/', expect.objectContaining({
        method: 'PUT',
      }))
      expect(result.theme).toBe('dark')
    })

    it('deletes a profile', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
      })

      await api.profiles.delete(1)

      expect(mockFetch).toHaveBeenCalledWith('/api/profiles/1/', expect.objectContaining({
        method: 'DELETE',
      }))
    })
  })

  describe('search', () => {
    it('searches recipes with query', async () => {
      const searchResponse = {
        results: [
          { url: 'https://example.com/recipe1', title: 'Chocolate Cookies', host: 'example.com', image_url: '', description: 'Delicious cookies' },
          { url: 'https://example.com/recipe2', title: 'Sugar Cookies', host: 'example.com', image_url: '', description: 'Sweet treats' },
        ],
        total: 2,
        page: 1,
        has_more: false,
        sites: { 'example.com': 2 },
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(searchResponse),
      })

      const result = await api.recipes.search('cookies')

      expect(mockFetch).toHaveBeenCalledWith('/api/recipes/search/?q=cookies&page=1', expect.any(Object))
      expect(result.results).toHaveLength(2)
      expect(result.total).toBe(2)
      expect(result.has_more).toBe(false)
    })

    it('searches recipes with source filter', async () => {
      const searchResponse = {
        results: [{ url: 'https://allrecipes.com/recipe', title: 'Recipe', host: 'allrecipes.com', image_url: '', description: '' }],
        total: 1,
        page: 1,
        has_more: false,
        sites: { 'allrecipes.com': 1 },
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(searchResponse),
      })

      const result = await api.recipes.search('cookies', 'allrecipes.com')

      expect(mockFetch).toHaveBeenCalledWith('/api/recipes/search/?q=cookies&page=1&sources=allrecipes.com', expect.any(Object))
      expect(result.results).toHaveLength(1)
    })

    it('searches recipes with pagination', async () => {
      const searchResponse = {
        results: [],
        total: 20,
        page: 3,
        has_more: false,
        sites: {},
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(searchResponse),
      })

      const result = await api.recipes.search('cookies', undefined, 3)

      expect(mockFetch).toHaveBeenCalledWith('/api/recipes/search/?q=cookies&page=3', expect.any(Object))
      expect(result.page).toBe(3)
    })

    it('returns has_more when more results exist', async () => {
      const searchResponse = {
        results: Array(6).fill({ url: '', title: '', host: '', image_url: '', description: '' }),
        total: 50,
        page: 1,
        has_more: true,
        sites: {},
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(searchResponse),
      })

      const result = await api.recipes.search('pasta')

      expect(result.has_more).toBe(true)
      expect(result.total).toBe(50)
    })
  })

  describe('scrape', () => {
    it('scrapes a recipe from URL', async () => {
      const recipe = {
        id: 1,
        title: 'Chocolate Cake',
        host: 'example.com',
        image_url: 'https://example.com/cake.jpg',
        image: null,
        total_time: 60,
        rating: 4.5,
        is_remix: false,
        scraped_at: '2024-01-01T00:00:00Z',
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(recipe),
      })

      const result = await api.recipes.scrape('https://example.com/chocolate-cake')

      expect(mockFetch).toHaveBeenCalledWith('/api/recipes/scrape/', expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ url: 'https://example.com/chocolate-cake' }),
      }))
      expect(result.title).toBe('Chocolate Cake')
    })
  })

  describe('error handling', () => {
    it('throws on API error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: () => Promise.resolve('Not found'),
      })

      await expect(api.profiles.get(999)).rejects.toThrow('Not found')
    })

    it('throws on network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(api.profiles.list()).rejects.toThrow('Network error')
    })
  })
})
