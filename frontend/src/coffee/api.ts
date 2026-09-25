export type RecipeType = 'espresso' | 'pour_over' | 'drip' | 'french_press'
export type SuggestionField = 'roaster' | 'product' | 'grinder'

export interface RecipeInput {
  date: string
  roaster: string
  product: string
  roast_level: number
  recipe_type: RecipeType
  coffee_weight_g: number
  brew_time_seconds: number
  total_yield_g: number
  grind_setting: number
  grinder: string
  rating: number
  notes: string | null
}

export interface Recipe extends RecipeInput {
  id: string
  created_at: string
  updated_at: string
}

export interface RecipeList {
  items: Recipe[]
  total: number
  limit: number
  offset: number
}

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown) {
    super(status === 422 ? 'Please review the highlighted fields.' : 'Could not save the recipe. Please try again.')
    this.status = status
    this.detail = detail
  }
}

async function readJson<T>(response: Response): Promise<T> {
  const body = await response.json()
  if (!response.ok) throw new ApiError(response.status, body.detail)
  return body as T
}

export async function createRecipe(input: RecipeInput): Promise<Recipe> {
  return readJson<Recipe>(await fetch('/api/coffee/recipes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  }))
}

export async function listRecipes(signal?: AbortSignal): Promise<RecipeList> {
  return readJson<RecipeList>(await fetch(
    '/api/coffee/recipes?limit=20&offset=0&sort_by=date&sort_dir=desc',
    { signal },
  ))
}

export async function getSuggestions(
  field: SuggestionField,
  q: string,
  roaster: string,
  signal: AbortSignal,
): Promise<string[]> {
  const params = new URLSearchParams({ field, q, limit: '10' })
  if (field === 'product') params.set('roaster', roaster.trim())
  const result = await readJson<{ values: string[] }>(await fetch(
    `/api/coffee/recipes/suggestions?${params}`,
    { signal },
  ))
  return result.values
}
