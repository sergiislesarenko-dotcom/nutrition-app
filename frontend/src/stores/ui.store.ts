import { create } from 'zustand'

interface IToast {
  id: string
  message: string
  type: 'success' | 'error' | 'info'
}

interface IUiState {
  sidebarOpen: boolean
  toasts: IToast[]
  toggleSidebar: () => void
  addToast: (message: string, type?: IToast['type']) => void
  removeToast: (id: string) => void
}

export const useUiStore = create<IUiState>((set) => ({
  sidebarOpen: true,
  toasts: [],
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  addToast: (message, type = 'info') =>
    set((s) => ({
      toasts: [...s.toasts, { id: crypto.randomUUID(), message, type }],
    })),
  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))
