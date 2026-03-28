import { createContext, lazy, Suspense, useContext, useState, useEffect } from 'react'
import { createBrowserRouter, Outlet, Navigate, useLocation } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AIStatusProvider } from './contexts/AIStatusContext'
import { ProfileProvider, useProfile } from './contexts/ProfileContext'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { api } from './api/client'

const ProfileSelector = lazy(() => import('./screens/ProfileSelector'))
const Login = lazy(() => import('./screens/Login'))
const Register = lazy(() => import('./screens/Register'))
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
const PairDevice = lazy(() => import('./screens/PairDevice'))
const PasskeyManage = lazy(() => import('./screens/PasskeyManage'))

function LoadingFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-muted-foreground">Loading...</div>
    </div>
  )
}

// Mode context — provides the operating mode to child components without hook violations
const ModeContext = createContext<'home' | 'public' | 'passkey'>('home')

export function useMode() {
  return useContext(ModeContext)
}

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
function AppLayout() {
  const [mode, setMode] = useState<'home' | 'public' | 'passkey' | null>(null)

  useEffect(() => {
    api.system
      .mode()
      .then((data) => setMode(data.mode))
      .catch(() => setMode('home'))
  }, [])

  if (mode === null) {
    return <LoadingFallback />
  }

  if (mode === 'public' || mode === 'passkey') {
    return (
      <ModeContext.Provider value={mode}>
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
    )
  }

  return (
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
  )
}

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
function AuthProfileBridge({ children }: { children: React.ReactNode }) {
  const { profile: authProfile, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingFallback />
  }

  return <ProfileProvider authProfile={authProfile}>{children}</ProfileProvider>
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

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
function RootRoute() {
  const mode = useMode()
  if (mode === 'passkey') {
    return <PasskeyLogin />
  }
  if (mode === 'public') {
    return <Login />
  }
  return <ProfileSelector />
}

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
function LoginRoute() {
  const mode = useMode()
  if (mode === 'passkey') {
    return <PasskeyLogin />
  }
  return <Login />
}

// eslint-disable-next-line react-refresh/only-export-components -- Internal router component, not exported for reuse
function RegisterRoute() {
  const mode = useMode()
  if (mode === 'passkey') {
    return <PasskeyRegister />
  }
  return <Register />
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
        path: '/login',
        element: (
          <PublicRoute>
            <LoginRoute />
          </PublicRoute>
        ),
      },
      {
        path: '/register',
        element: (
          <PublicRoute>
            <RegisterRoute />
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
        element: (
          <ProtectedRoute>
            <PairDevice />
          </ProtectedRoute>
        ),
      },
      {
        path: '/passkeys',
        element: (
          <ProtectedRoute>
            <PasskeyManage />
          </ProtectedRoute>
        ),
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
])
