import { GitCompareArrows } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { type LinkedRecipe } from '../../api/client'
import { cn } from '../../lib/utils'

interface LinkedRecipesNavProps {
  linkedRecipes: LinkedRecipe[]
}

export default function LinkedRecipesNav({
  linkedRecipes,
}: LinkedRecipesNavProps) {
  const navigate = useNavigate()

  if (linkedRecipes.length === 0) return null

  return (
    <div className="border-b border-border px-4 py-3">
      <div className="flex items-center gap-2 text-sm">
        <GitCompareArrows className="h-4 w-4 text-muted-foreground" />
        <span className="text-muted-foreground">Linked recipes:</span>
        <div className="flex flex-wrap gap-2">
          {linkedRecipes.map((linked) => (
            <button
              key={linked.id}
              onClick={() => navigate(`/recipe/${linked.id}`)}
              className="inline-flex items-center gap-1 rounded-full bg-muted px-3 py-1 text-xs font-medium text-foreground transition-colors hover:bg-muted/80"
            >
              <span
                className={cn(
                  'h-1.5 w-1.5 rounded-full',
                  linked.relationship === 'original'
                    ? 'bg-primary'
                    : linked.relationship === 'remix'
                      ? 'bg-accent'
                      : 'bg-muted-foreground'
                )}
              />
              {linked.title}
              <span className="text-muted-foreground">
                ({linked.relationship})
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
