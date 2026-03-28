import { createContext, lazy, Suspense, useContext, useState, useEffect } from 'react'
import { createBrowserRouter, Outlet, Navigate, useLocation } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AIStatusProvider } from './contexts/AIStatusContext'
import { ProfileProvider, useProfile } from './contexts/ProfileContext'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { api } from './api/client'

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
const VersionContext = createContext<string>('dev')

export function useMode() {
  return useContext(ModeContext)
}

export function useVersion() {
  return useContext(VersionContext)
}

function AppLayout() {
  const [mode, setMode] = useState<'home' | 'passkey' | null>(null)
  const [version, setVersion] = useState('dev')

  useEffect(() => {
    api.system
      .mode()
      .then((data) => {
        setMode(data.mode === 'passkey' ? 'passkey' : 'home')
        setVersion(data.version || 'dev')
      })
      .catch(() => setMode('home'))
  }, [])

  if (mode === null) {
    return <LoadingFallback />
  }

  if (mode === 'passkey') {
    return (
      <VersionContext.Provider value={version}>
      <ModeContext.Provider value="passkey">
        <AuthProvider>
          <AIStatusProvider>
            <AuthProfileBridge>
              <Toaster position="top-center" richColors />
              <Suspense fallback={<LoadingFallback />}>
                <Outlet />
              </Suspense>
            </AuthProfileBridge>
          </AIStatusProvider>
        </AuthProvider>
      </ModeContext.Provider>
      </VersionContext.Provider>
    )
  }

  return (
    <VersionContext.Provider value={version}>
    <ModeContext.Provider value="home">
      <AIStatusProvider>
        <ProfileProvider>
          <Toaster position="top-center" richColors />
          <Suspense fallback={<LoadingFallback />}>
            <Outlet />
          </Suspense>
        </ProfileProvider>
      </AIStatusProvider>
    </ModeContext.Provider>
    </VersionContext.Provider>
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

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
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
