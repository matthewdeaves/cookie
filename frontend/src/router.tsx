import { createContext, lazy, Suspense, useContext, useState, useEffect } from 'react'
import { createBrowserRouter, Outlet, Navigate, useLocation, useRouteError } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AIStatusProvider } from './contexts/AIStatusContext'
import { ProfileProvider, useProfile } from './contexts/ProfileContext'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { api } from './api/client'
import ErrorBoundary from './components/ErrorBoundary'

const ProfileSelector = lazy(() => import('./screens/ProfileSelector'))
const PasskeyLogin = lazy(() => import('./screens/PasskeyLogin'))
const PasskeyRegister = lazy(() => import('./screens/PasskeyRegister'))
const Home = lazy(() => import('./screens/Home'))
const Search = lazy(() => import('./screens/Search'))
const RecipeDetail = lazy(() => import('./screens/RecipeDetail'))
const PlayMode = lazy(() => import('./screens/PlayMode'))
const Favorites = lazy(() => import('./screens/Favorites'))
const AllRecipes = lazy(() => import('./screens/AllRecipes'))
const Collections = lazy(() => import('./screens/Collections'))
const CollectionDetail = lazy(() => import('./screens/CollectionDetail'))
const Settings = lazy(() => import('./screens/Settings'))
// PairDevice and PasskeyManage are now inline tabs in Settings

function LoadingFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-muted-foreground">Loading...</div>
    </div>
  )
}

// Mode context — provides the operating mode to child components without hook violations
const ModeContext = createContext<'home' | 'passkey'>('home')

export function useMode() {
  return useContext(ModeContext)
}

// Version is no longer fetched from the server (/api/system/mode/ dropped the
// `version` key in v1.42.0 to eliminate fingerprinting). Operators read the
// version via `python manage.py cookie_admin status --json`.
export function useVersion() {
  return 'dev'
}

function AppLayout() {
  const [mode, setMode] = useState<'home' | 'passkey' | null>(null)

  useEffect(() => {
    api.system
      .mode()
      .then((data) => {
        setMode(data.mode === 'passkey' ? 'passkey' : 'home')
      })
      .catch(() => setMode('home'))
  }, [])

  if (mode === null) {
    return <LoadingFallback />
  }

  if (mode === 'passkey') {
    return (
      <ModeContext.Provider value="passkey">
        {/* Toaster lives OUTSIDE AuthProfileBridge on purpose.
            AuthProfileBridge unmounts its children while isLoading=true
            (e.g. during refreshSession after self-delete or login).
            If the Toaster is inside, any in-flight toast is torn down
            mid-animation and renders unstyled at the document-flow
            default position (top-left on mobile). Keeping it at the
            ModeContext level means it survives every auth-state change
            within passkey mode. */}
        <Toaster position="top-center" richColors />
        <AuthProvider>
          <AIStatusProvider>
            <AuthProfileBridge>
              <ErrorBoundary>
              <Suspense fallback={<LoadingFallback />}>
                <Outlet />
              </Suspense>
              </ErrorBoundary>
            </AuthProfileBridge>
          </AIStatusProvider>
        </AuthProvider>
      </ModeContext.Provider>
    )
  }

  return (
    <ModeContext.Provider value="home">
      {/* Same reasoning as the passkey branch above. */}
      <Toaster position="top-center" richColors />
      <AIStatusProvider>
        <ProfileProvider>
          <ErrorBoundary>
          <Suspense fallback={<LoadingFallback />}>
            <Outlet />
          </Suspense>
          </ErrorBoundary>
        </ProfileProvider>
      </AIStatusProvider>
    </ModeContext.Provider>
  )
}

function AuthProfileBridge({ children }: { children: React.ReactNode }) {
  const { profile: authProfile, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingFallback />
  }

  return <ProfileProvider authProfile={authProfile}>{children}</ProfileProvider>
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { profile, loading } = useProfile()
  const location = useLocation()

  if (loading) {
    return <LoadingFallback />
  }

  if (!profile) {
    return <Navigate to="/" state={{ from: location }} replace />
  }

  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { profile, loading } = useProfile()

  if (loading) {
    return <LoadingFallback />
  }

  if (profile) {
    return <Navigate to="/home" replace />
  }

  return <>{children}</>
}

function RootRoute() {
  const mode = useMode()
  if (mode === 'passkey') {
    return <PasskeyLogin />
  }
  return <ProfileSelector />
}

function RouteErrorFallback() {
  const error = useRouteError()
  console.error('Route error:', error)
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-8 text-center shadow-lg">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
          <svg className="h-8 w-8 text-destructive" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
            <path d="M12 9v4" />
            <path d="M12 17h.01" />
          </svg>
        </div>
        <h1 className="mb-2 text-xl font-semibold text-foreground">Something went wrong</h1>
        <p className="mb-6 text-sm text-muted-foreground">
          An unexpected error occurred. Please try again.
        </p>
        <div className="flex flex-col gap-2">
          <button
            onClick={() => window.location.href = '/'}
            className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Go Home
          </button>
          <button
            onClick={() => window.location.reload()}
            className="w-full rounded-lg bg-muted px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted/80 hover:text-foreground"
          >
            Reload Page
          </button>
        </div>
      </div>
    </div>
  )
}

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    errorElement: <RouteErrorFallback />,
    children: [
      {
        path: '/',
        element: (
          <PublicRoute>
            <RootRoute />
          </PublicRoute>
        ),
      },
      {
        path: '/register',
        element: (
          <PublicRoute>
            <PasskeyRegister />
          </PublicRoute>
        ),
      },
      {
        path: '/home',
        element: (
          <ProtectedRoute>
            <Home />
          </ProtectedRoute>
        ),
      },
      {
        path: '/search',
        element: (
          <ProtectedRoute>
            <Search />
          </ProtectedRoute>
        ),
      },
      {
        path: '/recipe/:id',
        element: (
          <ProtectedRoute>
            <RecipeDetail />
          </ProtectedRoute>
        ),
      },
      {
        path: '/recipe/:id/play',
        element: (
          <ProtectedRoute>
            <PlayMode />
          </ProtectedRoute>
        ),
      },
      {
        path: '/favorites',
        element: (
          <ProtectedRoute>
            <Favorites />
          </ProtectedRoute>
        ),
      },
      {
        path: '/all-recipes',
        element: (
          <ProtectedRoute>
            <AllRecipes />
          </ProtectedRoute>
        ),
      },
      {
        path: '/collections',
        element: (
          <ProtectedRoute>
            <Collections />
          </ProtectedRoute>
        ),
      },
      {
        path: '/collection/:id',
        element: (
          <ProtectedRoute>
            <CollectionDetail />
          </ProtectedRoute>
        ),
      },
      {
        path: '/settings',
        element: (
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        ),
      },
      {
        path: '/pair-device',
        element: <Navigate to="/settings" replace />,
      },
      {
        path: '/passkeys',
        element: <Navigate to="/settings" replace />,
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
])
