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
import { request } from './request'

export type { ApiError } from './request'

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

    // Update per-profile display preferences (theme, unit_preference) for the
    // caller's OWN profile. Works in both home and passkey modes — unlike the
    // PUT above which is HomeOnly. Use this from the theme toggle / unit
    // selector; use PUT for full-profile edits (home mode only).
    updatePreferences: (
      id: number,
      data: { theme?: 'light' | 'dark'; unit_preference?: 'metric' | 'imperial' },
    ) =>
      request<Profile>(`/profiles/${id}/preferences/`, {
        method: 'PATCH',
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
      return request<SearchResponse>(`/recipes/search/?${params}`, { signal, timeoutMs: 45000 })
    },

    scrape: (url: string) =>
      request<RecipeDetail>('/recipes/scrape/', {
        method: 'POST',
        body: JSON.stringify({ url }),
      }),

    delete: (id: number) =>
      request<null>(`/recipes/${id}/`, { method: 'DELETE' }),
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

    // Passkey-mode self-service deletion. These live under /auth/ (not
    // /profiles/) because the home-mode equivalents on /profiles/{id}/
    // are HomeOnlyAuth (404 in passkey) — a user deleting THEIR OWN
    // account in passkey mode goes through here instead.
    meDeletionPreview: () =>
      request<DeletionPreview>('/auth/me/deletion-preview/'),

    deleteMe: () =>
      request<null>('/auth/me/', {
        method: 'DELETE',
      }),
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
