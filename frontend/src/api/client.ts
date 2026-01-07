const API_BASE = '/api'

export interface Profile {
  id: number
  name: string
  avatar_color: string
  theme: string
  unit_preference: string
}

export interface ProfileInput {
  name: string
  avatar_color: string
  theme?: string
  unit_preference?: string
}

export interface Recipe {
  id: number
  title: string
  host: string
  image_url: string
  image: string | null
  total_time: number | null
  rating: number | null
  is_remix: boolean
  scraped_at: string
}

export interface Favorite {
  recipe: Recipe
  created_at: string
}

export interface HistoryItem {
  recipe: Recipe
  viewed_at: string
}

export interface SearchResult {
  url: string
  title: string
  host: string
  image_url: string
  description: string
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  page: number
  has_more: boolean
  sites: Record<string, number>
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`

  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  }

  const response = await fetch(url, config)

  if (!response.ok) {
    const error = await response.text()
    throw new Error(error || `Request failed with status ${response.status}`)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T
  }

  return response.json()
}

export const api = {
  profiles: {
    list: () => request<Profile[]>('/profiles/'),

    get: (id: number) => request<Profile>(`/profiles/${id}/`),

    create: (data: ProfileInput) =>
      request<Profile>('/profiles/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    update: (id: number, data: ProfileInput) =>
      request<Profile>(`/profiles/${id}/`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),

    delete: (id: number) =>
      request<null>(`/profiles/${id}/`, {
        method: 'DELETE',
      }),

    select: (id: number) =>
      request<Profile>(`/profiles/${id}/select/`, {
        method: 'POST',
      }),
  },

  favorites: {
    list: () => request<Favorite[]>('/favorites/'),

    add: (recipeId: number) =>
      request<Favorite>('/favorites/', {
        method: 'POST',
        body: JSON.stringify({ recipe_id: recipeId }),
      }),

    remove: (recipeId: number) =>
      request<null>(`/favorites/${recipeId}/`, {
        method: 'DELETE',
      }),
  },

  history: {
    list: (limit: number = 6) =>
      request<HistoryItem[]>(`/history/?limit=${limit}`),

    record: (recipeId: number) =>
      request<HistoryItem>('/history/', {
        method: 'POST',
        body: JSON.stringify({ recipe_id: recipeId }),
      }),

    clear: () =>
      request<null>('/history/', {
        method: 'DELETE',
      }),
  },

  recipes: {
    search: (query: string, sources?: string, page: number = 1) => {
      const params = new URLSearchParams({ q: query, page: String(page) })
      if (sources) params.append('sources', sources)
      return request<SearchResponse>(`/recipes/search/?${params}`)
    },

    scrape: (url: string) =>
      request<Recipe>('/recipes/scrape/', {
        method: 'POST',
        body: JSON.stringify({ url }),
      }),
  },
}
