const API_BASE = '/api'

export interface Settings {
  ai_available: boolean
}

export interface AIStatus {
  available: boolean
  default_model: string
}

export interface AIModel {
  id: string
  name: string
}

export interface AIPrompt {
  prompt_type: string
  name: string
  description: string
  system_prompt: string
  user_prompt_template: string
  model: string
  is_active: boolean
}

export interface AIPromptUpdate {
  system_prompt?: string
  user_prompt_template?: string
  model?: string
  is_active?: boolean
}

export interface RemixSuggestionsResponse {
  suggestions: string[]
}

export interface RemixResponse {
  id: number
  title: string
  description: string
  ingredients: string[]
  instructions: { text: string }[]
  host: string
  site_name: string
  is_remix: boolean
  prep_time: number | null
  cook_time: number | null
  total_time: number | null
  yields: string
  servings: number | null
}

export interface NutritionValues {
  per_serving: Record<string, string | number>
  total: Record<string, string | number>
}

export interface ScaleResponse {
  target_servings: number
  original_servings: number
  ingredients: string[]
  instructions: string[]  // QA-031
  notes: string[]
  prep_time_adjusted: number | null  // QA-032
  cook_time_adjusted: number | null  // QA-032
  total_time_adjusted: number | null  // QA-032
  nutrition: NutritionValues | null
  cached: boolean
}

export interface TipsResponse {
  tips: string[]
  cached: boolean
}

export interface DiscoverSuggestion {
  type: string
  title: string
  description: string
  search_query: string
}

export interface DiscoverResponse {
  suggestions: DiscoverSuggestion[]
  refreshed_at: string
}

export interface TestApiKeyResponse {
  success: boolean
  message: string
}

export interface SaveApiKeyResponse {
  success: boolean
  message: string
}

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

export interface IngredientGroup {
  purpose: string
  ingredients: string[]
}

export interface RecipeDetail extends Recipe {
  source_url: string | null
  canonical_url: string
  site_name: string
  author: string
  description: string
  ingredients: string[]
  ingredient_groups: IngredientGroup[]
  instructions: string[]
  instructions_text: string
  prep_time: number | null
  cook_time: number | null
  yields: string
  servings: number | null
  category: string
  cuisine: string
  cooking_method: string
  keywords: string[]
  dietary_restrictions: string[]
  equipment: string[]
  nutrition: Record<string, string>
  rating_count: number | null
  language: string
  links: string[]
  ai_tips: string[]
  remix_profile_id: number | null
  updated_at: string
}

export interface Favorite {
  recipe: Recipe
  created_at: string
}

export interface HistoryItem {
  recipe: Recipe
  viewed_at: string
}

export interface Collection {
  id: number
  name: string
  description: string
  recipe_count: number
  created_at: string
  updated_at: string
}

export interface CollectionItem {
  recipe: Recipe
  order: number
  added_at: string
}

export interface CollectionDetail {
  id: number
  name: string
  description: string
  recipes: CollectionItem[]
  created_at: string
  updated_at: string
}

export interface CollectionInput {
  name: string
  description?: string
}

export interface SearchResult {
  url: string
  title: string
  host: string
  image_url: string
  cached_image_url: string | null
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
    // Read body as text first (can only be read once)
    const errorText = await response.text()
    let errorMessage = errorText || `Request failed with status ${response.status}`

    // Try to parse as JSON to extract detail/message
    try {
      const errorData = JSON.parse(errorText)
      errorMessage = errorData.detail || errorData.message || errorMessage
    } catch {
      // Not JSON, use text as-is
    }
    throw new Error(errorMessage)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T
  }

  return response.json()
}

export const api = {
  settings: {
    get: () => request<Settings>('/settings/'),
  },

  ai: {
    status: () => request<AIStatus>('/ai/status'),

    testApiKey: (apiKey: string) =>
      request<TestApiKeyResponse>('/ai/test-api-key', {
        method: 'POST',
        body: JSON.stringify({ api_key: apiKey }),
      }),

    saveApiKey: (apiKey: string) =>
      request<SaveApiKeyResponse>('/ai/save-api-key', {
        method: 'POST',
        body: JSON.stringify({ api_key: apiKey }),
      }),

    models: () => request<AIModel[]>('/ai/models'),

    prompts: {
      list: () => request<AIPrompt[]>('/ai/prompts'),

      get: (promptType: string) => request<AIPrompt>(`/ai/prompts/${promptType}`),

      update: (promptType: string, data: AIPromptUpdate) =>
        request<AIPrompt>(`/ai/prompts/${promptType}`, {
          method: 'PUT',
          body: JSON.stringify(data),
        }),
    },

    remix: {
      getSuggestions: (recipeId: number) =>
        request<RemixSuggestionsResponse>('/ai/remix-suggestions', {
          method: 'POST',
          body: JSON.stringify({ recipe_id: recipeId }),
        }),

      create: (recipeId: number, modification: string, profileId: number) =>
        request<RemixResponse>('/ai/remix', {
          method: 'POST',
          body: JSON.stringify({
            recipe_id: recipeId,
            modification,
            profile_id: profileId,
          }),
        }),
    },

    scale: (recipeId: number, targetServings: number, profileId: number, unitSystem: string = 'metric') =>
      request<ScaleResponse>('/ai/scale', {
        method: 'POST',
        body: JSON.stringify({
          recipe_id: recipeId,
          target_servings: targetServings,
          profile_id: profileId,
          unit_system: unitSystem,
        }),
      }),

    tips: (recipeId: number, regenerate: boolean = false) =>
      request<TipsResponse>('/ai/tips', {
        method: 'POST',
        body: JSON.stringify({ recipe_id: recipeId, regenerate }),
      }),

    discover: (profileId: number) =>
      request<DiscoverResponse>(`/ai/discover/${profileId}/`),
  },

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

  collections: {
    list: () => request<Collection[]>('/collections/'),

    get: (id: number) => request<CollectionDetail>(`/collections/${id}/`),

    create: (data: CollectionInput) =>
      request<Collection>('/collections/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    update: (id: number, data: CollectionInput) =>
      request<Collection>(`/collections/${id}/`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),

    delete: (id: number) =>
      request<null>(`/collections/${id}/`, {
        method: 'DELETE',
      }),

    addRecipe: (collectionId: number, recipeId: number) =>
      request<CollectionItem>(`/collections/${collectionId}/recipes/`, {
        method: 'POST',
        body: JSON.stringify({ recipe_id: recipeId }),
      }),

    removeRecipe: (collectionId: number, recipeId: number) =>
      request<null>(`/collections/${collectionId}/recipes/${recipeId}/`, {
        method: 'DELETE',
      }),
  },

  recipes: {
    get: (id: number) => request<RecipeDetail>(`/recipes/${id}/`),

    search: (query: string, sources?: string, page: number = 1) => {
      const params = new URLSearchParams({ q: query, page: String(page) })
      if (sources) params.append('sources', sources)
      return request<SearchResponse>(`/recipes/search/?${params}`)
    },

    scrape: (url: string) =>
      request<RecipeDetail>('/recipes/scrape/', {
        method: 'POST',
        body: JSON.stringify({ url }),
      }),
  },
}
