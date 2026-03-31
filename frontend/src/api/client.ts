import type {
  ModeResponse,
  AIStatus,
  AIErrorResponse,
  AIModel,
  AIPrompt,
  AIPromptUpdate,
  RemixSuggestionsResponse,
  RemixResponse,
  NutritionValues,
  ScaleResponse,
  TipsResponse,
  DiscoverSuggestion,
  DiscoverResponse,
  TimerNameResponse,
  TestApiKeyResponse,
  SaveApiKeyResponse,
  Profile,
  ProfileStats,
  ProfileWithStats,
  DeletionData,
  ProfileSummary,
  DeletionPreview,
  ProfileInput,
  Recipe,
  IngredientGroup,
  LinkedRecipe,
  RecipeDetail,
  Favorite,
  HistoryItem,
  Collection,
  CollectionItem,
  CollectionDetail,
  CollectionInput,
  SearchResult,
  SearchResponse,
  Source,
  SourceTestResult,
  TestAllSourcesResult,
  ResetDataCounts,
  ResetPreview,
  ResetResult,
  PasskeyAuthResponse,
  PasskeyCredential,
  PasskeyCredentialList,
  DeviceCodeResponse,
  DevicePollResponse,
  QuotaLimits,
  QuotaResponse,
} from './types'

// Re-export all types for consumers
export type {
  ModeResponse,
  AIStatus,
  AIErrorResponse,
  AIModel,
  AIPrompt,
  AIPromptUpdate,
  RemixSuggestionsResponse,
  RemixResponse,
  NutritionValues,
  ScaleResponse,
  TipsResponse,
  DiscoverSuggestion,
  DiscoverResponse,
  TimerNameResponse,
  TestApiKeyResponse,
  SaveApiKeyResponse,
  Profile,
  ProfileStats,
  ProfileWithStats,
  DeletionData,
  ProfileSummary,
  DeletionPreview,
  ProfileInput,
  Recipe,
  IngredientGroup,
  LinkedRecipe,
  RecipeDetail,
  Favorite,
  HistoryItem,
  Collection,
  CollectionItem,
  CollectionDetail,
  CollectionInput,
  SearchResult,
  SearchResponse,
  Source,
  SourceTestResult,
  TestAllSourcesResult,
  ResetDataCounts,
  ResetPreview,
  ResetResult,
  PasskeyAuthResponse,
  PasskeyCredential,
  PasskeyCredentialList,
  DeviceCodeResponse,
  DevicePollResponse,
  QuotaLimits,
  QuotaResponse,
}

const API_BASE = '/api'

function getCsrfToken(): string {
  const value = '; ' + document.cookie
  const parts = value.split('; csrftoken=')
  if (parts.length === 2) return parts.pop()!.split(';').shift() || ''
  return ''
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`

  const method = (options.method || 'GET').toUpperCase()
  const needsCsrf = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)

  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(needsCsrf ? { 'X-CSRFToken': getCsrfToken() } : {}),
      ...options.headers,
    },
  }

  const response = await fetch(url, config)

  if (!response.ok) {
    const errorText = await response.text()
    let errorBody: Record<string, unknown> | null = null
    let errorMessage: string

    try {
      errorBody = JSON.parse(errorText)
      errorMessage = (errorBody as Record<string, string>).detail
        || (errorBody as Record<string, string>).message
        || `Request failed (${response.status})`
    } catch {
      // Non-JSON response (e.g. HTML error page) — never expose raw server
      // output to the user as it may leak internal details.
      errorMessage = `Request failed (${response.status})`
    }

    const error = new Error(errorMessage) as Error & { status: number; body: Record<string, unknown> | null }
    error.status = response.status
    error.body = errorBody
    throw error
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T
  }

  return response.json()
}

export const api = {
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

    discover: (profileId: number, refresh = false) =>
      request<DiscoverResponse>(`/ai/discover/${profileId}/${refresh ? '?refresh=true' : ''}`),

    timerName: (stepText: string, durationMinutes: number) =>
      request<TimerNameResponse>('/ai/timer-name', {
        method: 'POST',
        body: JSON.stringify({
          step_text: stepText,
          duration_minutes: durationMinutes,
        }),
      }),

    quotas: {
      get: () => request<QuotaResponse>('/ai/quotas'),
      update: (limits: QuotaLimits) =>
        request<QuotaResponse>('/ai/quotas', {
          method: 'PUT',
          body: JSON.stringify(limits),
        }),
    },
  },

  profiles: {
    list: () => request<ProfileWithStats[]>('/profiles/'),

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

    deletionPreview: (id: number) =>
      request<DeletionPreview>(`/profiles/${id}/deletion-preview/`),

    setUnlimited: (id: number, unlimited: boolean) =>
      request<{ id: number; name: string; unlimited_ai: boolean }>(
        `/profiles/${id}/set-unlimited/`,
        { method: 'POST', body: JSON.stringify({ unlimited }) },
      ),

    rename: (id: number, name: string) =>
      request<{ id: number; name: string; avatar_color: string }>(
        `/profiles/${id}/rename/`,
        { method: 'PATCH', body: JSON.stringify({ name }) },
      ),
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
    list: (limit: number = 50, offset: number = 0) =>
      request<Recipe[]>(`/recipes/?limit=${limit}&offset=${offset}`),

    get: (id: number) => request<RecipeDetail>(`/recipes/${id}/`),

    search: (query: string, sources?: string, page: number = 1, signal?: AbortSignal) => {
      const params = new URLSearchParams({ q: query, page: String(page) })
      if (sources) params.append('sources', sources)
      return request<SearchResponse>(`/recipes/search/?${params}`, { signal })
    },

    scrape: (url: string) =>
      request<RecipeDetail>('/recipes/scrape/', {
        method: 'POST',
        body: JSON.stringify({ url }),
      }),
  },

  sources: {
    list: () => request<Source[]>('/sources/'),

    get: (id: number) => request<Source>(`/sources/${id}/`),

    enabledCount: () =>
      request<{ enabled: number; total: number }>('/sources/enabled-count/'),

    toggle: (id: number) =>
      request<{ id: number; is_enabled: boolean }>(`/sources/${id}/toggle/`, {
        method: 'POST',
      }),

    bulkToggle: (enable: boolean) =>
      request<{ updated_count: number; is_enabled: boolean }>(
        '/sources/bulk-toggle/',
        {
          method: 'POST',
          body: JSON.stringify({ enable }),
        }
      ),

    updateSelector: (id: number, selector: string) =>
      request<{ id: number; result_selector: string }>(
        `/sources/${id}/selector/`,
        {
          method: 'PUT',
          body: JSON.stringify({ result_selector: selector }),
        }
      ),

    test: (id: number) =>
      request<SourceTestResult>(`/sources/${id}/test/`, {
        method: 'POST',
      }),

    testAll: () =>
      request<TestAllSourcesResult>('/sources/test-all/', {
        method: 'POST',
      }),
  },

  system: {
    mode: () => request<ModeResponse>('/system/mode/'),

    resetPreview: () => request<ResetPreview>('/system/reset-preview/'),

    reset: (confirmationText: string) =>
      request<ResetResult>('/system/reset/', {
        method: 'POST',
        body: JSON.stringify({ confirmation_text: confirmationText }),
      }),
  },

  auth: {
    logout: () =>
      request<{ message: string }>('/auth/logout/', {
        method: 'POST',
      }),

    me: () => request<PasskeyAuthResponse>('/auth/me/'),
  },

  passkey: {
    registerOptions: () =>
      request<Record<string, unknown>>('/auth/passkey/register/options/', {
        method: 'POST',
      }),

    registerVerify: (credential: Record<string, unknown>) =>
      request<PasskeyAuthResponse>('/auth/passkey/register/verify/', {
        method: 'POST',
        body: JSON.stringify(credential),
      }),

    loginOptions: () =>
      request<Record<string, unknown>>('/auth/passkey/login/options/', {
        method: 'POST',
      }),

    loginVerify: (credential: Record<string, unknown>) =>
      request<PasskeyAuthResponse>('/auth/passkey/login/verify/', {
        method: 'POST',
        body: JSON.stringify(credential),
      }),

    listCredentials: () =>
      request<PasskeyCredentialList>('/auth/passkey/credentials/'),

    addCredentialOptions: () =>
      request<Record<string, unknown>>('/auth/passkey/credentials/add/options/', {
        method: 'POST',
      }),

    addCredentialVerify: (credential: Record<string, unknown>) =>
      request<{ credential: PasskeyCredential }>('/auth/passkey/credentials/add/verify/', {
        method: 'POST',
        body: JSON.stringify(credential),
      }),

    deleteCredential: (credentialId: number) =>
      request<{ message: string }>(`/auth/passkey/credentials/${credentialId}/`, {
        method: 'DELETE',
      }),
  },

  device: {
    requestCode: () =>
      request<DeviceCodeResponse>('/auth/device/code/', {
        method: 'POST',
      }),

    poll: () =>
      request<DevicePollResponse>('/auth/device/poll/'),

    authorize: (code: string) =>
      request<{ message: string }>('/auth/device/authorize/', {
        method: 'POST',
        body: JSON.stringify({ code }),
      }),
  },
}
