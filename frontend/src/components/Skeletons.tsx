/**
 * Skeleton loading components for React frontend
 * Used to show placeholder content while data is loading
 */

import { cn } from '../lib/utils'

/**
 * Base skeleton element with pulse animation
 */
function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn('animate-pulse rounded bg-muted', className)} />
  )
}

/**
 * Skeleton for recipe cards in grids (AllRecipes, Search, Favorites)
 */
export function RecipeCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-lg bg-card shadow-sm">
      {/* Image placeholder */}
      <Skeleton className="aspect-[4/3] rounded-none" />
      {/* Content */}
      <div className="p-3 space-y-2">
        {/* Title */}
        <Skeleton className="h-4 w-3/4" />
        {/* Meta row */}
        <div className="flex items-center gap-3">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-3 w-12" />
        </div>
      </div>
    </div>
  )
}

/**
 * Grid of recipe card skeletons
 */
export function RecipeGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <RecipeCardSkeleton key={i} />
      ))}
    </div>
  )
}

/**
 * Skeleton for collection cards
 */
export function CollectionCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-lg bg-card p-4 shadow-sm">
      {/* Icon placeholder */}
      <Skeleton className="mb-8 h-12 w-12 rounded-lg" />
      {/* Name */}
      <Skeleton className="mb-2 h-5 w-3/4" />
      {/* Count */}
      <Skeleton className="h-4 w-16" />
    </div>
  )
}

/**
 * Grid of collection card skeletons
 */
export function CollectionGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <CollectionCardSkeleton key={i} />
      ))}
    </div>
  )
}

/**
 * Full recipe detail page skeleton
 */
export function RecipeDetailSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero image skeleton */}
      <div className="relative h-64 sm:h-80">
        <Skeleton className="h-full w-full rounded-none" />
        {/* Back button placeholder */}
        <div className="absolute left-4 top-4">
          <Skeleton className="h-10 w-10 rounded-full" />
        </div>
        {/* Title overlay placeholder */}
        <div className="absolute bottom-4 left-4 right-4">
          <Skeleton className="mb-2 h-7 w-3/4" />
          <div className="flex gap-3">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
        {/* Action buttons placeholder */}
        <div className="absolute bottom-4 right-4 flex gap-2">
          <Skeleton className="h-10 w-10 rounded-full" />
          <Skeleton className="h-10 w-10 rounded-full" />
          <Skeleton className="h-10 w-20 rounded-full" />
        </div>
      </div>

      {/* Meta info skeleton */}
      <div className="border-b border-border px-4 py-4">
        <div className="flex flex-wrap gap-4">
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-5 w-32" />
        </div>
      </div>

      {/* Tabs skeleton */}
      <div className="border-b border-border px-4">
        <div className="flex gap-4 py-3">
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-5 w-16" />
          <Skeleton className="h-5 w-12" />
        </div>
      </div>

      {/* Content skeleton */}
      <div className="px-4 py-6 space-y-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex items-start gap-3">
            <Skeleton className="h-7 w-7 rounded-full shrink-0" />
            <Skeleton className="h-5 flex-1" />
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * Simple centered loading spinner
 */
export function LoadingSpinner({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center justify-center py-12', className)}>
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
    </div>
  )
}

/**
 * Loading state for list pages with optional message
 */
export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="mb-3 h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
      <span className="text-sm text-muted-foreground">{message}</span>
    </div>
  )
}

/**
 * Search result card skeleton
 */
export function SearchResultSkeleton() {
  return (
    <div className="overflow-hidden rounded-lg bg-card shadow-sm">
      {/* Image placeholder */}
      <Skeleton className="aspect-[4/3] rounded-none" />
      {/* Content */}
      <div className="p-3 space-y-2">
        {/* Title */}
        <Skeleton className="h-4 w-3/4" />
        {/* Meta */}
        <Skeleton className="h-3 w-1/2" />
        {/* Description */}
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-2/3" />
        {/* Button */}
        <Skeleton className="h-8 w-full mt-2" />
      </div>
    </div>
  )
}

/**
 * Grid of search result skeletons
 */
export function SearchGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <SearchResultSkeleton key={i} />
      ))}
    </div>
  )
}
