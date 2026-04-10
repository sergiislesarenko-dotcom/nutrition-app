import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { IUserOut } from '../types/api.types'

interface IAuthState {
  token: string | null
  user: IUserOut | null
  isAuthenticated: boolean
  setAuth: (token: string, user: IUserOut) => void
  clearAuth: () => void
}

export const useAuthStore = create<IAuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      setAuth: (token, user) => set({ token, user, isAuthenticated: true }),
      clearAuth: () => set({ token: null, user: null, isAuthenticated: false }),
    }),
    { name: 'auth-storage' },
  ),
)
