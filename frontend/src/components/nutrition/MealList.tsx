import type { INutritionLog } from '../../types/api.types'

type MealListProps = {
  logs: INutritionLog[]
  onDelete: (id: number) => void
}

export default function MealList({ logs, onDelete }: MealListProps) {
  if (logs.length === 0) {
    return <p className="text-gray-400 text-sm text-center py-4">No meals logged today</p>
  }

  return (
    <div className="bg-white rounded-xl shadow divide-y">
      {logs.map((log) => (
        <div key={log.id} className="flex items-center justify-between px-4 py-3">
          <div>
            <p className="font-medium">{log.food_name}</p>
            <p className="text-xs text-gray-400 capitalize">
              {log.meal_type} · {log.weight_g}g · {Math.round(log.calories_kcal)} kcal
            </p>
          </div>
          <button
            onClick={() => onDelete(log.id)}
            className="text-red-400 hover:text-red-600 text-sm"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  )
}
