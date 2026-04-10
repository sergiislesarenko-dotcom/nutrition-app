import { useAuthStore } from '../stores/auth.store'
import { useNutritionLog } from '../hooks/useNutritionLog'
import DaySummaryCard from '../components/nutrition/DaySummaryCard'
import MealList from '../components/nutrition/MealList'
import NutritionLogForm from '../components/nutrition/NutritionLogForm'
import ChatWindow from '../components/chat/ChatWindow'

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const clearAuth = useAuthStore((s) => s.clearAuth)
  const { logs, summary, isLoading, deleteLog } = useNutritionLog()

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold text-blue-700">Nutrition App</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">{user?.email}</span>
          <button onClick={clearAuth} className="text-sm text-red-500 hover:underline">
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          {summary && <DaySummaryCard summary={summary} />}
          <NutritionLogForm onSuccess={() => {}} />
          {isLoading ? (
            <p className="text-gray-500 text-sm">Loading…</p>
          ) : (
            <MealList logs={logs} onDelete={deleteLog} />
          )}
        </div>
        <div>
          <ChatWindow />
        </div>
      </main>
    </div>
  )
}
