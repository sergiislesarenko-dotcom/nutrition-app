import type { IAddLogRequest } from '../../types/api.types'

type MacroValues = Pick<
  IAddLogRequest,
  'weight_g' | 'calories_kcal' | 'protein_g' | 'carbs_g' | 'fat_g'
>

type MacroFieldsProps = {
  values: MacroValues
  onWeightChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onWeightBlur: (e: React.FocusEvent<HTMLInputElement>) => void
  onMacroChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onMacroBlur: (e: React.FocusEvent<HTMLInputElement>) => void
  lockedFields: boolean
}

const MACRO_FIELDS: { name: keyof MacroValues; label: string }[] = [
  { name: 'weight_g', label: 'Weight, g' },
  { name: 'calories_kcal', label: 'Calories' },
  { name: 'protein_g', label: 'Protein, g' },
  { name: 'carbs_g', label: 'Carbs, g' },
  { name: 'fat_g', label: 'Fat, g' },
]

export default function MacroFields({
  values,
  onWeightChange,
  onWeightBlur,
  onMacroChange,
  onMacroBlur,
  lockedFields,
}: MacroFieldsProps) {
  return (
    <div className="grid grid-cols-5 gap-2">
      {MACRO_FIELDS.map(({ name, label }) => {
        const isWeight = name === 'weight_g'
        const disabled = lockedFields && !isWeight
        return (
          <div key={name} className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">{label}</label>
            <input
              name={name}
              type="number"
              min={0}
              step={0.1}
              value={values[name] || ''}
              onChange={isWeight ? onWeightChange : onMacroChange}
              onBlur={isWeight ? onWeightBlur : onMacroBlur}
              disabled={disabled}
              className={`w-full border rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500
                ${disabled ? 'bg-gray-50 text-gray-400 cursor-not-allowed' : ''}`}
            />
          </div>
        )
      })}
    </div>
  )
}
