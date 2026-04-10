import { useState } from 'react'
import type { IFood } from '../../types/api.types'

type FoodSearchInputProps = {
  value: string
  onChange: (value: string) => void
  onSelect: (food: IFood) => void
  suggestions: IFood[]
  isSearching: boolean
}

export default function FoodSearchInput({
  value,
  onChange,
  onSelect,
  suggestions,
  isSearching,
}: FoodSearchInputProps) {
  const [open, setOpen] = useState(false)

  function handleBlur() {
    setTimeout(() => setOpen(false), 150)
  }

  return (
    <div className="relative">
      <input
        type="text"
        placeholder="Food name"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setOpen(true)}
        onBlur={handleBlur}
        className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      {isSearching && (
        <span className="absolute right-3 top-2.5 text-xs text-gray-400">Searching…</span>
      )}
      {open && suggestions.length > 0 && (
        <ul className="absolute z-10 w-full bg-white border rounded-lg shadow-lg mt-1 max-h-48 overflow-y-auto">
          {suggestions.map((food) => (
            <li
              key={food.id}
              onMouseDown={() => onSelect(food)}
              className="px-3 py-2 text-sm cursor-pointer hover:bg-blue-50"
            >
              <span className="font-medium">{food.name}</span>
              <span className="ml-2 text-xs text-gray-400">
                {Math.round(food.calories_per_100g)} kcal / 100g
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
