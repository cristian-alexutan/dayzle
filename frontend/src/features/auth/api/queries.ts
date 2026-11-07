// TanStack Query hooks for the Auth (Google login, guest identity, route guards) feature.
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import { ApiError } from '@/api/http'

import { fetchSession, loginWithGoogle, logoutSession } from './endpoints'

export const sessionKey = ['auth', 'session'] as const

/** The backend's error code (`invalid_google_token`, ...), or null for any other error. */
export function authErrorCode(error: unknown): string | null {
  return error instanceof ApiError ? error.code : null
}

export function useSessionQuery() {
  return useQuery({
    queryKey: sessionKey,
    queryFn: fetchSession,
  })
}

export function useGoogleLoginMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (credential: string) => loginWithGoogle(credential),
    onSuccess: (session) => {
      queryClient.setQueryData(sessionKey, session)
    },
  })
}

export function useLogoutMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => logoutSession(),
    onSuccess: (session) => {
      queryClient.setQueryData(sessionKey, session)
    },
  })
}
