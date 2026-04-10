import { useState } from 'react'
import { useNutritionLog } from '../../hooks/useNutritionLog'
import { useFoodSearch } from '../../hooks/useFoodSearch'
import FoodSearchInput from './FoodSearchInput'
import MacroFields from './MacroFields'
import type { IAddLogRequest, IFood, IFoodMacrosResponse, IKnownMacros } from '../../types/api.types'

type NutritionLogFormProps = {
  onSuccess: () => void
}

const EMPTY_FORM: IAddLogRequest = {
  meal_type: 'breakfast',
  food_name: '',
  weight_g: 0,
  calories_kcal: 0,
  protein_g: 0,
  carbs_g: 0,
  fat_g: 0,
}

const NUMERIC_MACRO_FIELDS = new Set(['calories_kcal', 'protein_g', 'carbs_g', 'fat_g'])

export default function NutritionLogForm({ onSuccess }: NutritionLogFormProps) {
  const [form, setForm] = useState<IAddLogRequest>(EMPTY_FORM)
  const [selectedFood, setSelectedFood] = useState<IFood | null>(null)
  const { addLog, isAdding } = useNutritionLog()
  const { query, setQuery, suggestions, isSearching, fetchMacros, completeMacros, isFetchingMacros } =
    useFoodSearch()

  function applyMacros(result: IFoodMacrosResponse) {
    setSelectedFood(result.food)
    setForm((prev) => ({
      ...prev,
      calories_kcal: result.calories_kcal,
      protein_g: result.protein_g,
      carbs_g: result.carbs_g,
      fat_g: result.fat_g,
    }))
  }

  async function handleFoodSelect(food: IFood) {
    const name = food.name.toLowerCase()
    setQuery(food.name)
    setForm((prev) => ({ ...prev, food_name: name }))
    if (form.weight_g > 0) {
      const result = await fetchMacros({ name, weight: form.weight_g })
      applyMacros(result)
    } else {
      setSelectedFood(food)
    }
  }

  function handleFoodNameChange(value: string) {
    setQuery(value)
    setForm((prev) => ({ ...prev, food_name: value.toLowerCase() }))
    if (!value) setSelectedFood(null)
  }

  // Triggered when weight field loses focus — picks scenario based on filled BJ/U count
  async function handleWeightBlur(e: React.FocusEvent<HTMLInputElement>) {
    const weight = Number(e.target.value)
    if (weight <= 0 || !form.food_name) return

    const filledBju = [form.protein_g, form.carbs_g, form.fat_g].filter((v) => v > 0)

    if (filledBju.length === 3) {
      // All BJ/U known — calculate calories client-side, no API call
      const kcal = Math.round((form.protein_g * 4 + form.carbs_g * 4 + form.fat_g * 9) * 10) / 10
      setForm((prev) => ({ ...prev, calories_kcal: kcal }))
    } else if (filledBju.length >= 1) {
      // Partial BJ/U — call POST /foods/complete with known per-100g values
      const known: IKnownMacros = {}
      if (form.protein_g > 0) known.protein_per_100g = Math.round((form.protein_g / weight) * 1000) / 10
      if (form.carbs_g > 0) known.carbs_per_100g = Math.round((form.carbs_g / weight) * 1000) / 10
      if (form.fat_g > 0) known.fat_per_100g = Math.round((form.fat_g / weight) * 1000) / 10
      if (form.calories_kcal > 0) known.calories_per_100g = Math.round((form.calories_kcal / weight) * 1000) / 10
      const result = await completeMacros({ name: form.food_name, weight_g: weight, known })
      applyMacros(result)
    } else {
      // No BJ/U — standard AI lookup
      const result = await fetchMacros({ name: form.food_name, weight })
      applyMacros(result)
    }
  }

  // Triggered on blur of any macro field — re-runs scenario logic using form.weight_g
  async function handleMacroBlur(e: React.FocusEvent<HTMLInputElement>) {
    const weight = form.weight_g
    if (weight <= 0 || !form.food_name) return

    // Use the blurred field's latest value (state may not have updated yet)
    const current = { ...form, [e.target.name]: Number(e.target.value) }
    const filledBju = [current.protein_g, current.carbs_g, current.fat_g].filter((v) => v > 0)

    if (filledBju.length === 3) {
      const kcal = Math.round((current.protein_g * 4 + current.carbs_g * 4 + current.fat_g * 9) * 10) / 10
      setForm((prev) => ({ ...prev, calories_kcal: kcal }))
    } else if (filledBju.length >= 1) {
      const known: IKnownMacros = {}
      if (current.protein_g > 0) known.protein_per_100g = Math.round((current.protein_g / weight) * 1000) / 10
      if (current.carbs_g > 0) known.carbs_per_100g = Math.round((current.carbs_g / weight) * 1000) / 10
      if (current.fat_g > 0) known.fat_per_100g = Math.round((current.fat_g / weight) * 1000) / 10
      if (current.calories_kcal > 0) known.calories_per_100g = Math.round((current.calories_kcal / weight) * 1000) / 10
      const result = await completeMacros({ name: form.food_name, weight_g: weight, known })
      applyMacros(result)
    }
  }

  function handleWeightChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm((prev) => ({ ...prev, weight_g: Number(e.target.value) }))
  }

  function handleMacroChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target
    if (NUMERIC_MACRO_FIELDS.has(name)) {
      setSelectedFood(null)
      setForm((prev) => ({ ...prev, [name]: Number(value) }))
    }
  }

  function handleMealTypeChange(e: React.ChangeEvent<HTMLSelectElement>) {
    setForm((prev) => ({ ...prev, meal_type: e.target.value as IAddLogRequest['meal_type'] }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    addLog(form, {
      onSuccess: () => {
        setForm(EMPTY_FORM)
        setQuery('')
        setSelectedFood(null)
        onSuccess()
      },
    })
  }

  return (
    <div className="bg-white rounded-xl shadow p-5">
      <h2 className="text-lg font-semibold mb-4">Add meal</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">Meal type</label>
            <select
              name="meal_type"
              value={form.meal_type}
              onChange={handleMealTypeChange}
              className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="breakfast">Breakfast</option>
              <option value="lunch">Lunch</option>
              <option value="dinner">Dinner</option>
              <option value="snack">Snack</option>
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">Food name</label>
            <FoodSearchInput
              value={query}
              onChange={handleFoodNameChange}
              onSelect={handleFoodSelect}
              suggestions={suggestions}
              isSearching={isSearching}
            />
          </div>
        </div>

        <MacroFields
          values={form}
          onWeightChange={handleWeightChange}
          onWeightBlur={handleWeightBlur}
          onMacroChange={handleMacroChange}
          onMacroBlur={handleMacroBlur}
          lockedFields={selectedFood !== null}
        />

        {isFetchingMacros && (
          <p className="text-xs text-blue-500">Looking up nutritional data…</p>
        )}
        {selectedFood && (
          <p className="text-xs text-green-600">
            ✓ Macros auto-filled ·{' '}
            <button type="button" onClick={() => setSelectedFood(null)} className="underline">
              enter manually
            </button>
          </p>
        )}

        <div className="bg-blue-50 rounded-lg p-2 text-xs text-gray-500">
          Enter food name and weight, then click outside the weight field — macros will be filled automatically.
        </div>

        <button
          type="submit"
          disabled={isAdding}
          className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
        >
          {isAdding ? 'Adding…' : 'Add meal'}
        </button>
      </form>
    </div>
  )
}
