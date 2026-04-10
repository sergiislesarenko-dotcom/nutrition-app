import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getLogs, addLog, deleteLog } from '../services/nutrition.service'
import type { IAddLogRequest } from '../types/api.types'

const TODAY = new Date().toISOString().slice(0, 10)

export function useNutritionLog(date = TODAY) {
  const queryClient = useQueryClient()

  const logsQuery = useQuery({
    queryKey: ['nutrition-logs', date],
    queryFn: () => getLogs(date),
  })

  const addMutation = useMutation({
    mutationFn: (data: IAddLogRequest) => addLog(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['nutrition-logs'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (logId: number) => deleteLog(logId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['nutrition-logs'] }),
  })

  return {
    logs: logsQuery.data?.logs ?? [],
    summary: logsQuery.data?.summary ?? null,
    isLoading: logsQuery.isLoading,
    addLog: addMutation.mutate,
    deleteLog: deleteMutation.mutate,
    isAdding: addMutation.isPending,
  }
}
