import { lazy, Suspense } from 'react'
import { createBrowserRouter, Outlet, Navigate, useLocation } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AIStatusProvider } from './contexts/AIStatusContext'
import { ProfileProvider, useProfile } from './contexts/ProfileContext'

const ProfileSelector = lazy(() => import('./screens/ProfileSelector'))
const Home = lazy(() => import('./screens/Home'))
const Search = lazy(() => import('./screens/Search'))
const RecipeDetail = lazy(() => import('./screens/RecipeDetail'))
const PlayMode = lazy(() => import('./screens/PlayMode'))
const Favorites = lazy(() => import('./screens/Favorites'))
const AllRecipes = lazy(() => import('./screens/AllRecipes'))
const Collections = lazy(() => import('./screens/Collections'))
const CollectionDetail = lazy(() => import('./screens/CollectionDetail'))
const Settings = lazy(() => import('./screens/Settings'))

function LoadingFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-muted-foreground">Loading...</div>
    </div>
  )
}

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
function AppLayout() {
  return (
    <AIStatusProvider>
      <ProfileProvider>
        <Toaster position="top-center" richColors />
        <Suspense fallback={<LoadingFallback />}>
          <Outlet />
        </Suspense>
      </ProfileProvider>
    </AIStatusProvider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
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

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
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

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      {
        path: '/',
        element: (
          <PublicRoute>
            <ProfileSelector />
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
      // Catch-all redirect to home
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
])
