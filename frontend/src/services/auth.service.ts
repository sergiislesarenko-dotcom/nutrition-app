import api from './api'
import type { IAuthResponse, ILoginRequest, IRegisterRequest, IUserOut } from '../types/api.types'

export async function login(data: ILoginRequest): Promise<IAuthResponse> {
  const res = await api.post<IAuthResponse>('/auth/login', data)
  return res.data
}

export async function register(data: IRegisterRequest): Promise<IAuthResponse> {
  const res = await api.post<IAuthResponse>('/auth/register', data)
  return res.data
}

export async function getMe(): Promise<IUserOut> {
  const res = await api.get<IUserOut>('/users/me')
  return res.data
}
