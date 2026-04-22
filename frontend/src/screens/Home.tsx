import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import { useProfile } from '../contexts/ProfileContext'
import { useAIStatus } from '../contexts/AIStatusContext'
import { useHomeData } from '../hooks/useHomeData'
import { useDiscoverTab } from '../hooks/useDiscoverTab'
import NavHeader from '../components/NavHeader'
import { RecipeGridSkeleton } from '../components/Skeletons'
import { cn } from '../lib/utils'
import FavoritesTab from './FavoritesTab'
import DiscoverTab from './DiscoverTab'

type Tab = 'favorites' | 'discover'

function TabToggle({ activeTab, onFavoritesClick, onDiscoverClick }: {
  activeTab: Tab
  onFavoritesClick: () => void
  onDiscoverClick: () => void
}) {
  return (
    <div className="mb-6 flex justify-center">
      <div className="inline-flex rounded-lg bg-muted p-1">
        <button
          onClick={onFavoritesClick}
          className={cn(
            'rounded-md px-4 py-2 text-sm font-medium transition-colors',
            activeTab === 'favorites'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          My Favorites
        </button>
        <button
          onClick={onDiscoverClick}
          className={cn(
            'rounded-md px-4 py-2 text-sm font-medium transition-colors',
            activeTab === 'discover'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          Discover
        </button>
      </div>
    </div>
  )
}

export default function Home() {
  const navigate = useNavigate()
  const { profile } = useProfile()
  const aiStatus = useAIStatus()
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<Tab>('favorites')

  const { favorites, history, recipesCount, loading, favoriteIds, handleRecipeClick, handleToggleFavorite } = useHomeData()

  const discoverAvailable = aiStatus.isFeatureAvailable('discover')

  const discover = useDiscoverTab({
    profileId: profile?.id,
    aiAvailable: discoverAvailable,
  })

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  const handleDiscoverTabClick = () => {
    setActiveTab('discover')
    discover.loadIfEmpty()
  }

  if (!profile) return null

  const showFavorites = activeTab === 'favorites' || !discoverAvailable

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <NavHeader />
      <main className="flex-1 px-4 py-6">
        <div className="mx-auto max-w-4xl">
          <form onSubmit={handleSearchSubmit} className="mb-6">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search recipes..."
                className="w-full rounded-xl border border-border bg-input-background py-3 pl-12 pr-4 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </form>

          {discoverAvailable && (
            <TabToggle
              activeTab={activeTab}
              onFavoritesClick={() => setActiveTab('favorites')}
              onDiscoverClick={handleDiscoverTabClick}
            />
          )}

          {loading ? (
            <RecipeGridSkeleton count={6} />
          ) : showFavorites ? (
            <FavoritesTab
              history={history}
              favorites={favorites}
              recipesCount={recipesCount}
              favoriteIds={favoriteIds}
              onRecipeClick={handleRecipeClick}
              onFavoriteToggle={handleToggleFavorite}
            />
          ) : (
            <DiscoverTab
              suggestions={discover.suggestions}
              loading={discover.loading}
              error={discover.error}
              aiAvailable={discoverAvailable}
              onRefresh={() => discover.load(true)}
              onRetry={() => discover.load()}
              onSwitchToFavorites={() => setActiveTab('favorites')}
            />
          )}
        </div>
      </main>
    </div>
  )
}
