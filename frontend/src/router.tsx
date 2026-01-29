import { createBrowserRouter, Outlet, Navigate, useLocation } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AIStatusProvider } from './contexts/AIStatusContext'
import { ProfileProvider, useProfile } from './contexts/ProfileContext'
import ProfileSelector from './screens/ProfileSelector'
import Home from './screens/Home'
import Search from './screens/Search'
import RecipeDetail from './screens/RecipeDetail'
import PlayMode from './screens/PlayMode'
import Favorites from './screens/Favorites'
import AllRecipes from './screens/AllRecipes'
import Collections from './screens/Collections'
import CollectionDetail from './screens/CollectionDetail'
import Settings from './screens/Settings'

// Layout component that provides context and protects routes
function AppLayout() {
  return (
    <AIStatusProvider>
      <ProfileProvider>
        <Toaster position="top-center" richColors />
        <Outlet />
      </ProfileProvider>
    </AIStatusProvider>
  )
}

// Protected route wrapper - redirects to profile selector if not logged in
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { profile, loading } = useProfile()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  if (!profile) {
    return <Navigate to="/" state={{ from: location }} replace />
  }

  return <>{children}</>
}

// Public route - redirects to home if already logged in
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { profile, loading } = useProfile()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
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
