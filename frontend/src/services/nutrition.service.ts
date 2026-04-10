import api from './api'
import type {
  IAddLogRequest,
  IGoal,
  IGoalCreate,
  ILogsResponse,
  IRestriction,
  IRestrictionCreate,
} from '../types/api.types'

export async function getLogs(date: string, days = 1): Promise<ILogsResponse> {
  const res = await api.get<ILogsResponse>('/nutrition/logs', { params: { date, days } })
  return res.data
}

export async function addLog(data: IAddLogRequest): Promise<void> {
  await api.post('/nutrition/logs', data)
}

export async function deleteLog(logId: number): Promise<void> {
  await api.delete(`/nutrition/logs/${logId}`)
}

export async function getActiveGoal(): Promise<IGoal | null> {
  const res = await api.get<IGoal | null>('/goals/active')
  return res.data
}

export async function createGoal(data: IGoalCreate): Promise<IGoal> {
  const res = await api.post<IGoal>('/goals', data)
  return res.data
}

export async function getRestrictions(): Promise<IRestriction[]> {
  const res = await api.get<IRestriction[]>('/users/me/restrictions')
  return res.data
}

export async function addRestriction(data: IRestrictionCreate): Promise<IRestriction> {
  const res = await api.post<IRestriction>('/users/me/restrictions', data)
  return res.data
}

export async function deleteRestriction(restrictionId: number): Promise<void> {
  await api.delete(`/users/me/restrictions/${restrictionId}`)
}
