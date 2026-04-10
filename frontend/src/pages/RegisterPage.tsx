import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useRegister } from '../hooks/useAuth'
import type { IRegisterRequest } from '../types/api.types'

const ACTIVITY_LEVELS: IRegisterRequest['activity_level'][] = [
  'sedentary', 'light', 'moderate', 'active', 'very_active',
]

export default function RegisterPage() {
  const { mutate, isPending, error } = useRegister()
  const [form, setForm] = useState<IRegisterRequest>({
    email: '',
    password: '',
    age: 25,
    weight_kg: 70,
    height_cm: 170,
    gender: 'male',
    activity_level: 'moderate',
  })

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, value } = e.target
    setForm((prev) => ({
      ...prev,
      [name]: ['age', 'weight_kg', 'height_cm'].includes(name) ? Number(value) : value,
    }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    mutate(form)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-8">
      <div className="w-full max-w-md bg-white rounded-xl shadow p-8">
        <h1 className="text-2xl font-bold mb-6 text-center">Create account</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input name="email" type="email" placeholder="Email" value={form.email} onChange={handleChange} required
            className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <input name="password" type="password" placeholder="Password" value={form.password} onChange={handleChange} required
            className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <div className="grid grid-cols-3 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500">Age</label>
              <input name="age" type="number" value={form.age} onChange={handleChange} min={10} max={120} required
                className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500">Weight, kg</label>
              <input name="weight_kg" type="number" value={form.weight_kg} onChange={handleChange} min={20} required
                className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500">Height, cm</label>
              <input name="height_cm" type="number" value={form.height_cm} onChange={handleChange} min={50} required
                className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <select name="gender" value={form.gender} onChange={handleChange}
            className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
          <select name="activity_level" value={form.activity_level} onChange={handleChange}
            className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
            {ACTIVITY_LEVELS.map((lvl) => (
              <option key={lvl} value={lvl}>{lvl}</option>
            ))}
          </select>
          {error && <p className="text-red-500 text-sm">Registration failed. Email may already exist.</p>}
          <button type="submit" disabled={isPending}
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {isPending ? 'Creating account…' : 'Register'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          Have an account?{' '}
          <Link to="/login" className="text-blue-600 hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
