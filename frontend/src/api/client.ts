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
}
