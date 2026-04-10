import api from './api'
import type { IChatResponse, IRecommendationsResponse } from '../types/api.types'
import { API_BASE_URL } from '../constants/api.constants'
import { useAuthStore } from '../stores/auth.store'

export async function sendChat(message: string): Promise<IChatResponse> {
  const res = await api.post<IChatResponse>('/ai/chat', { message })
  return res.data
}

export function createChatStream(message: string): EventSource {
  const token = useAuthStore.getState().token
  const url = `${API_BASE_URL}/ai/chat/stream?message=${encodeURIComponent(message)}&token=${token ?? ''}`
  return new EventSource(url)
}

export async function getRecommendations(limit = 20, offset = 0): Promise<IRecommendationsResponse> {
  const res = await api.get<IRecommendationsResponse>('/ai/recommendations', {
    params: { limit, offset },
  })
  return res.data
}
