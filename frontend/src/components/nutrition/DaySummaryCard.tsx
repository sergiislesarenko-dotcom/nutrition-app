import type { IDaySummary } from '../../types/api.types'

type DaySummaryCardProps = {
  summary: IDaySummary
}

export default function DaySummaryCard({ summary }: DaySummaryCardProps) {
  const deficit = summary.deficit_surplus

  return (
    <div className="bg-white rounded-xl shadow p-5">
      <h2 className="text-lg font-semibold mb-3">Today's summary</h2>
      <div className="grid grid-cols-4 gap-3 text-center">
        <Stat label="Calories" value={Math.round(summary.total_calories)} unit="kcal" />
        <Stat label="Protein" value={Math.round(summary.total_protein)} unit="g" />
        <Stat label="Carbs" value={Math.round(summary.total_carbs)} unit="g" />
        <Stat label="Fat" value={Math.round(summary.total_fat)} unit="g" />
      </div>
      {summary.goal_calories && (
        <p className="mt-3 text-sm text-center text-gray-500">
          Goal: {summary.goal_calories} kcal &nbsp;|&nbsp;
          <span className={deficit && deficit < 0 ? 'text-green-600' : 'text-orange-500'}>
            {deficit !== null
              ? deficit < 0
                ? `${Math.abs(Math.round(deficit))} kcal deficit`
                : `${Math.round(deficit)} kcal surplus`
              : '—'}
          </span>
        </p>
      )}
    </div>
  )
}

function Stat({ label, value, unit }: { label: string; value: number; unit: string }) {
  return (
    <div>
      <p className="text-xl font-bold">{value}</p>
      <p className="text-xs text-gray-400">{unit}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}
