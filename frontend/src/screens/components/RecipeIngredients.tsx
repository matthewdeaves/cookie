import { type RecipeDetail, type ScaleResponse } from '../../api/client'

interface RecipeIngredientsProps {
  recipe: RecipeDetail
  scaledData: ScaleResponse | null
}

export default function RecipeIngredients({
  recipe,
  scaledData,
}: RecipeIngredientsProps) {
  // Use scaled ingredients if available, otherwise use recipe ingredients
  const ingredients = scaledData?.ingredients || recipe.ingredients

  // Use ingredient_groups if available and not scaled, otherwise flat ingredients list
  const hasGroups = recipe.ingredient_groups.length > 0 && !scaledData

  if (hasGroups) {
    return (
      <div className="space-y-6">
        {recipe.ingredient_groups.map((group, groupIndex) => (
          <div key={groupIndex}>
            {group.purpose && (
              <h3 className="mb-3 font-medium text-foreground">
                {group.purpose}
              </h3>
            )}
            <ol className="space-y-2">
              {group.ingredients.map((ingredient, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 text-foreground"
                >
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
                    {index + 1}
                  </span>
                  <span>{ingredient}</span>
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>
    )
  }

  return (
    <ol className="space-y-2">
      {ingredients.map((ingredient, index) => (
        <li key={index} className="flex items-start gap-3 text-foreground">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
            {index + 1}
          </span>
          <span>{ingredient}</span>
        </li>
      ))}
    </ol>
  )
}
