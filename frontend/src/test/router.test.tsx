import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { RouterProvider, createMemoryRouter } from 'react-router-dom'

// Mock all lazy-loaded screens
vi.mock('../screens/ProfileSelector', () => ({ default: () => <div>ProfileSelector</div> }))
vi.mock('../screens/Login', () => ({ default: () => <div>Login</div> }))
vi.mock('../screens/Register', () => ({ default: () => <div>Register</div> }))
vi.mock('../screens/PasskeyLogin', () => ({ default: () => <div>PasskeyLogin</div> }))
vi.mock('../screens/PasskeyRegister', () => ({ default: () => <div>PasskeyRegister</div> }))
vi.mock('../screens/Home', () => ({ default: () => <div>Home</div> }))
vi.mock('../screens/Search', () => ({ default: () => <div>Search</div> }))
vi.mock('../screens/RecipeDetail', () => ({ default: () => <div>RecipeDetail</div> }))
vi.mock('../screens/PlayMode', () => ({ default: () => <div>PlayMode</div> }))
vi.mock('../screens/Favorites', () => ({ default: () => <div>Favorites</div> }))
vi.mock('../screens/AllRecipes', () => ({ default: () => <div>AllRecipes</div> }))
vi.mock('../screens/Collections', () => ({ default: () => <div>Collections</div> }))
vi.mock('../screens/CollectionDetail', () => ({ default: () => <div>CollectionDetail</div> }))
vi.mock('../screens/Settings', () => ({ default: () => <div>Settings</div> }))
vi.mock('../screens/PairDevice', () => ({ default: () => <div>PairDevice</div> }))
vi.mock('../screens/PasskeyManage', () => ({ default: () => <div>PasskeyManage</div> }))

// Mock API
vi.mock('../api/client', () => ({
  api: {
    system: { mode: vi.fn() },
    profiles: { list: vi.fn(), select: vi.fn() },
    auth: { me: vi.fn() },
    ai: { status: vi.fn() },
  },
}))

vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    user: null,
    profile: null,
    isAdmin: false,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshSession: vi.fn(),
  }),
}))

import { api } from '../api/client'
import { useMode } from '../router'

describe('useMode', () => {
  it('is exported as a function', () => {
    expect(typeof useMode).toBe('function')
  })
})

describe('Router - home mode', () => {
  it('renders profile selector at / in home mode', async () => {
    vi.mocked(api.system.mode).mockResolvedValue({ mode: 'home' })
    vi.mocked(api.profiles.list).mockResolvedValue([])
    vi.mocked(api.ai.status).mockResolvedValue({ available: false, model: '', has_key: false })

    const { router } = await import('../router')
    const testRouter = createMemoryRouter(router.routes, { initialEntries: ['/'] })
    render(<RouterProvider router={testRouter} />)

    await waitFor(() => {
      expect(screen.getByText('ProfileSelector')).toBeDefined()
    })
  })
})
