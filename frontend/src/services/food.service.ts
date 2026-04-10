import api from './api'
import type { IFoodCompleteRequest, IFoodMacrosResponse, IFoodSearchResponse } from '../types/api.types'

export async function searchFoods(q: string, limit = 10): Promise<IFoodSearchResponse> {
  const res = await api.get<IFoodSearchResponse>('/foods/search', { params: { q, limit } })
  return res.data
}

export async function getFoodMacros(name: string, weight: number): Promise<IFoodMacrosResponse> {
  const res = await api.get<IFoodMacrosResponse>('/foods/macros', { params: { name, weight } })
  return res.data
}

export async function completeFoodMacros(data: IFoodCompleteRequest): Promise<IFoodMacrosResponse> {
  const res = await api.post<IFoodMacrosResponse>('/foods/complete', data)
  return res.data
}
