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

  describe('collections', () => {
    const mockRecipe = {
      id: 1,
      title: 'Test Recipe',
      host: 'example.com',
      image_url: 'https://example.com/img.jpg',
      image: null,
      total_time: 30,
      rating: 4.5,
      is_remix: false,
      scraped_at: '2024-01-01T00:00:00Z',
    }

    it('lists collections', async () => {
      const collections = [
        { id: 1, name: 'Weeknight Dinners', description: 'Quick meals', recipe_count: 5, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' },
        { id: 2, name: 'Holiday Baking', description: '', recipe_count: 3, created_at: '2024-01-02T00:00:00Z', updated_at: '2024-01-02T00:00:00Z' },
      ]
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(collections),
      })

      const result = await api.collections.list()

      expect(mockFetch).toHaveBeenCalledWith('/api/collections/', expect.objectContaining({
        headers: { 'Content-Type': 'application/json' },
      }))
      expect(result).toHaveLength(2)
      expect(result[0].name).toBe('Weeknight Dinners')
    })

    it('creates a collection', async () => {
      const newCollection = { name: 'Desserts', description: 'Sweet treats' }
      const createdCollection = { id: 3, ...newCollection, recipe_count: 0, created_at: '2024-01-03T00:00:00Z', updated_at: '2024-01-03T00:00:00Z' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(createdCollection),
      })

      const result = await api.collections.create(newCollection)

      expect(mockFetch).toHaveBeenCalledWith('/api/collections/', expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(newCollection),
      }))
      expect(result.name).toBe('Desserts')
    })

    it('gets a collection with recipes', async () => {
      const collectionDetail = {
        id: 1,
        name: 'Weeknight Dinners',
        description: 'Quick meals',
        recipes: [
          { recipe: mockRecipe, order: 1, added_at: '2024-01-01T00:00:00Z' },
        ],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(collectionDetail),
      })

      const result = await api.collections.get(1)

      expect(mockFetch).toHaveBeenCalledWith('/api/collections/1/', expect.any(Object))
      expect(result.recipes).toHaveLength(1)
      expect(result.recipes[0].recipe.title).toBe('Test Recipe')
    })

    it('updates a collection', async () => {
      const updatedCollection = { id: 1, name: 'Quick Dinners', description: 'Updated desc', recipe_count: 5, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-03T00:00:00Z' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(updatedCollection),
      })

      const result = await api.collections.update(1, { name: 'Quick Dinners', description: 'Updated desc' })

      expect(mockFetch).toHaveBeenCalledWith('/api/collections/1/', expect.objectContaining({
        method: 'PUT',
      }))
      expect(result.name).toBe('Quick Dinners')
    })

    it('deletes a collection', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
      })

      await api.collections.delete(1)

      expect(mockFetch).toHaveBeenCalledWith('/api/collections/1/', expect.objectContaining({
        method: 'DELETE',
      }))
    })

    it('adds a recipe to a collection', async () => {
      const collectionItem = { recipe: mockRecipe, order: 2, added_at: '2024-01-03T00:00:00Z' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(collectionItem),
      })

      const result = await api.collections.addRecipe(1, 1)

      expect(mockFetch).toHaveBeenCalledWith('/api/collections/1/recipes/', expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ recipe_id: 1 }),
      }))
      expect(result.recipe.title).toBe('Test Recipe')
    })

    it('removes a recipe from a collection', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
      })

      await api.collections.removeRecipe(1, 1)

      expect(mockFetch).toHaveBeenCalledWith('/api/collections/1/recipes/1/', expect.objectContaining({
        method: 'DELETE',
      }))
    })
  })

  describe('favorites', () => {
    const mockRecipe = {
      id: 1,
      title: 'Chocolate Cake',
      host: 'example.com',
      image_url: 'https://example.com/cake.jpg',
      image: null,
      total_time: 60,
      rating: 4.8,
      is_remix: false,
      scraped_at: '2024-01-01T00:00:00Z',
    }

    it('lists favorites', async () => {
      const favorites = [
        { recipe: mockRecipe, created_at: '2024-01-01T00:00:00Z' },
      ]
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(favorites),
      })

      const result = await api.favorites.list()

      expect(mockFetch).toHaveBeenCalledWith('/api/favorites/', expect.any(Object))
      expect(result).toHaveLength(1)
      expect(result[0].recipe.title).toBe('Chocolate Cake')
    })

    it('adds a favorite', async () => {
      const favorite = { recipe: mockRecipe, created_at: '2024-01-01T00:00:00Z' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(favorite),
      })

      const result = await api.favorites.add(1)

      expect(mockFetch).toHaveBeenCalledWith('/api/favorites/', expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ recipe_id: 1 }),
      }))
      expect(result.recipe.title).toBe('Chocolate Cake')
    })

    it('removes a favorite', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
      })

      await api.favorites.remove(1)

      expect(mockFetch).toHaveBeenCalledWith('/api/favorites/1/', expect.objectContaining({
        method: 'DELETE',
      }))
    })
  })

  describe('history', () => {
    const mockRecipe = {
      id: 1,
      title: 'Pasta Carbonara',
      host: 'example.com',
      image_url: 'https://example.com/pasta.jpg',
      image: null,
      total_time: 30,
      rating: 4.7,
      is_remix: false,
      scraped_at: '2024-01-01T00:00:00Z',
    }

    it('lists history', async () => {
      const history = [
        { recipe: mockRecipe, viewed_at: '2024-01-01T12:00:00Z' },
      ]
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(history),
      })

      const result = await api.history.list()

      expect(mockFetch).toHaveBeenCalledWith('/api/history/?limit=6', expect.any(Object))
      expect(result).toHaveLength(1)
      expect(result[0].recipe.title).toBe('Pasta Carbonara')
    })

    it('lists history with custom limit', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      })

      await api.history.list(10)

      expect(mockFetch).toHaveBeenCalledWith('/api/history/?limit=10', expect.any(Object))
    })

    it('records a view', async () => {
      const historyItem = { recipe: mockRecipe, viewed_at: '2024-01-01T12:00:00Z' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(historyItem),
      })

      const result = await api.history.record(1)

      expect(mockFetch).toHaveBeenCalledWith('/api/history/', expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ recipe_id: 1 }),
      }))
      expect(result.recipe.title).toBe('Pasta Carbonara')
    })

    it('clears history', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
      })

      await api.history.clear()

      expect(mockFetch).toHaveBeenCalledWith('/api/history/', expect.objectContaining({
        method: 'DELETE',
      }))
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
