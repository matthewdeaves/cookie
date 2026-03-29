import { Search, X } from 'lucide-react'

interface RecipeSearchFilterProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  totalCount: number
  filteredCount: number
}

export default function RecipeSearchFilter({
  searchQuery,
  onSearchChange,
  totalCount,
  filteredCount,
}: RecipeSearchFilterProps) {
  return (
    <>
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Filter recipes..."
          className="w-full rounded-lg border border-border bg-input-background py-2 pl-10 pr-10 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      <p className="mb-4 text-sm text-muted-foreground">
        {searchQuery
          ? `${filteredCount} of ${totalCount} recipe${totalCount !== 1 ? 's' : ''}`
          : `${totalCount} recipe${totalCount !== 1 ? 's' : ''}`}
      </p>
    </>
  )
}
