import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../services/auth.service'
import { useAuthStore } from '../stores/auth.store'
import type { ILoginRequest, IRegisterRequest } from '../types/api.types'

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: ILoginRequest) => login(data),
    onSuccess: (res) => {
      setAuth(res.access_token, res.user)
      navigate('/')
    },
  })
}

export function useRegister() {
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: IRegisterRequest) => register(data),
    onSuccess: (res) => {
      setAuth(res.access_token, res.user)
      navigate('/')
    },
  })
}
