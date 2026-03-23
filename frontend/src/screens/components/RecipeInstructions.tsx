import { type RecipeDetail, type ScaleResponse } from '../../api/client'

interface RecipeInstructionsProps {
  recipe: RecipeDetail
  scaledData: ScaleResponse | null
}

export default function RecipeInstructions({
  recipe,
  scaledData,
}: RecipeInstructionsProps) {
  // Use scaled instructions if available, otherwise fall back to original
  const hasScaledInstructions = scaledData?.instructions && scaledData.instructions.length > 0
  const instructions = hasScaledInstructions
    ? scaledData.instructions
    : recipe.instructions.length > 0
      ? recipe.instructions
      : recipe.instructions_text
        ? recipe.instructions_text.split('\n').filter((s) => s.trim())
        : []

  if (instructions.length === 0) {
    return (
      <p className="text-muted-foreground">
        No instructions available for this recipe.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      {hasScaledInstructions && (
        <p className="text-sm text-muted-foreground">
          Instructions adjusted for {scaledData.target_servings} servings
        </p>
      )}
      <ol className="space-y-4">
        {instructions.map((step, index) => (
          <li key={index} className="flex items-start gap-4">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
              {index + 1}
            </span>
            <p className="pt-0.5 text-foreground">{step}</p>
          </li>
        ))}
      </ol>
    </div>
  )
}
