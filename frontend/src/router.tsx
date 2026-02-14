import { createBrowserRouter, Outlet, Navigate, useLocation } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AIStatusProvider } from './contexts/AIStatusContext'
import { ProfileProvider, useProfile } from './contexts/ProfileContext'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import ProfileSelector from './screens/ProfileSelector'
import Login from './screens/Login'
import Register from './screens/Register'
import Home from './screens/Home'
import Search from './screens/Search'
import RecipeDetail from './screens/RecipeDetail'
import PlayMode from './screens/PlayMode'
import Favorites from './screens/Favorites'
import AllRecipes from './screens/AllRecipes'
import Collections from './screens/Collections'
import CollectionDetail from './screens/CollectionDetail'
import Settings from './screens/Settings'

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
function AppLayout() {
  return (
    <AuthProvider>
      <AIStatusProvider>
        <ProfileProvider>
          <Toaster position="top-center" richColors />
          <Outlet />
        </ProfileProvider>
      </AIStatusProvider>
    </AuthProvider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { profile, loading: profileLoading } = useProfile()
  const { isPublicMode, isAuthenticated, loading: authLoading } = useAuth()
  const location = useLocation()

  if (profileLoading || authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  // Public mode: require authentication
  if (isPublicMode && !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Home mode: require profile selection
  if (!isPublicMode && !profile) {
    return <Navigate to="/" state={{ from: location }} replace />
  }

  return <>{children}</>
}

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
function AdminRoute({ children }: { children: React.ReactNode }) {
  const { profile, loading: profileLoading } = useProfile()
  const { isPublicMode, isAuthenticated, isAdmin, loading: authLoading } = useAuth()
  const location = useLocation()

  if (profileLoading || authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  // Public mode: require authentication
  if (isPublicMode && !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Home mode: require profile selection
  if (!isPublicMode && !profile) {
    return <Navigate to="/" state={{ from: location }} replace />
  }

  // Require admin access
  if (!isAdmin) {
    return <Navigate to="/home" replace />
  }

  return <>{children}</>
}

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { profile, loading: profileLoading } = useProfile()
  const { isPublicMode, isAuthenticated, loading: authLoading } = useAuth()

  if (profileLoading || authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  // Public mode: redirect authenticated users to home
  if (isPublicMode && isAuthenticated) {
    return <Navigate to="/home" replace />
  }

  // Home mode: redirect users with profile to home
  if (!isPublicMode && profile) {
    return <Navigate to="/home" replace />
  }

  return <>{children}</>
}

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
function AuthRoute({ children }: { children: React.ReactNode }) {
  const { isPublicMode, isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  // Home mode: redirect to profile selector (no login needed)
  if (!isPublicMode) {
    return <Navigate to="/" replace />
  }

  // Public mode: redirect authenticated users to home
  if (isAuthenticated) {
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
        path: '/login',
        element: (
          <AuthRoute>
            <Login />
          </AuthRoute>
        ),
      },
      {
        path: '/register',
        element: (
          <AuthRoute>
            <Register />
          </AuthRoute>
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
          <AdminRoute>
            <Settings />
          </AdminRoute>
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
